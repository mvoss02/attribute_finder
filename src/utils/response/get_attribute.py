import base64
import json
import os
from typing import List, Optional

import backoff
import openai
from loguru import logger
from pydantic import BaseModel

from config.config import openai_config, response_config
from utils.response.llm import llm_client
from utils.response.preprocess_images import (
    download_and_process_image,
    write_failed_image,
)


@backoff.on_exception(backoff.expo, openai.RateLimitError)
async def _call_llm(client, content: List, is_color: bool, temperature: float = 0.0, max_completion_tokens: int = 50,):
    # Defining a class which allows for the response of the LLM to be of JSON format
    class Response(BaseModel):
        response: str

    # Defining a class which allows for the response of the LLM to be of JSON format
    class ResponseColor(BaseModel):
        response: List[str]

    response = await client.beta.chat.completions.parse(
                temperature=temperature,
                model=llm_client.model_name,
                max_completion_tokens=max_completion_tokens,
                messages=[
                    {'role': 'system', 'content': response_config.system_prompt_attribute if not is_color else response_config.system_prompt_color},
                    {
                        'role': 'user',
                        'content': content
                    },
                ],
                response_format=Response if not is_color else ResponseColor,
            )

    return response

async def get_response(
    attribute_id: str,
    product_id: int,
    image_urls: List[str],
    attribute_description: str = None,
    attribute_orientation: str = None,
    product_category: str = '',
    target_group: str = '',
    supplier_colour: Optional[str] = None,
    possible_options: Optional[dict] = None
) -> json:
    """
    Get response from the LLM API. It should pick the correct attribute of the given product.
    This happens based on a supplied list of possible_options, the product category, brand, target group and an image of the product.
    Several possible_options are tested, except of the colour. Colour will be assessed in another file.
    If is_color is set to True, the response will be for a colour (in terms of Hexcode).

    Args:
        attribute_id (str): The attribute ID corresponding to the URL.
        product_id (int): The product ID corresponding to the URL.
        supplier_colour (str): The colour of the product as provided by the supplier.
        possible_options (List[str], optional): A list of possible_options to use for the response. Defaults to [].
        possible_options (dict, optional): A dictionary of the ids (Wertemengen) and the descriptions.
        product_category (str, optional): The product category to use for the response. Defaults to "".
        attribute_description (str, optional): A general description of the attribute itself.
        attribute_orientation (str, optional): Where the model should look in order to identify the attribute.
        target_group (str, optional): The target group to use for the response. Defaults to "".
        image_url (List[str]): The URL(s) of the image(s) to use for the response. Defaults to "".

    Returns:
        Optional[str]: The response from the LLM API.
    """

    client = llm_client.get_client()

    final_images = []
    for i, img in enumerate(image_urls):
        # Process image first
        processed_image_path = download_and_process_image(
            url=img, suffix=i, verify_certificate=response_config.verify_certificate
        )

        if not processed_image_path:
            logger.error(f'Failed to process image from URL: {img}')
            write_failed_image(product_id, supplier_colour, img)
        else:
            final_images.append(processed_image_path)

    if len(final_images) > 0:
        content = [{'type': 'text',
                    'text': response_config.prompt_template_attribute.format(
                                    attribute_id=attribute_id,
                                    attribute_description=attribute_description,
                                    attribute_orientation=attribute_orientation,
                                    possible_options=possible_options,
                                    product_category=product_category,
                                    target_group=target_group,
                    ) if attribute_id != 'farbe'
                    else response_config.prompt_template_color.format(
                        target_group=target_group,
                    ),
                    },]

        for img in final_images:
            try:
                # Read the processed image
                with open(img, 'rb') as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')

                # Append each image to the contents
                content.append(
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{base64_image}'
                        },
                    },
                )
            except Exception as e:
                logger.warning(f'Image could not be retireved (URL: {img}). Error: {e}')

        try:
            logger.info(
                    f'Getting LLM Resposne from product {product_id} and attribute {attribute_id} with image {image_urls}'
                )

            response = await _call_llm(client=client, content=content, is_color=attribute_id == 'farbe', temperature=openai_config.temperature, max_completion_tokens=openai_config.max_completion_tokens)

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
            raise Exception(f'API call failed: {str(e)}')

        finally:
            # Clean up all saved image files
            for img_path in final_images:
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        logger.info(f'Removed temporary image file: {img_path}')
                except Exception as e:
                    logger.warning(f'Failed to delete temporary image file {img_path}: {e}')
    else:
        logger.error('None of the image paths worked!')
        return None


if __name__ == '__main__':
    logger.info('Starting LLM response directly from __main__ in the source file')

    import time

    start_time = time.time()

    #TODO: Implement color article

    #logger.debug(f'Test result colour for product_id 80416852: {test_result_colour}')

    #TODO: Implement other attribute than color article

    #logger.debug(f'Test result for product_id 80416852: {test_result}')

    logger.info('--- %s seconds ---' % (time.time() - start_time))
