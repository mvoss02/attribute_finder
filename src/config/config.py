import os
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from config.paths import data_env_file, ftp_env_file, openai_env_file, response_env_file

# Load env files
load_dotenv(ftp_env_file)
load_dotenv(data_env_file)
load_dotenv(openai_env_file)
load_dotenv(response_env_file)


class OpenAIConfig(BaseSettings):
    """
    Configuration for the Openai API.
    """

    api_key: str = os.environ["API_KEY"]
    api_base: str = os.environ["API_BASE"]
    model_name: str = os.environ["MODEL_NAME"]
    temperature: float = os.environ["TEMPERATURE"]
    max_tokens: int = os.environ["MAX_TOKENS"]
    provider: Literal['openai', 'ollama'] = os.environ["PROVIDER"]


openai_config = OpenAIConfig()


class ResponseConfig(BaseSettings):
    """
    Configuration for response.
    """

    system_prompt_attribute: str = os.environ["SYSTEM_PROMPT_ATTRIBUTE"]
    system_prompt_color: str = os.environ["SYSTEM_PROMPT_COLOR"]
    prompt_template_attribute: str = os.environ["PROMPT_TEMPLATE_ATTRIBUTE"]
    prompt_template_color: str = os.environ["PROMPT_TEMPLATE_COLOR"]
    verify_certificate: bool = os.environ["VERIFY_CERTIFICATE"]


response_config = ResponseConfig()


class DataConfig(BaseSettings):
    """
    Configuration for the data ingestion.
    """

    number_of_articles: int = os.environ["NUMBER_OF_ARTICLES"]
    number_of_runs: int = os.environ["NUMBER_OF_RUNS"]
    get_already_processed_articles: bool = os.environ["GET_ALREADY_PROCESSED_ARTICLES"]
    batch_size: int = os.environ["BATCH_SIZE"]


data_config = DataConfig()


class FTPConfig(BaseSettings):
    """
    Configuration for the data ingestion from the FTP Server.
    """

    host_address_integ: str = os.environ["HOST_ADDRESS_INTEG"]
    host_address_prod: str = os.environ["HOST_ADDRESS_PROD"]
    port: int = os.environ["PORT"]
    username: str = os.environ["USERNAME"]
    integ_password: str = os.environ["INTEG_PASSWORD"]
    prod_password: str = os.environ["PROD_PASSWORD"]
    integ_or_prod: Literal['integ', 'prod'] = os.environ["INTEG_OR_PROD"]


ftp_config = FTPConfig()
