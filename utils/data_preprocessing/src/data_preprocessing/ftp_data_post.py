import paramiko
import io
import os
from loguru import logger

from config.config import ftp_config, data_config


def post_json_to_ftp():
    """
    Connects to SFTP, changes to 'out/' directory, and uploads all JSON files
    from data_config.raw_data_path to the SFTP server.
    """
    host_address = ftp_config.host_address_integ if ftp_config.integ_or_prod == 'integ' else ftp_config.host_address_prod
    password = ftp_config.integ_password if ftp_config.integ_or_prod == 'integ' else ftp_config.prod_password

    sftp_client = None  # Initialize to None for finally block
    client = None       # Initialize to None for finally block

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
        
        # Change to the 'out/' directory on the SFTP server
        remote_out_dir = 'out/'
        try:
            sftp_client.chdir(remote_out_dir)
            current_remote_dir = sftp_client.getcwd() # Store the current remote directory
            logger.info(f"Successfully connected to SFTP and changed directory to: {current_remote_dir}")
        except IOError:
            logger.error(f"Remote directory '{remote_out_dir}' does not exist")
            raise IOError(f"Remote directory '{remote_out_dir}' does not exist")
            
    except Exception as e:
        logger.error(f'Unable to login to host_address: {host_address} with user: {ftp_config.username}')
        raise Exception(f'Unable to login to host_address: {host_address} with user: {ftp_config.username}. Error: {e}')    
        
    try:
        if not data_config.output_data_path or not os.path.isdir(data_config.raw_data_path):
            logger.error(f"Error: '{data_config.output_data_path}' is not a valid directory or is not provided.")
            raise ValueError("Path not valid")

        logger.info(f"Scanning local directory: {data_config.output_data_path} for JSON files to upload.")
        
        uploaded_count = 0
        for filename in os.listdir(data_config.output_data_path):
            if filename.endswith('.json'):
                local_file_full_path = os.path.join(data_config.output_data_path, filename)
                
                # Check if it's actually a file (not a subdirectory named .json)
                if os.path.isfile(local_file_full_path):
                    remote_destination_path = os.path.join(current_remote_dir, filename) 

                    logger.info(f"Uploading '{filename}' from '{local_file_full_path}' to '{remote_destination_path}' on SFTP")
                    try:
                        sftp_client.put(local_file_full_path, remote_destination_path)
                        logger.info(f"Successfully uploaded '{filename}'")
                        uploaded_count += 1
                    except Exception as upload_e:
                        logger.error(f"Failed to upload '{filename}': {upload_e}")
                else:
                    logger.warning(f"Skipping '{filename}' in '{data_config.output_data_path}' as it is not a regular file.")
            else:
                logger.info(f"Skipping '{filename}' as it is not a JSON file.")
        
        if uploaded_count == 0:
            logger.warning(f"No JSON files found in '{data_config.output_data_path}' to upload.")
        else:
            logger.info(f"Finished uploading {uploaded_count} JSON file(s) from '{data_config.output_data_path}'.")
                
    except Exception as e:
        logger.error(f"Error during file upload process: {e}")
        raise # Re-raise the exception after logging
                
    finally:
        if sftp_client:
            sftp_client.close()
            logger.info("SFTP connection closed.")
        if client:
            client.close()
            logger.info("SSH client closed.")
