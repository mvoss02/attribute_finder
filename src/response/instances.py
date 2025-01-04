from src.config import openai_config

from .llm import LLM

llm_client = LLM(api_key=openai_config.api_key, model_name=openai_config.model_name)
