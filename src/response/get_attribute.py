import base64
import json
import os
from typing import List, Optional

from loguru import logger
from pydantic import BaseModel

from config import response_config
from response.instances import llm_client
from response.preprocess_images import (
    download_and_process_image,
    write_failed_image,
)


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

    client = llm_client.get_client()

    # Defining a class which allows for the response of the LLM to be of JSON format
    class Response(BaseModel):
        response: str

    # Process image first
    processed_image_path = download_and_process_image(
        image_url, verify_certificate=response_config.verify_certificate
    )
    if not processed_image_path:
        logger.error(f'Failed to process image from URL: {image_url}')
        write_failed_image(product_id, supplier_colour, image_url)
        return None

    try:
        # Read the processed image
        with open(processed_image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        logger.info(
            f'Getting LLM Resposne from product {product_id} with image {image_url}'
        )

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

        # Debugging
        # logger.debug(is_color)
        # logger.debug(
        #     response_config.prompt_template.format(
        #         categories=categories,
        #         product_category=product_category,
        #         brand=brand,
        #         target_group=target_group,
        #     )
        #     if not is_color
        #     else response_config.prompt_template_color.format(
        #         product_category=product_category,
        #         brand=brand,
        #         target_group=target_group,
        #     )
        # )
        # logger.debug(categories)

        try:
            json_response = json.loads(response.choices[0].message.content)

            logger.info(f'LLM Response: {json_response["response"]}')

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
    logger.info('Starting LLM response directly from __main__ in the source file')

    # Simple test cases for colour and other attribute
    test_result_colour = get_response(
        product_id=80416852,
        supplier_colour='8426 Nightshadow Blu',
        temperature=0.0,
        categories=[None],
        product_category='Damen / D-Jacken',
        brand='amberundjune',
        target_group='D',
        image_url='https://assets.bettybarclay.com/media/image/c491ec3dd5db9f9fc8b350b627aa74ee80416852-8426-f.jpg',
        is_color=True,
    )

    logger.debug(f'Test result colour for product_id 80416852: {test_result_colour}')

    # Simple test cases for colour and other attribute
    test_result = get_response(
        product_id=80416852,
        supplier_colour='8426 Nightshadow Blu',
        temperature=0.0,
        categories=[
            'turtleneck',
            'uBoot',
            'envelope',
            'troyer',
            'henley',
            'rollkragen',
            'kapuze',
            'rundhals',
            'karree',
            'volant',
            'aufliegend',
            'stehkragen',
            'vNeck',
            'schulterfrei',
            'rueckenausschnitt',
            'wasserfall',
            'offen',
            'reversekragen',
        ],
        product_category='Damen / D-Jacken',
        brand='amberundjune',
        target_group='D',
        image_url='https://assets.bettybarclay.com/media/image/c491ec3dd5db9f9fc8b350b627aa74ee80416852-8426-f.jpg',
        is_color=False,
    )

    logger.debug(f'Test result for product_id 80416852: {test_result}')
