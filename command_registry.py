"""
Modular command registry.

Built-in commands live in the `command_modules` package. Each module exposes:
  COMMAND_ID, TITLE, DESCRIPTION, ARGS, handler(**kwargs) -> (data|message, http_code)
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Callable, Dict, List, Optional

from config import logger

Handler = Callable[..., tuple[Any, int]]


class RegisteredCommand:
    def __init__(
        self,
        command_id: str,
        title: str,
        description: str,
        args: Optional[List[dict]] = None,
        handler: Optional[Handler] = None,
        needs_message: bool = False,
    ):
        self.command_id = command_id
        self.title = title
        self.description = description
        self.args = args or []
        self.handler = handler
        self.needs_message = needs_message

    def to_dict(self) -> dict:
        return {
            "command_id": self.command_id,
            "name": self.title or self.command_id,
            "description": self.description,
            "args": self.args,
        }

    def execute(self, **kwargs) -> tuple[Any, int]:
        if not self.handler:
            return f"No handler for {self.command_id}", 500
        return self.handler(**kwargs)


class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, RegisteredCommand] = {}

    def register(self, command: RegisteredCommand) -> None:
        self._commands[command.command_id] = command
        logger.info(f"Registered command '{command.command_id}'")

    def get(self, command_id: str) -> Optional[RegisteredCommand]:
        return self._commands.get(command_id)

    def list_dict(self) -> Dict[str, dict]:
        return {cid: cmd.to_dict() for cid, cmd in self._commands.items()}

    def list_items(self) -> List[dict]:
        return [cmd.to_dict() for cmd in self._commands.values()]

    def load_package(self, package_name: str = "command_modules") -> None:
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            logger.error(f"Could not import command package '{package_name}': {e}")
            return

        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if module_info.name.endswith(".blueprint"):
                continue
            try:
                module = importlib.import_module(module_info.name)
            except Exception as e:
                logger.warning(f"Failed loading command module {module_info.name}: {e}")
                continue

            command_id = getattr(module, "COMMAND_ID", None)
            handler = getattr(module, "handler", None)
            if not command_id or not callable(handler):
                logger.warning(f"Skipping {module_info.name}: missing COMMAND_ID/handler")
                continue

            self.register(
                RegisteredCommand(
                    command_id=command_id,
                    title=getattr(module, "TITLE", command_id),
                    description=getattr(module, "DESCRIPTION", ""),
                    args=getattr(module, "ARGS", []),
                    handler=handler,
                    needs_message=getattr(module, "NEEDS_MESSAGE", False),
                )
            )


registry = CommandRegistry()
