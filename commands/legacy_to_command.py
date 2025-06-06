import os
import shutil
import logging

# Configure logging for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def restructure_commands_directory():
    """
    Restructures the current directory by moving individual command .py files
    into new subfolders, renaming them to 'command.py', and adding an __init__.py.

    Original structure:
    commands/
    ├── __init__.py
    ├── blueprint_command.py
    ├── my_command.py
    └── another_command.py

    New structure:
    commands/
    ├── __init__.py
    ├── blueprint_command.py
    ├── my_command/
    │   ├── command.py
    │   └── __init__.py
    └── another_command/
        ├── command.py
        └── __init__.py
    """
    # Get the directory where this Python script is located
    commands_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"=========================================================")
    logger.info(f"Starting Command File Restructuring")
    logger.info(f"Looking for command files in: '{commands_dir}'")
    logger.info(f"=========================================================")

    # Define files to explicitly exclude from being moved and renamed.
    # Add any other .py files in your 'commands' folder that are NOT individual commands.
    excluded_files = {
        '__init__.py',
        'blueprint_command.py',  # Your template file
        'Command.py',  # If you have a separate Command class file
        os.path.basename(__file__)  # Exclude this script itself
    }
    logger.info(f"Excluded files: {excluded_files}")

    processed_count = 0
    # Iterate through all items (files and directories) in the current directory
    for item_name in os.listdir(commands_dir):
        item_full_path = os.path.join(commands_dir, item_name)

        # Check if it's a Python file and not in the excluded list
        if os.path.isfile(item_full_path) and item_name.endswith('.py') and item_name not in excluded_files:
            logger.info(f"\n--- Processing: '{item_name}' ---")

            command_folder_name = os.path.splitext(item_name)[0]  # e.g., "my_command" from "my_command.py"
            new_command_folder_path = os.path.join(commands_dir, command_folder_name)
            new_command_entry_file_path = os.path.join(new_command_folder_path, 'command.py')
            new_init_file_path = os.path.join(new_command_folder_path, '__init__.py')

            try:
                # 1. Create the new directory
                if not os.path.exists(new_command_folder_path):
                    logger.info(f"Creating directory: '{new_command_folder_path}'")
                    os.makedirs(new_command_folder_path)  # Use makedirs for parent directories too, if ever needed
                else:
                    logger.info(f"Directory already exists: '{new_command_folder_path}'")

                # 2. Move and rename the original .py file
                # shutil.move handles moving across filesystems and renaming in one go.
                # os.rename can move and rename if source/dest are on same filesystem.
                logger.info(f"Moving '{item_name}' to '{new_command_folder_path}' and renaming to 'command.py'")
                shutil.move(item_full_path, new_command_entry_file_path)
                logger.info(
                    f"Successfully moved and renamed '{item_name}' to '{os.path.basename(new_command_entry_file_path)}'")

                # 3. Create an empty __init__.py file in the new directory
                if not os.path.exists(new_init_file_path):
                    logger.info(f"Creating __init__.py in '{new_command_folder_path}'")
                    with open(new_init_file_path, 'w') as f:
                        pass  # Create an empty file
                    logger.info(f"Successfully created '{os.path.basename(new_init_file_path)}'")
                else:
                    logger.info(f"__init__.py already exists in '{new_command_folder_path}'")

                processed_count += 1
                logger.info(f"Successfully processed '{item_name}'")

            except FileExistsError:
                logger.error(
                    f"Error processing '{item_name}': Target file '{new_command_entry_file_path}' already exists. Skipping.")
            except FileNotFoundError:
                logger.error(
                    f"Error processing '{item_name}': Original file '{item_full_path}' not found (might have been moved/deleted). Skipping.")
            except PermissionError:
                logger.error(
                    f"Error processing '{item_name}': Permission denied. Please ensure you have write permissions to '{commands_dir}'. Skipping.")
            except Exception as e:
                logger.error(f"An unexpected error occurred while processing '{item_name}': {e}", exc_info=True)
        else:
            logger.debug(f"Skipping '{item_name}': Not a .py file or is excluded/already a directory.")

    logger.info(f"\n=========================================================")
    logger.info(f"Command refactoring complete! Processed {processed_count} command files.")
    logger.info(f"=========================================================")


if __name__ == "__main__":
    restructure_commands_directory()
