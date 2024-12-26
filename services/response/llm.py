from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional
from config import openai_config


class LLM(BaseModel):
    model_name: Optional[str] = Field("gpt-4o", description="Model name for OpenAI")
    api_key: str = Field(..., description="API key for OpenAI")
    
    @property
    def client(self):
        return OpenAI(api_key=self.api_key)
    
    def get_client(self):
        return self.client

openai_config = openai_config
llm_client = LLM(api_key=openai_config.api_key, model_name=openai_config.model_name)