import os

from loguru import logger


def cleanup_files(dir_path_to_delete: str):
    # Step 6: Delete article from ./data/in/ locally
    logger.info(f'Deleting all the json from {dir_path_to_delete}')

    if not os.path.exists(dir_path_to_delete):
        logger.info(f"Directory '{dir_path_to_delete}' does not exist")
    else:
        for filename in os.listdir(dir_path_to_delete):
            file_path = os.path.join(dir_path_to_delete, filename)
            try:
                if os.path.isfile(file_path):  # Ensure it's a file, not a subdirectory
                    os.remove(file_path)
                    logger.info(f"Deleted: {file_path}")
            except Exception as e:
                logger.info(f"Error deleting {file_path}: {e}")