from pathlib import Path

# Root
root = Path(__file__).parent.parent.parent

# Main folders
src = root / "src"
config = src / "config"
data = root / "data"

# Env file paths
ftp_env_file = config / "ftp.settings.env"
data_env_file = config / "data.settings.env"
openai_env_file = config / "openai_credentials.env"
response_env_file = config / "response.settings.env"

# Data paths
data_path_in = data / "in"
data_path_out = data / "out"
data_path_temp_img = data / "temp_images"
