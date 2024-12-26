from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseSettings):
    """
    Configuration for the Openai API.
    """

    model_config = SettingsConfigDict(env_file='openai_credentials.env')
    api_key: str
    model_name: str


openai_config = OpenAIConfig()


class ResponseConfig(BaseSettings):
    """
    Configuration for response.
    """

    model_config = SettingsConfigDict(env_file='settings.env')
    system_prompt: str
    prompt_template: str
    prompt_template_color: str


response_config = ResponseConfig()
