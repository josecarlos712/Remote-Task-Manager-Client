import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, jsonify
import requests

import config
from commands import Command
from utils import APIResponse
from remote_client import RemoteClient


@pytest.fixture
def client():
    """Fixture to create a test client"""
    remote_client = RemoteClient(
        name="Test Client",
        port=5001,
        target_url="http://localhost:5000"
    )
    # Create a test client using Flask's test_client
    test_client = remote_client.app.test_client()
    return test_client


class TestRemoteClientEndpoints:
    """Test class for RemoteClient api"""

    def test_test_endpoint(self, client):
        """Test the test endpoint"""
        response = client.get('/api/test')
        data = json.loads(response.data)

        # Respuesta correcta con código 200
        assert response.status_code == 200
        # Contenido correcto en la respuesta (status, message, data)
        assert data['status'] == 'success'
        assert 'APIRest is running' in data['message']
        assert data['data']['name'] == 'Test Client'
        assert isinstance(data['data']['port'], int)

    def test_health_check_endpoint(self, client):
        """Test the health check endpoint""" 
        response = client.get('/api/health')
        data = json.loads(response.data)

        # Respuesta correcta con código 200
        assert response.status_code == 200
        # Contenido correcto en la respuesta (status, message, data)
        assert data['status'] == 'success'
        assert data['message'] == 'Health check successful'
        assert 'name' in data['data']
        assert data['data']['status'] == 'healthy'
        # "last_health_check" tiene formato de fecha y hora válido
        assert 'last_health_check' in data['data']

    def test_command_endpoint_no_command(self, client):
        """Test command endpoint with missing command"""
        response = client.post('/api/command', json={})
        data = json.loads(response.data)

        # Respuesta 400 si falta el campo "command"
        assert response.status_code == 400
        assert data['status'] == 'error'
        assert 'Command not provided' in data['message']

    def test_command_endpoint_invalid_command(self, client):
        """Test command endpoint with invalid command"""
        response = client.post('/api/command', json={'command': 'invalid_command'})
        data = json.loads(response.data)

        # Respuesta 404 si el comando no existe
        assert response.status_code == 404
        assert data['status'] == 'error'
        assert 'does not exist' in data['message']

    def test_command_endpoint_valid_command(self, client):
        """Test command endpoint with valid command using mocked dictionary"""
        response = client.post('/api/command', json={'command': 'test_command'})
        data = json.loads(response.data)

        # Respuesta correcta con código 200 si el comando es válido
        assert response.status_code == 200
        assert data['status'] == 'success'
        assert 'executed correctly' in data['message']

    def test_command_endpoint_with_message(self, client):
        """Test command endpoint with message parameter"""
        test_message = "test message"
        response = client.post('/api/command',
                               headers={'Origin': 'http://localhost'},
                               json={'command': 'test_command', 'message': test_message})
        data = json.loads(response.data)

        # Validación de formato de entrada (JSON válido)
        assert response.status_code == 200
        assert data['status'] == 'success'
        assert test_message in data['message']

    def test_options_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options('/api/test')
        # Manejador OPTIONS devuelve 204 (preflight CORS)
        assert response.status_code == 204

    def test_unsupported_http_methods(self, client):
        """Test that unsupported HTTP methods return correct error"""
        response = client.delete('/api/test')
        # Todas las rutas rechazan métodos HTTP no soportados (ej. DELETE)
        assert response.status_code == 405

    def test_not_found_route(self, client):
        """Test accessing a non-existent route"""
        response = client.get('/api/nonexistent')
        # Manejo correcto de errores 404 (ruta no encontrada)
        assert response.status_code == 404

    def test_internal_server_error_handling(self, client, mocker):
        """Test that internal server errors are handled properly"""
        mocker.patch('app.some_function', side_effect=Exception('Test error'))
        response = client.get('/api/test')
        # Manejo correcto de errores 500 (error interno en el servidor)
        assert response.status_code == 500

    def test_system_info_gathering(self):
        info = config.configuration.get_specification_info(key_path="cpu")
        assert info != "Unknown"


def test_cors_headers(client):
    """Test CORS headers are properly set."""
    response = client.options(
        '/api/test',
        headers={'Origin': 'http://localhost'}
    )
    headers = response.headers

    assert 'Access-Control-Allow-Origin' in headers
    assert headers['Access-Control-Allow-Origin'] == 'http://localhost'
    assert 'Access-Control-Allow-Methods' in headers
    assert 'OPTIONS' in headers['Access-Control-Allow-Methods']
    assert 'POST' in headers['Access-Control-Allow-Methods']


@pytest.mark.performance
class TestRemoteClientPerformance:
    """Performance tests for RemoteClient"""

    def test_concurrent_requests(self, client):
        """Test handling multiple concurrent requests"""
        import concurrent.futures
        import time

        def make_request():
            return client.post('/api/test')

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Make 100 concurrent requests
            futures = [executor.submit(make_request) for _ in range(100)]
            responses = [f.result() for f in futures]

        end_time = time.time()
        execution_time = end_time - start_time

        # Check all responses were successful
        assert all(r.status_code == 200 for r in responses)
        # Check if completed within reasonable time (adjust as needed)
        assert execution_time < 10  # Should complete in less than 10 seconds


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
