import paramiko
from loguru import logger

from config.config import ftp_config


def test_sftp_has_out_folder():
    """
    Minimal integration test:
      - Connects to the SFTP server using ftp_config
      - cd into 'out/' and verifies we can list it
    """
    host = ftp_config.host_address_integ if ftp_config.integ_or_prod == "integ" else ftp_config.host_address_prod
    password = ftp_config.integ_password if ftp_config.integ_or_prod == "integ" else ftp_config.prod_password

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=host,
            port=ftp_config.port,
            username=ftp_config.username,
            password=password,
            timeout=10,
        )
        sftp = client.open_sftp()
        # this is the only behavior we care about:
        sftp.chdir("out/")
        cwd = sftp.getcwd()
        listing = sftp.listdir()

        # Logging
        logger.debug(f"Successfully changed to directory: {cwd}")
        logger.debug(f"Listing of 'out/' folder: {listing}")

        # Very light assertions
        assert cwd.endswith("/out") or cwd == "out", f"Expected to be in 'out', got {cwd!r}"
        assert isinstance(listing, list), "Should be able to list items in 'out/'"

    finally:
        try:
            sftp.close()
        except Exception:
            pass
        client.close()
