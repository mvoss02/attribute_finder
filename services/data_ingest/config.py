from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Configuration for the data ingestion service.
    """

    model_config = SettingsConfigDict(env_file='settings.env')

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


config = Config()
