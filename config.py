from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Configuration for the main function config.
    """

    model_config = SettingsConfigDict(env_file='settings.env')

    temperature: float


config = Config()
