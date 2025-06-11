import paramiko
import io
import os
from loguru import logger

from config.config import ftp_config, data_config
        

class FTPDataPoster:
    def __init__(self):
        """
        Initialize FTP connection parameters
        """
        
        self.host_address = ftp_config.host_address_integ if ftp_config.integ_or_prod == 'integ' else ftp_config.host_address_prod
        self.password = ftp_config.integ_password if ftp_config.integ_or_prod == 'integ' else ftp_config.prod_password
        self.client = None
        self.sftp_client = None

    def connect(self):
        """
        Establish SFTP connection
        """
        
        try:
            logger.info(f"Connecting to SFTP with host_address: {self.host_address} and user: {ftp_config.username}")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host_address,
                port=ftp_config.port,
                username=ftp_config.username,
                password=self.password,
            )
            self.sftp_client = self.client.open_sftp()
        except Exception as e:
            logger.error(f'Unable to login to host_address: {self.host_address} with user: {ftp_config.username}')
            raise Exception(f'Unable to login to SFTP server. Error: {e}')

    def close(self):
        """
        Close SFTP connections
        """
        
        if self.sftp_client:
            self.sftp_client.close()
            logger.info("SFTP connection closed.")
        if self.client:
            self.client.close()
            logger.info("SSH client closed.")

    def post_json_to_ftp(self):
        """
        Upload JSON files to SFTP out/ directory
        """
        
        try:
            self.connect()
            
            # Change to out/ directory
            try:
                self.sftp_client.chdir('out/')
                current_remote_dir = self.sftp_client.getcwd()
                logger.info(f"Changed directory to: {current_remote_dir}")
            except IOError as e:
                logger.error("Remote directory 'out/' does not exist")
                raise

            if not data_config.output_data_path or not os.path.isdir(data_config.output_data_path):
                raise ValueError(f"'{data_config.output_data_path}' is not a valid directory")

            uploaded_count = 0
            for filename in os.listdir(data_config.output_data_path):
                if filename.endswith('.json'):
                    local_file_path = os.path.join(data_config.output_data_path, filename)
                    if os.path.isfile(local_file_path):
                        remote_path = os.path.join(current_remote_dir, filename)
                        logger.info(f"Uploading '{filename}' to '{remote_path}'")
                        self.sftp_client.put(local_file_path, remote_path)
                        uploaded_count += 1

            logger.info(f"Uploaded {uploaded_count} JSON files")

        except Exception as e:
            logger.error(f"Error during upload: {e}")
            raise
        finally:
            self.close()

    def delete_files_from_ftp(self, files_to_delete):
        """
        Delete specified files from SFTP in/ directory
        
        Args:
            files_to_delete (list): List of filenames to delete
        """
        
        try:
            self.connect()
            
            try:
                self.sftp_client.chdir('in/')
                current_remote_dir = self.sftp_client.getcwd()
                logger.info(f"Changed directory to: {current_remote_dir}")
            except IOError:
                logger.error("Remote directory 'in/' does not exist")
                raise

            deleted_count = 0
            for filename in files_to_delete:
                try:
                    self.sftp_client.remove(filename)
                    logger.info(f"Deleted file: {filename}")
                    deleted_count += 1
                except IOError as e:
                    logger.error(f"Could not delete {filename}: {e}")

            logger.info(f"Deleted {deleted_count} files")

        except Exception as e:
            logger.error(f"Error during deletion: {e}")
            raise
        finally:
            self.close()
