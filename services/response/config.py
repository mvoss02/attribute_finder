from pydantic_settings import BaseSettings, SettingsConfigDict


class CryptopanicConfig(BaseSettings):
    """
    Configuration for the Openai API.
    """

    model_config = SettingsConfigDict(env_file='openai_credentials.env')
    api_key: str
    model_name: str
    temperature: float
    max_tokens: int


openai_config = CryptopanicConfig()

class Config(BaseSettings):
    """
    Configuration for the response object.
    """

    model_config = SettingsConfigDict(env_file='settings.env')
    prompt: str


config = Config()