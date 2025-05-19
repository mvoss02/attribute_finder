from typing import Optional, Literal

import openai
from pydantic import BaseModel, Field

from config import openai_config


class LLM(BaseModel):
    """
    Class which defines the LLM model.
    """

    model_name: Optional[str] = Field('gpt-4.1', description='Model name for OpenAI')
    api_key: str = Field(..., description='API key for OpenAI')
    api_base: str | None = Field(default=None, description='Überschreibt die Basis-URL (z.B. http://localhost:11434/v1)')
    provider: Literal['openai', 'ollama'] = Field(default='openai', description='Welcher Backend-Provider genutzt wird')

    def get_client(self):
        """
        Liefert einen OpenAI-kompatiblen Asnyc-Client
        * Für OpenAI -> api_base = None (SDK setzt https://api.openai.com/v1)
        * Für Ollama -> api_base = http://localhost:11434/v1
        """
        base = self.api_base
        if self.provider == 'ollama' and base is None:
            base = 'http://localhost:11434/v1'

        return openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=base
         )

    # Backwards-Kompatibilität
    @property
    def client(self):
        return self.get_client()


llm_client = LLM(api_key=openai_config.api_key, model_name=openai_config.model_name, api_base=openai_config.api_base, provider=openai_config.provider)