import os
import importlib
from config import logger


def load_endpoints(app):
    """
    Loads dynamic endpoints from the 'endpoints' folder.

    This function supports two types of endpoints:

    1. Simple endpoints: If a .py file is found in the root of the 'endpoints' folder, it is treated as an independent
       endpoint. The endpoint name is derived from the filename (without the .py extension).

    2. Complex endpoints: If a folder is found inside 'endpoints', it is considered a complex endpoint that consists
       of multiple files. The function 'register' must be inside a file named 'endpoint.py' within that folder.
       The endpoint name is the folder name.

    The function attempts to import and register each valid endpoint. If registration fails, a warning is logged.

    :param app: The Flask application instance where endpoints should be registered.
    """

    loaded_modules = {}  # Stores successfully loaded modules
    endpoint_folder = os.path.join(os.path.dirname(__file__), '..', 'endpoints')

    for item in os.listdir(endpoint_folder):
        excluded_files = ['__init__.py', 'blueprint_endpoint.py']
        full_path = os.path.join(endpoint_folder, item)

        if os.path.isfile(full_path) and item.endswith('.py') and item not in excluded_files:
            # Simple endpoint (.py file in the root folder)
            module_name = item[:-3]
            module_path = f'endpoints.{module_name}'

        elif os.path.isdir(full_path):
            # Complex endpoint (folder containing an 'endpoint.py' file)
            module_name = item  # The endpoint name is the folder name
            endpoint_file = os.path.join(full_path, 'endpoint.py')

            if not os.path.exists(endpoint_file):
                logger.warn(f"Skipping '{module_name}': 'endpoint.py' not found in folder.")
                continue  # Required file not found, skipping

            module_path = f'endpoints.{module_name}.endpoint'

        else:
            continue  # Neither a valid .py file nor a folder

        # Attempt to import and register the module
        loaded_modules[module_name] = False
        try:
            module = importlib.import_module(module_path)

            if hasattr(module, 'register'):
                try:
                    if module.register(app, module_name) == 0:
                        loaded_modules[module_name] = True
                    else:
                        raise ImportError(f"Failed to register endpoint '{module_name}'.")
                except Exception as e:
                    logger.warn(f"Failed on 'register()' function for '{module_name}'. - {e}")

        except Exception as e:
            logger.warn(f"Failed to load module '{module_name}' - {e}")

        if loaded_modules[module_name]:
            logger.debug(f"Loaded module '{module_name}' - OK")