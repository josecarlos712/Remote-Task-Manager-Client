import threading
from typing import Any, Dict

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve
import multiprocessing

import config
from auth import require_api_key
from command_registry import registry
from config import logger
from utils import APIResponse
from utils.APIResponse import ErrorResponse, SuccessResponse, error_handler
from utils.endpoints_loader import load_endpoints


class RemoteClient:
    def __init__(self, name: str, port: int, target_url: str, debug: bool = False):
        self.name = name
        self.port = port
        self.target_url = target_url.rstrip("/")
        self.debug = debug
        self.app = Flask(__name__)
        self.session = requests.Session()
        self.client_db_id = None
        self.last_health_check = None

        CORS(
            self.app,
            resources={
                r"/api/*": {
                    "origins": "*",
                    "methods": ["OPTIONS", "POST", "GET"],
                    "allow_headers": ["Content-Type", "X-Client-API-Key", "X-Register-Token"],
                }
            },
        )

        registry.load_package("command_modules")
        self._register_routes()
        load_endpoints(self.app)

    def _register_routes(self):
        routes = {
            "health": (self.health_check_endpoint, ["GET"]),
            "command/list": (require_api_key(self.command_list_endpoint), ["GET"]),
            "command/execute": (require_api_key(self.command_execute_endpoint), ["POST"]),
            # Legacy alias kept for older callers
            "command": (require_api_key(self.legacy_command_endpoint), ["POST"]),
        }
        for route_name, (handler, methods) in routes.items():
            self.app.add_url_rule(
                f"/api/{route_name}",
                endpoint=route_name.replace("/", "_"),
                view_func=error_handler(handler),
                methods=methods,
            )

    def start_server(self):
        logger.info(f"Attempting to start server on port {self.port}...")
        # Guarantee a local API key before register/execute (persisted to configuration.ini).
        config.ensure_api_key()
        self.register_with_server()
        self._start_health_check()
        try:
            serve(
                self.app,
                host="0.0.0.0",
                port=self.port,
                threads=max(4, multiprocessing.cpu_count() * 2),
                channel_timeout=300,
                cleanup_interval=30,
                connection_limit=200,
            )
        except Exception as e:
            logger.error(f"Server failed to start: {e}")
            raise

    def register_with_server(self) -> bool:
        """Register with Django. Returns True on success. Retries later via health loop if False."""
        token = config.get_register_token()
        if not token:
            logger.warning("REGISTER_TOKEN empty; skipping auto-register.")
            return False

        local_key = config.ensure_api_key()
        payload = {
            "name": self.name,
            "local_ip": config.get_local_ip(),
            "port": self.port,
            "owner_username": config.get_owner_username() or None,
            "api_key": local_key,
            "commands": registry.list_dict(),
            "register_token": token,
        }
        url = f"{self.target_url}/api/clients/register"
        try:
            response = self.session.post(
                url,
                json=payload,
                headers={"X-Register-Token": token, "Content-Type": "application/json"},
                timeout=10,
            )
            data = response.json() if response.content else {}
            if response.status_code in (200, 201):
                body = data.get("data") or data
                server_key = (body.get("api_key") or "").strip()
                if server_key:
                    config.set_api_key(server_key, persist=True)
                self.client_db_id = body.get("id")
                logger.info(f"Registered with server as client id={self.client_db_id}")
                return True
            logger.error(f"Register failed ({response.status_code}): {data}")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning(
                f"Server not reachable at {self.target_url}. "
                "Start Django first (scripts\\start_server.bat). Will retry on next heartbeat."
            )
            return False
        except requests.exceptions.Timeout:
            logger.warning(f"Register timed out contacting {self.target_url}. Will retry later.")
            return False
        except Exception as e:
            logger.error(f"Register request failed: {e}")
            return False

    def _start_health_check(self):
        interval = config.get_health_interval()

        def health_check():
            while True:
                try:
                    # If we never registered (server was down at boot), keep trying.
                    if self.client_db_id is None:
                        if self.register_with_server():
                            logger.info("Deferred registration succeeded.")
                        threading.Event().wait(interval)
                        continue

                    payload = {
                        "name": self.name,
                        "local_ip": config.get_local_ip(),
                        "client_id": self.client_db_id,
                    }
                    headers = {"Content-Type": "application/json"}
                    api_key = config.get_api_key()
                    if api_key:
                        headers["X-Client-API-Key"] = api_key
                    response = self.session.post(
                        f"{self.target_url}/api/clients/health",
                        json=payload,
                        headers=headers,
                        timeout=5,
                    )
                    self.last_health_check = response.json() if response.content else None
                    if response.status_code == 401:
                        # Key mismatch (stale process / server key changed): force re-register.
                        logger.warning("Health 401 (API key mismatch). Re-registering to sync keys.")
                        self.client_db_id = None
                        self.register_with_server()
                    elif response.status_code != 200:
                        logger.warning(
                            f"Health report failed ({response.status_code}): {self.last_health_check}"
                        )
                except requests.exceptions.ConnectionError:
                    logger.warning(
                        f"Health: server not reachable at {self.target_url} "
                        "(is Django running on port 8000?)"
                    )
                except Exception as e:
                    logger.warning(f"Health check failed: {e}")
                threading.Event().wait(interval)

        threading.Thread(target=health_check, daemon=True).start()
        logger.info(f"Health heartbeat started (every {interval}s)")

    # ---------------- endpoints ----------------
    def health_check_endpoint(self):
        return jsonify(
            APIResponse.SystemInfoResponse(
                message="Health check successful",
                system_data={
                    "name": self.name,
                    "status": "healthy",
                    "port": self.port,
                    "last_health_check": self.last_health_check,
                    "commands": list(registry.list_dict().keys()),
                },
            ).to_dict()
        ), 200

    def command_list_endpoint(self):
        data = registry.list_dict()
        logger.info(f"command/list served ({len(data)} commands)")
        return jsonify(SuccessResponse("Command list", data).to_dict()), 200

    def command_execute_endpoint(self):
        json_data = request.get_json(silent=True) or {}
        command_id = json_data.get("command_id") or json_data.get("command")
        if not command_id:
            return jsonify(
                ErrorResponse("Missing command_id", config.LogLevel.ERROR).to_dict()
            ), 400

        command = registry.get(str(command_id))
        if command is None:
            logger.error(f"Command '{command_id}' not found in registered commands.")
            return jsonify(
                ErrorResponse(f"Command '{command_id}' not found.", config.LogLevel.ERROR).to_dict()
            ), 404

        args = json_data.get("args") or []
        kwargs = dict(json_data.get("kwargs") or {})
        # Merge positional-style convenience fields
        if isinstance(args, list):
            for index, value in enumerate(args):
                kwargs.setdefault(f"arg{index}", value)
        for key in ("message", "title", "time", "url", "path"):
            if key in json_data and key not in kwargs:
                kwargs[key] = json_data[key]

        # Map first free-form message into required args when useful
        if command.needs_message and "message" not in kwargs and args:
            kwargs["message"] = args[0]

        for arg_def in command.args:
            if arg_def.get("required") and arg_def.get("name") not in kwargs:
                return jsonify(
                    ErrorResponse(
                        f"Missing required argument: {arg_def.get('name')}",
                        config.LogLevel.WARNING,
                    ).to_dict()
                ), 400

        try:
            result, code = command.execute(**kwargs)
        except Exception as e:
            logger.error(f"Command '{command_id}' failed: {e}", exc_info=True)
            return jsonify(
                ErrorResponse(f"Command execution failed: {e}", config.LogLevel.ERROR).to_dict()
            ), 500

        if code == 200:
            # Keep API message short/neutral; the web UI maps command_id to user-facing text.
            user_message = "OK"
            if isinstance(result, dict) and result.get("message"):
                user_message = str(result.get("message"))
            elif isinstance(result, str) and result.strip():
                user_message = result
            return jsonify(
                SuccessResponse(
                    user_message,
                    result if isinstance(result, (dict, list)) else result,
                ).to_dict()
            ), 200
        # Avoid leaking internal command ids in error strings when possible
        err_text = str(result)
        return jsonify(
            ErrorResponse(err_text, config.LogLevel.ERROR).to_dict()
        ), code

    def legacy_command_endpoint(self):
        """Backward-compatible POST /api/command with {'command': name, ...}."""
        return self.command_execute_endpoint()
