import base64
from openai import OpenAI
from typing import List, Optional
from pydantic import BaseModel, Field


class ResponseObject(BaseModel):
    model_name: Optional[str] = Field("gpt-4o", description="Model name for OpenAI")
    api_key: str = Field(..., description="API key for OpenAI")
    temperature: Optional[float] = Field(0, description="Temperature for OpenAI")
    categories: List[str] = Field([""], description="Categories for the corresponding product category")
    brand: str = Field("", description="The brand for the corresponding product")
    prompt: str = Field("", description="The skeleton prompt for OpenAI")
    target_group: str = Field("", description="The intended target group for the corresponding product")
    max_tokens: Optional[int] = Field(50, description="Max tokens for OpenAI")
    image_url: str = Field("", description="Image for OpenAI")
    
    @property
    def client(self):
        return OpenAI(api_key=self.api_key)

    def get_response(self) -> str:
        response = self.client.chat.completions.create(
            temperature=self.temperature,
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{self.prompt}",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"{self.image_url}"},
                        },
                    ],
                }
            ],
        )

        print(response.choices[0])

    
    