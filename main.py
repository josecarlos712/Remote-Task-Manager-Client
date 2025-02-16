from remote_client import RemoteClient


# Usage example for Point A
if __name__ == '__main__':
    server_socket = ("192.168.0.3", 8000)
    # Initialize and start the RemoteClient instance for Point A
    point_a = RemoteClient(name="Point A", port=5000, target_url=f'http://{server_socket[0]}:{server_socket[1]}')
    point_a.start_server()

    # Send a test request to Point B
    #point_a.send_request({"message": "Hello from Point A"})

# SUGGESTED FUTURE IMPROVEMENTS (not implemented):
"""
1. Configuration Management:
   - Move configuration to a separate config.py file
   - Use environment variables for sensitive data
   - Add configuration validation

2. Testing:
   - Add unit tests for each endpoint
   - Add integration tests for command system
   - Add load testing scripts

3. Additional Security:
   - Implement JWT authentication
   - Add rate limiting
   - Add request payload validation
   - Use HTTPS
   - Add input sanitization

4. Monitoring and Logging:
   - Add Prometheus metrics
   - Implement log rotation
   - Add request/response logging middleware
   - Add performance monitoring
   - Add a deeper check on a daily health check.

5. Error Handling:
   - Add custom exception classes
   - Add more granular error codes
   - Implement retry mechanism for failed requests

6. Performance:
   - Add response caching
   - Implement connection pooling
   - Add request queuing for high load

7. Documentation:
   - Add API documentation using Swagger/OpenAPI
   - Add deployment documentation
   - Add troubleshooting guide
   
Health check:
 - Path to programs on Commands class
"""