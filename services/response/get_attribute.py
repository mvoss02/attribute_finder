import base64
import io
import json
import os
import time
from pathlib import Path
from typing import List, Optional

import pandas as pd
import requests
from llm import llm_client
from loguru import logger
from PIL import Image
from pydantic import BaseModel

from config import response_config


def download_and_process_image(url: str, max_retries: int = 2) -> Optional[str]:
    """
    Download and process an image from a URL, with retry logic and validation.
    Returns the processed image URL or None if failed.

    Args:
        url (str): The URL of the image to download and process.
        max_retries (int, optional): The maximum number of retries. Defaults to 2.

    Returns:
        Optional[str]: The URL of the processed image or None if failed.
    """
    for attempt in range(max_retries):
        try:
            # Download image with timeout
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Load image and validate
            image = Image.open(io.BytesIO(response.content))

            # Convert to RGB if necessary (handles RGBA/other formats)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large (adjust size as needed)
            max_size = (500, 500)  # Example max size
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size)

            # Save to temp file
            temp_dir = Path('temp_images')
            temp_dir.mkdir(exist_ok=True)

            temp_path = temp_dir / f'processed_{int(time.time())}_{attempt}.jpg'
            image.save(temp_path, 'JPEG', quality=85)

            return str(temp_path)

        except requests.RequestException as e:
            logger.warning(f'Attempt {attempt + 1}/{max_retries} failed: {str(e)}')
            time.sleep(1)  # Wait before retry
        except Exception as e:
            logger.error(f'Image processing error: {str(e)}')
            return None

    return None


def get_response(
    categories: Optional[List[str]],
    temperature: float = 0.0,
    product_category: str = '',
    brand: str = '',
    target_group: str = '',
    max_tokens: int = 50,
    image_url: str = '',
    is_color: bool = False,
) -> json:
    """
    Get response from the LLM API. It should pick the correct attribute of the given product.
    This happens based on a supplied list of categories, the product category, brand, target group and an image of the product.
    Several categories are tested, except of the colour. Colour will be assessed in another file.
    If is_color is set to True, the response will be for a colour (in terms of Hexcode).

    Args:
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

    client = llm_client.get_client()

    # Defining a class which allows for the response of the LLM to be of JSON format
    class Response(BaseModel):
        response: str

    # Process image first
    processed_image_path = download_and_process_image(image_url)
    if not processed_image_path:
        logger.error(f'Failed to process image from URL: {image_url}')
        return None

    try:
        # Read the processed image
        with open(processed_image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # chat.completions.create
        response = client.beta.chat.completions.parse(
            temperature=temperature,
            model=llm_client.model_name,
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
                            if is_color
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

        logger.info(response.choices[0].message.content)
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
    data = pd.read_csv('../../data/final_data/final_combined_data.csv')

    # Pick n random observations
    random_sample = data.sample(n=3)

    for idx, row in random_sample.iterrows():
        result = get_response(
            temperature=0.0,
            categories=row['Identifier'],
            product_category=row['WgrBez'],
            brand=row['Labelgruppe_norm'],
            target_group=row['Geschlecht'],
            image_url=row['Bild_URL_1'],
            is_color=True if row['Identifier'] == 'farbe' else False,
        )
        if result is None:
            logger.warning(f'Failed to process row {idx}')
