from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseSettings):
    """
    Configuration for the Openai API.
    """

    model_config = SettingsConfigDict(
        env_file='config/openai_credentials.env', env_file_encoding='utf-8'
    )

    api_key: str
    api_base: str
    model_name: str
    temperature: float
    max_tokens: int
    provider: Literal['openai', 'ollama'] = 'openai'


openai_config = OpenAIConfig()


class ResponseConfig(BaseSettings):
    """
    Configuration for response.
    """

    model_config = SettingsConfigDict(
        env_file='config/response.settings.env', env_file_encoding='utf-8'
    )

    system_prompt_attribute: str
    system_prompt_color: str
    prompt_template_attribute: str
    prompt_template_color: str
    verify_certificate: bool


response_config = ResponseConfig()


class DataConfig(BaseSettings):
    """
    Configuration for the data ingestion.
    """

    model_config = SettingsConfigDict(
        env_file='config/data.settings.env', env_file_encoding='utf-8'
    )

    raw_data_path: str
    output_data_path: str
    number_of_articles: int
    number_of_runs: int
    get_already_processed_articles: bool


data_config = DataConfig()


class FTPConfig(BaseSettings):
    """
    Configuration for the data ingestion from the FTP Server.
    """
    
    model_config = SettingsConfigDict(
        env_file='config/ftp.settings.env', env_file_encoding='utf-8'
    )
    
    host_address_integ: str
    host_address_prod: str
    port: int
    username: str
    integ_password: str
    prod_password: str
    integ_or_prod: Literal['integ', 'prod'] # Using 'prod' (production) or 'integ' (integration/development) system


ftp_config = FTPConfig()
