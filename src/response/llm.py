from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field


class LLM(BaseModel):
    """
    Class which defines the LLM model.
    """

    model_name: Optional[str] = Field('gpt-4o', description='Model name for OpenAI')
    api_key: str = Field(..., description='API key for OpenAI')

    @property
    def client(self):
        return OpenAI(api_key=self.api_key)

    def get_client(self):
        return self.client
