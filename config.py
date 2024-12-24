from pydantic_settings import BaseSettings, SettingsConfigDict


class CryptopanicConfig(BaseSettings):
    """
    Configuration for the Openai API.
    """

    model_config = SettingsConfigDict(env_file='openai_credentials.env')
    api_key: str


openai_config = CryptopanicConfig()