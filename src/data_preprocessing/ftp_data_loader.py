import paramiko
import io
import os
from loguru import logger

from config.config import ftp_config


def load_json_from_ftp():
    host_address = ftp_config.host_address_integ if ftp_config.integ_or_prod == 'integ' else ftp_config.host_address_prod
    password = ftp_config.integ_password if ftp_config.integ_or_prod == 'integ' else ftp_config.prod_password

    try:
        # Connect to SFTP
        logger.info(f"Connecting to SFTP with host_address: {host_address} and user: {ftp_config.username}")
        
        # Create an SSHClient object
        client = paramiko.SSHClient()

        # Automatically add host key
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print('PASSWORD:', password)

        # Connect to the server
        client.connect(
            hostname=host_address,
            port=ftp_config.port,
            username=ftp_config.username,
            password=password,
        )

        # Open SFTP session
        sftp_client = client.open_sftp()
        
        # Change to the 'in/' directory
        sftp_client.chdir('in/')
        current_dir = sftp_client.getcwd()
        
        logger.info(f"Successfully connected to SFTP and changed directory to: {current_dir}")
        
    except Exception as e:
        logger.error(f'Unable to login to host_address: {host_address} with user: {ftp_config.username}')
        raise Exception(f'Unable to login to host_address: {host_address} with user: {ftp_config.username}. Error: {e}')    
        
    try:
        # Get all files in the given directory
        file_list = sftp_client.listdir()
        logger.info(f"Found {len(file_list)} items in 'in/'.")
        
        for filename in file_list:
            # Check if the filename ends with '.json'
            if filename.endswith('.json'):
                logger.info(f"\n Reading content of '{filename}' from SFTP")
                try:
                    # Create an in-memory binary stream to store the file content temporarily
                    file_content_buffer = io.BytesIO()
                    
                    # Download file content to buffer
                    with sftp_client.open(filename, 'rb') as remote_file:
                        file_content_buffer.write(remote_file.read())
                    
                    file_content_buffer.seek(0)  # Go to the beginning of the stream
                    
                    # Create the local directory if it doesn't exist
                    os.makedirs(ftp_config.local_save_directory, exist_ok=True)

                    # Define the full local path for saving the file
                    local_file_path = os.path.join(ftp_config.local_save_directory, filename)

                    logger.info(f"Saving '{filename}' to '{local_file_path}'")
                    
                    # Open the local file in binary write mode ('wb')
                    with open(local_file_path, 'wb') as local_file:
                        local_file.write(file_content_buffer.getvalue())  # Write the entire buffer content

                    logger.info(f"Successfully saved '{filename}' locally")

                except Exception as e:
                    logger.error(f"Error retrieving or saving '{filename}': {e}")

            else:
                logger.warning(f"Skipping '{filename}' as it is not a .json file.")
                
    finally:
        # Close SFTP connection and transport
        sftp_client.close()
        logger.info("SFTP connection closed.")
        