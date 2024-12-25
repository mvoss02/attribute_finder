from typing import List
from llm import llm_client
from loguru import logger
from config import response_config


def get_response(temperature: float = 0.0,
        categories: List[str] = [],
        product_category: str = "",
        brand: str = "",
        target_group: str = "",
        max_tokens: int = 50,
        image_url: str = ""
    ) -> str:
    
    response = llm_client.chat.completions.create(
        temperature=temperature,
        model=llm_client.model_name,
        max_tokens=max_tokens,
        messages=[
            {
                "role": "system", 
                "content": response_config.system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": response_config.prompt_template.format(
                            categories=categories,
                            product_category=product_category,
                            brand=brand,
                            target_group=target_group,
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"{image_url}"},
                    },
                ],
            }
        ],
    )
    
    logger.info(response.choices[0])
    
if __name__ == "__main__":
    examples = [
        {
            
            
        }
    ]
    
    for example in examples:
        get_response(**example)
    