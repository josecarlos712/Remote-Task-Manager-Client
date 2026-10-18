import json
from unittest.mock import patch

import pytest

import config
from remote_client import RemoteClient


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setattr(config, "get_api_key", lambda: "test-key")
    return "test-key"


@pytest.fixture
def client(api_key, monkeypatch):
    monkeypatch.setattr(RemoteClient, "register_with_server", lambda self: None)
    monkeypatch.setattr(RemoteClient, "_start_health_check", lambda self: None)
    remote_client = RemoteClient(
        name="Test Client",
        port=5001,
        target_url="http://localhost:8000",
    )
    return remote_client.app.test_client()


class TestRemoteClientEndpoints:
    def test_health_check_endpoint(self, client):
        response = client.get("/api/health")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["data"]["status"] == "healthy"

    def test_command_list_requires_api_key(self, client):
        response = client.get("/api/command/list")
        assert response.status_code == 401

    def test_command_list_with_api_key(self, client, api_key):
        response = client.get("/api/command/list", headers={"X-Client-API-Key": api_key})
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["status"] == "success"
        assert "test_command" in data["data"]
        assert "show_popup" in data["data"]

    def test_command_execute_without_key(self, client):
        response = client.post(
            "/api/command/execute",
            json={"command_id": "test_command"},
        )
        assert response.status_code == 401

    def test_command_execute_with_key(self, client, api_key):
        response = client.post(
            "/api/command/execute",
            headers={"X-Client-API-Key": api_key},
            json={"command_id": "test_command", "kwargs": {"message": "hi"}},
        )
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["status"] == "success"

    def test_command_execute_unknown(self, client, api_key):
        response = client.post(
            "/api/command/execute",
            headers={"X-Client-API-Key": api_key},
            json={"command_id": "does_not_exist"},
        )
        data = json.loads(response.data)
        assert response.status_code == 404
        assert data["status"] == "error"

    def test_download_file_command_listed(self, client, api_key):
        response = client.get("/api/command/list", headers={"X-Client-API-Key": api_key})
        data = json.loads(response.data)
        assert response.status_code == 200
        assert "download_file" in data["data"]

    def test_download_file_starts_background(self, client, api_key, monkeypatch):
        from command_modules import download_file as df

        started = {"called": False}

        def fake_worker(job_id, url, save_dir, filename):
            started["called"] = True
            df._set_job(job_id, status="completed", path=str(save_dir / "x.bin"))

        monkeypatch.setattr(df, "_download_worker", fake_worker)
        response = client.post(
            "/api/command/execute",
            headers={"X-Client-API-Key": api_key},
            json={
                "command_id": "download_file",
                "kwargs": {"url": "https://civitai.com/api/download/models/1"},
            },
        )
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["status"] == "success"
        assert data["data"]["started"] is True
        assert "ComfyUI-Shared" in data["data"]["save_dir"]
        # worker runs in thread; give it a moment
        import time

        for _ in range(20):
            if started["called"]:
                break
            time.sleep(0.05)
        assert started["called"] is True
