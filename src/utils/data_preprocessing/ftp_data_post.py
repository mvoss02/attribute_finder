import os
import re
import stat

import paramiko
from loguru import logger

from config.config import ftp_config
from config.paths import data_path_in


class FTPDataPoster:
    def __init__(self):
        self.host_address = (
            ftp_config.host_address_integ
            if ftp_config.integ_or_prod == 'integ'
            else ftp_config.host_address_prod
        )
        self.password = (
            ftp_config.integ_password
            if ftp_config.integ_or_prod == 'integ'
            else ftp_config.prod_password
        )
        self.client = None
        self.sftp_client = None

    # --- small helper: keep using os.path but ensure POSIX slashes for SFTP ---
    @staticmethod
    def _rjoin(*parts: str) -> str:
        return os.path.join(*parts).replace("\\", "/")

    def connect(self):
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
        if self.sftp_client:
            self.sftp_client.close()
            logger.info("SFTP connection closed.")
        if self.client:
            self.client.close()
            logger.info("SSH client closed.")

    def _ensure_done_dir(self):
        """
        Ensure /out/done exists (relative to SFTP root).
        """
        sftp = self.sftp_client
        try:
            sftp.chdir('out')
        except IOError:
            raise RuntimeError("Remote directory 'out/' does not exist")

        try:
            sftp.chdir('done')
        except IOError:
            # create and enter
            sftp.mkdir('done')
            sftp.chdir('done')
        # go back to /out for sanity
        sftp.chdir('..')

    def post_json_to_ftp(self) -> int:
        """
        Upload JSON files from local data_path_in to remote in/ directory.
        Returns the number of files uploaded.
        """
        try:
            self.connect()
            sftp = self.sftp_client

            # Change to in/ directory
            try:
                sftp.chdir('in/')
                current_remote_dir = sftp.getcwd()
                logger.info(f"Changed directory to: {current_remote_dir}")
            except IOError:
                logger.error("Remote directory 'in/' does not exist")
                raise

            if not data_path_in or not os.path.isdir(data_path_in):
                raise ValueError(f"'{data_path_in}' is not a valid local directory")

            uploaded = 0
            for filename in os.listdir(data_path_in):
                if not filename.endswith('.json'):
                    continue
                local_file_path = os.path.join(data_path_in, filename)
                if not os.path.isfile(local_file_path):
                    continue

                remote_path = self._rjoin(current_remote_dir, filename)
                logger.info(f"Uploading '{filename}' to '{remote_path}'")
                sftp.put(local_file_path, remote_path)
                uploaded += 1

            logger.success(f"Uploaded {uploaded} JSON file(s)")
            return uploaded

        except Exception as e:
            logger.error(f"Error during upload: {e}")
            raise
        finally:
            self.close()

    def move_to_done(self, files: list[str]) -> None:
        """
        Move all regular files from out/ to out/done/ via server-side rename.
        """
        try:
            self.connect()
            sftp = self.sftp_client

            # cd to /out
            sftp.chdir('out')

            # ensure 'done' exists
            try:
                sftp.stat('done')
            except IOError:
                logger.info("Creating 'done' directory under 'out/'.")
                sftp.mkdir('done')

            # find all regular files (ignore subdirectories)
            entries = sftp.listdir_attr('.')
            files = [e.filename for e in entries if stat.S_ISREG(e.st_mode) and e.filename in files]

            moved = 0
            for fname in files:
                src = fname
                dst = f"done/{fname}"
                try:
                    sftp.rename(src, dst)
                    logger.info(f"Moved: {src} -> {dst}")
                    moved += 1
                except IOError as e:
                    logger.warning(f"File '{fname}' could not be moved: {e}. Probably it already exists in 'done/'.")
                    # Delete file in done and retry
                    try:
                        sftp.remove(dst)
                        logger.warning(f"Deleted existing file in 'done/': {dst}. Retrying move.")
                        sftp.rename(src, dst)
                        logger.success(f"Moved: {src} -> {dst}")
                        moved += 1
                    except IOError as e2:
                        logger.error(f"Retry failed for moving '{fname}': {e2}")

            logger.info(f"Moved {moved}/{len(files)} file(s) to out/done/")

        except Exception as e:
            logger.error(f"Error during move: {e}")
            raise
        finally:
            self.close()


    def delete_files_from_ftp(self, files_to_delete):
        """
        Delete specified files from the SFTP `out/` directory.

        Args:
            files_to_delete (list[str]): List of filenames (basenames) to delete.
        """

        try:
            self.connect()

            try:
                self.sftp_client.chdir('out/')
                current_remote_dir = self.sftp_client.getcwd()
                logger.info(f"Changed directory to: {current_remote_dir}")
            except IOError:
                logger.error("Remote directory 'out/' does not exist")
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
