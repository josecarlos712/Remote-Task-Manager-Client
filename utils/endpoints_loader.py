import os
import importlib
from config import logger


def load_endpoints(app):
    # Store what modules are successfully loaded. Failed ones can't be used.
    loaded_modules = {}
    # Get the list of files in the endpoints folder
    endpoint_folder = os.path.join(os.path.dirname(__file__), '..', 'endpoints')
    for filename in os.listdir(endpoint_folder):
        excluded_files = ['__init__.py', 'blueprint_endpoint.py']
        if filename.endswith('.py') and filename not in excluded_files:
            # Remove the .py extension to get the module name
            module_name = filename[:-3]
            # Import the module dynamically
            loaded_modules[module_name] = False # Set module imported to False until it's imported successfully
            try:
                #logger.debug(f"Trying to load module \'{module_name}\'.")
                module = importlib.import_module(f'endpoints.{module_name}')
                # Call the register function (if it exists)
                if hasattr(module, 'register'):
                    try:
                        if module.register(app, module_name) == 0:
                            loaded_modules[module_name] = True
                        else:
                            raise ImportError(f"Failed to import module {module_name}.")
                    except Exception as e:
                        logger.warn(f"Failed on \'register()\' function. - {e}")
            except Exception as e:
                logger.warn(f"Failed to load module \'{module_name}\' - {e}")
            if loaded_modules[module_name]:
                logger.debug(f"Loaded module \'{module_name}\' - OK")
