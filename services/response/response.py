from typing import List
from llm import llm_client
from loguru import logger


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
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Bitte gib das korrekte, zutreffende Attribut wieder.
                                Hier sind die möglichen Optionen, aus denen ausgewählt werden kann: {categories}.
                                Falls du nicht weisst welches Attribut wirklich zutrifft, gib bitte None zurück.
                                Es handelt sich hier bei um folgende Marke: {brand} und die Beschreibung der Kategorie
                                lautet: {product_category}. Die Target Group ist: {target_group}",
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
    get_response(temperature=0.0,)
    