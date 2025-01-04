from pathlib import Path
from typing import List

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
    model_name: str
    temperature: float


openai_config = OpenAIConfig()


class ResponseConfig(BaseSettings):
    """
    Configuration for response.
    """

    model_config = SettingsConfigDict(
        env_file=CONFIG_DIR / 'response.settings.env', env_file_encoding='utf-8'
    )

    system_prompt: str
    prompt_template: str
    prompt_template_color: str
    is_test_run: bool
    number_of_test_cases: int
    verify_certificate: bool


response_config = ResponseConfig()


class DataConfig(BaseSettings):
    """
    Configuration for the data ingestion.
    """

    model_config = SettingsConfigDict(
        env_file=CONFIG_DIR / 'data.settings.env', env_file_encoding='utf-8'
    )

    product_file_path_input: str
    attribute_file_path_input: str
    category_file_path_input: str

    product_file_path_output: str
    attribute_file_path_output: str
    category_file_path_output: str

    final_dataset_file_path: str

    product_columns: List[str]
    attribute_columns: List[str]
    category_columns: List[str]

    aggregation_column: str
    group_by_columns: List[str]

    final_dataset_colour_file_path: str


data_config = DataConfig()
