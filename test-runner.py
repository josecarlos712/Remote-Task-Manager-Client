# test_runner.py
import pytest
import sys


def main():
    """
    Run all tests and print a summary of what was tested.
    This helps ensure all endpoints are being tested.
    """
    # Print test plan
    print("Remote Client Test Suite")
    print("=======================")
    print("\nEndpoints being tested:")
    print("1. /api/test - Basic API health check")
    print("2. /api/command - Command execution")
    print("3. /api/health - Health check endpoint")

    print("\nTest Categories:")
    print("- Unit Tests (endpoint behavior)")
    print("- Integration Tests (client communication)")
    print("- Performance Tests (concurrent requests)")
    print("- CORS Tests (security headers)")

    # Run the tests
    print("\nRunning all tests...\n")
    exit_code = pytest.main([
        'test.py',  # your test file
        '-v',  # verbose output
        '--tb=short',  # shorter traceback
        '-rA'  # show all test summary info
    ])

    return exit_code


if __name__ == '__main__':
    sys.exit(main())