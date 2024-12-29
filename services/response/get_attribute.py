import base64
import json
import os
from typing import List, Optional

import llm
import pandas as pd
from config import response_config
from loguru import logger
from preprocess_images import download_and_process_image, write_failed_image
from pydantic import BaseModel


def get_response(
    product_id: int,
    supplier_colour: str,
    categories: Optional[List[str]],
    temperature: float = 0.0,
    product_category: str = '',
    brand: str = '',
    target_group: str = '',
    max_tokens: int = 50,
    image_url: str = '',
    is_color: bool = True,
) -> json:
    """
    Get response from the LLM API. It should pick the correct attribute of the given product.
    This happens based on a supplied list of categories, the product category, brand, target group and an image of the product.
    Several categories are tested, except of the colour. Colour will be assessed in another file.
    If is_color is set to True, the response will be for a colour (in terms of Hexcode).

    Args:
        product_id (int): The product ID corresponding to the URL.
        supplier_colour (str): The colour of the product as provided by the supplier.
        temperature (float, optional): The temperature to use for the response. Defaults to 0.0.
        categories (List[str], optional): A list of categories to use for the response. Defaults to [].
        product_category (str, optional): The product category to use for the response. Defaults to "".
        brand (str, optional): The brand to use for the response. Defaults to "".
        target_group (str, optional): The target group to use for the response. Defaults to "".
        max_tokens (int, optional): The maximum number of tokens to use for the response. Defaults to 50.
        image_url (str, optional): The URL of the image to use for the response. Defaults to "".
        is_color (bool, optional): Whether the response should be for a colour. Defaults to False.

    Returns:
        Optional[str]: The response from the LLM API.
    """

    client = llm.llm_client.get_client()

    # Defining a class which allows for the response of the LLM to be of JSON format
    class Response(BaseModel):
        response: str

    # Process image first
    processed_image_path = download_and_process_image(image_url)
    if not processed_image_path:
        logger.error(f'Failed to process image from URL: {image_url}')
        write_failed_image(product_id, supplier_colour, image_url)
        return None

    try:
        # Read the processed image
        with open(processed_image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # chat.completions.create
        response = client.beta.chat.completions.parse(
            temperature=temperature,
            model=llm.llm_client.model_name,
            max_tokens=max_tokens,
            messages=[
                {'role': 'system', 'content': response_config.system_prompt},
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': response_config.prompt_template.format(
                                categories=categories,
                                product_category=product_category,
                                brand=brand,
                                target_group=target_group,
                            )
                            if not is_color
                            else response_config.prompt_template_color.format(
                                product_category=product_category,
                                brand=brand,
                                target_group=target_group,
                            ),
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{base64_image}'
                            },
                        },
                    ],
                },
            ],
            response_format=Response,
        )

        logger.debug(is_color)
        logger.debug(
            response_config.prompt_template.format(
                categories=categories,
                product_category=product_category,
                brand=brand,
                target_group=target_group,
            )
            if not is_color
            else response_config.prompt_template_color.format(
                product_category=product_category,
                brand=brand,
                target_group=target_group,
            )
        )
        logger.debug(categories)

        try:
            json_response = json.loads(response.choices[0].message.content)
            return json_response['response']
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse JSON response: {e}')
            return response.choices[0].message.content
        except KeyError as e:
            logger.error(f'Response key not found in JSON: {e}')
            return response.choices[0].message.content

    except Exception as e:
        logger.error(f'API call failed: {str(e)}')
        return None

    finally:
        # Cleanup temporary file
        if processed_image_path and os.path.exists(processed_image_path):
            os.remove(processed_image_path)


if __name__ == '__main__':
    # Read in data
    data = pd.read_csv(
        '../../data/final_data/final_combined_data.csv', low_memory=False
    )

    # Pick n random observations
    random_sample = data.sample(n=3)

    for idx, row in random_sample.iterrows():
        result = get_response(
            product_id=row['LiefArtNr'],
            supplier_colour=row['LiefFarbe'],
            temperature=0.0,
            categories=row['Identifier'],
            product_category=row['WgrBez'],
            brand=row['Labelgruppe_norm'],
            target_group=row['Geschlecht'],
            image_url=row['Bild_URL_1'],
            is_color=True if row['Attribut Id'] == 'farbe' else False,
        )
        if result is None:
            logger.warning(f'Failed to process row {idx}')
