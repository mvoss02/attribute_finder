from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# Get the config directory
CONFIG_DIR = Path(__file__).parent

class OpenAIConfig(BaseSettings):
    """
    Configuration for the Openai API.
    """

    model_config = SettingsConfigDict(
        env_file=CONFIG_DIR / 'openai_credentials.env', env_file_encoding='utf-8'
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
        env_file=CONFIG_DIR / 'response.settings.env', env_file_encoding='utf-8'
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
        env_file=CONFIG_DIR / 'data.settings.env', env_file_encoding='utf-8'
    )

    raw_data_path: str
    output_data_path: str
    local_data_path: str
    attributes_data_path: str
    api_url: str
    number_of_articles: int
    number_of_runs: int
    get_already_processed_articles: bool
    data_source: Literal['local', 'api']


data_config = DataConfig()
