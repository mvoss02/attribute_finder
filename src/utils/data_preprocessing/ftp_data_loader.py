import io
import os

import paramiko
from loguru import logger

from config.paths import data_path_out

from config.config import ftp_config


def load_json_from_ftp(batch_size: int = None):
    """
    Load JSON files from FTP server, optionally in batches.

    Args:
        batch_size (int, optional): Maximum number of files to download in this batch.
                                   If None, downloads all files.

    Returns:
        int: Number of files actually downloaded
    """
    host_address = ftp_config.host_address_integ if ftp_config.integ_or_prod == 'integ' else ftp_config.host_address_prod
    password = ftp_config.integ_password if ftp_config.integ_or_prod == 'integ' else ftp_config.prod_password

    try:
        # Connect to SFTP
        logger.info(f"Connecting to SFTP with host_address: {host_address} and user: {ftp_config.username}")

        # Create an SSHClient object
        client = paramiko.SSHClient()

        # Automatically add host key
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server
        client.connect(
            hostname=host_address,
            port=ftp_config.port,
            username=ftp_config.username,
            password=password,
        )

        # Open SFTP session
        sftp_client = client.open_sftp()

        # Change to the 'out/' directory
        # Novomind puts files into out/ folder - we read from there - put them back to in/ folder
        sftp_client.chdir('out/')
        current_dir = sftp_client.getcwd()

        logger.info(f"Successfully connected to SFTP and changed directory to: {current_dir}")

    except Exception as e:
        logger.error(f'Unable to login to host_address: {host_address} with user: {ftp_config.username}')
        raise Exception(f'Unable to login to host_address: {host_address} with user: {ftp_config.username}. Error: {e}')

    files_downloaded = 0

    try:
        # Get all folders in the given directory
        file_list = sftp_client.listdir()
        logger.info(f"Found {len(file_list)} item(s) under {current_dir}: {file_list}")

        # Filter only JSON files
        json_files = [f for f in file_list if f.endswith('.json')]
        logger.info(f"Found {len(json_files)} JSON files in 'out/'.")

        # Apply batch limit if specified
        if batch_size is not None:
            json_files = json_files[:batch_size]
            logger.info(f"Processing batch of {len(json_files)} files (batch_size={batch_size})")

        for filename in json_files:
            logger.info(f"\n Reading content of '{filename}' from SFTP")
            try:
                # Create an in-memory binary stream to store the file content temporarily
                file_content_buffer = io.BytesIO()

                # Download file content to buffer
                with sftp_client.open(filename, 'rb') as remote_file:
                    file_content_buffer.write(remote_file.read())

                file_content_buffer.seek(0)  # Go to the beginning of the stream

                # Create the local directory if it doesn't exist
                os.makedirs(data_path_out, exist_ok=True)

                # Define the full local path for saving the file
                local_file_path = os.path.join(data_path_out, filename)

                logger.info(f"Saving '{filename}' to '{local_file_path}'")

                # Open the local file in binary write mode ('wb')
                with open(local_file_path, 'wb') as local_file:
                    local_file.write(file_content_buffer.getvalue())  # Write the entire buffer content

                logger.info(f"Successfully saved '{filename}' locally")
                files_downloaded += 1

            except Exception as e:
                logger.error(f"Error retrieving or saving '{filename}': {e}")

    except Exception as e:
        logger.error(f"Error retrieving files. Error: {e}")

    finally:
        # Close SFTP connection and transport
        sftp_client.close()
        logger.info(f"SFTP connection closed. Downloaded {files_downloaded} files.")

    return files_downloaded
