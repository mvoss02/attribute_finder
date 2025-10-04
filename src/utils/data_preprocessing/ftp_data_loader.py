import io
import os
import posixpath
import re
import stat
from datetime import datetime

import paramiko
from loguru import logger

from config.config import ftp_config
from config.paths import data_path_out


def load_json_from_ftp(batch_size: int = None) -> int:
    """
    Load JSON files from SFTP server, only from date-based subfolders (YYYYMMDD) under '/out'.
    """
    host_address = ftp_config.host_address_integ if ftp_config.integ_or_prod == "integ" else ftp_config.host_address_prod
    password = ftp_config.integ_password if ftp_config.integ_or_prod == "integ" else ftp_config.prod_password

    client = None
    sftp = None
    files_downloaded = 0
    base_dir = "/out"  # absolute path; avoids relative confusion

    try:
        logger.info(f"Connecting to SFTP with host_address: {host_address} and user: {ftp_config.username}")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host_address, port=ftp_config.port, username=ftp_config.username, password=password)

        sftp = client.open_sftp()

        # --- discover date folders under /out ---
        entries = sftp.listdir_attr(base_dir)
        date_dirs = []
        for e in entries:
            if stat.S_ISDIR(e.st_mode) and re.fullmatch(r"\d{8}", e.filename):
                try:
                    datetime.strptime(e.filename, "%Y%m%d")
                    date_dirs.append(e.filename)
                except ValueError:
                    pass

        logger.info(f"Found {len(date_dirs)} date folders under {base_dir}: {date_dirs}")

        if not date_dirs:
            logger.warning("No date folders found; nothing to download.")
            return 0

        # --- collect JSON files inside those folders ---
        json_remote_paths = []
        for d in sorted(date_dirs):
            remote_subdir = posixpath.join(base_dir, d)          # e.g. /out/20250626
            try:
                names = sftp.listdir(remote_subdir)              # list relative to absolute /out/20250626
            except Exception as e:
                logger.error(f"Unable to list folder '{remote_subdir}': {e}")
                continue

            jsons = [n for n in names if n.endswith(".json")]
            logger.info(f"Folder {remote_subdir}: {len(jsons)} JSON file(s): {jsons}")
            json_remote_paths.extend([posixpath.join(remote_subdir, n) for n in jsons])

        # batch limit
        if batch_size is not None:
            json_remote_paths = json_remote_paths[:batch_size]
            logger.info(f"Processing batch of {len(json_remote_paths)} files (batch_size={batch_size})")
        else:
            logger.info(f"Processing {len(json_remote_paths)} files (no   limit)")

        if not json_remote_paths:
            logger.info("No JSON files found in the date folders; nothing to download.")
            return 0

        # --- download ---
        os.makedirs(data_path_out, exist_ok=True)

        for remote_path in json_remote_paths:
            filename = posixpath.basename(remote_path)
            logger.info(f"Reading '{remote_path}'")
            try:
                buf = io.BytesIO()
                with sftp.open(remote_path, "rb") as rf:
                    buf.write(rf.read())
                buf.seek(0)

                local_path = os.path.join(data_path_out, filename)
                with open(local_path, "wb") as lf:
                    lf.write(buf.getvalue())

                logger.info(f"Saved to '{local_path}'")
                files_downloaded += 1

            except Exception as e:
                logger.error(f"Error retrieving or saving '{remote_path}': {e}")

        return files_downloaded

    except Exception as e:
        logger.error(f"FTP error (host: {host_address}, user: {ftp_config.username}): {e}")
        raise
    finally:
        try:
            if sftp:
                sftp.close()
        finally:
            if client:
                client.close()
        logger.info(f"SFTP connection closed. Downloaded {files_downloaded} files.")
