import io
import time
from pathlib import Path
from typing import Optional

import requests
from loguru import logger
from PIL import Image


def write_failed_image(product_id: int, supplier_colour: str, url: str) -> None:
    logger.info(f'Writing failed image url to the failed_images.txt file: {url}')
    failed_dir = Path('../../data/failed_images')
    failed_dir.mkdir(parents=True, exist_ok=True)

    failed_file = failed_dir / 'failed_images.txt'
    entry = f'{product_id},{supplier_colour},{url}\n'

    # Check if file exists and if entry is already present
    if failed_file.exists():
        with open(failed_file, 'r') as f:
            if entry in f.readlines():
                return

    # Append new entry
    with open(failed_file, 'a') as f:
        f.write(entry)


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

    logger.info(f'Downloading and processing image from URL: {url}')

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
