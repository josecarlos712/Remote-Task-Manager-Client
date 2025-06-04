import logging
import os
import importlib

logger = logging.getLogger(__name__)


class EndpointsLoader:
    """
    This class is responsible for loading and registering API endpoints from the 'api' folder.
    Each Python file (`*.py`) inside `api/` is treated as an independent endpoint.
    Each folder inside `api/` represents a sub-level and must contain an `endpoint.py` file.
    The `register()` function inside each file is called with `app` as an argument.
    """

    def __init__(self, app):
        self.app = app

    def load_endpoints(self, relative_path: str) -> tuple[str, int]:
        """
        Recursively loads API endpoints from the 'api' folder.

        - Each Python file (`*.py`) inside `api/` is treated as an independent endpoint.
        - Each folder inside `api/` represents a sub-level and must contain an `endpoint.py` file.
        - The `register()` function inside each file is called with `app` as an argument.

        :param relative_path: Relative path from the `api` folder to the endpoints.
        :param app: Flask application instance.
        """
        api_folder = os.path.join(os.path.dirname(__file__), '..')
        excluded = {'__init__.py', 'blueprint_endpoint.py', '__pycache__', 'disabled'}

        # Register all the endpoints inside the folder
        api_items = os.listdir(api_folder + '/' + relative_path.strip('/').replace('\\', '/'))
        for item in api_items:
            full_path = os.path.join(api_folder, relative_path, item)

            if item in excluded:
                continue  # Skip excluded files and directories

            if os.path.isfile(full_path) and item.endswith('.py') and not item.endswith('endpoint.py'):
                # Register single-file API endpoints
                api_path = relative_path + '/' + item[:-3]  # Remove .py extension
                self.register_endpoint(api_path)

            elif os.path.isdir(full_path):
                # Register complex API endpoints (folders with `endpoint.py` inside)
                api_path = relative_path + '/' + item
                self.register_endpoint(api_path)
        return "Endpoints loaded successfully", 200  # Return success message

    def register_endpoint(self, api_path: str) -> tuple[str, int]:
        """ Helper function to import and register an endpoint. """
        api_folder = os.path.join(os.path.dirname(__file__), '..')

        if not api_path:
            return "API path null", 400  # Bad request if api_path is empty

        module_path = api_path.replace('/', '.')
        endpoint_name = os.path.basename(api_path)

        # Check if the path is an endpoint or a folder (a .py file of a folder with 'endpoint.py')
        if os.path.isfile(os.path.join(api_folder, f"{api_path}.py")):
            module_path = f'{module_path}'  # Single-file endpoint
        elif os.path.isdir(os.path.join(api_folder, api_path)):
            module_path = f'{module_path}.endpoint'  # sub-level
        else:
            return "Invalid API path", 404  # Not found if the path does not exist

        # Try to import and register the module
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, 'register'):  # Check if the module has a 'register()' function
                response, code = module.register(self, self.app, api_path)
                if code == 200:
                    #logger.debug(f"enpoint_loader - {response} for '{endpoint_name}'")
                    return "Endpoint registered", code
                else:
                    logger.warning(f"Registration failed for '{endpoint_name}'")
                    return response, code  # Return the response and code from the register function
            else:
                logger.warning(f"No 'register()' function found in '{module_path}'")
                return f"No 'register()' function found in '{module_path}'", 500  # Internal server error if no register function
        except Exception as e:
            logger.error(f"Error loading '{module_path}': {e}")
            return f"Error loading endpoint '{module_path}': {e}", 500
