from typing import Optional
import io, time
import requests
from pathlib import Path
from PIL import Image
from loguru import logger


def download_and_process_image(url: str, max_retries: int = 2) -> Optional[str]:
    """
    Download and process an image from a URL, with retry logic and validation.
    Returns the processed image URL or None if failed.
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
            temp_dir = Path("temp_images")
            temp_dir.mkdir(exist_ok=True)
            
            temp_path = temp_dir / f"processed_{int(time.time())}_{attempt}.jpg"
            image.save(temp_path, "JPEG", quality=85)
            
            return str(temp_path)
            
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            time.sleep(1)  # Wait before retry
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            return None
    
    return None


if __name__ == "__main__":
    # Example usage
    test_url = "https://assets.bettybarclay.com/media/image/c491ec3dd5db9f9fc8b350b627aa74ee80416852-8426-f.jpg"
    result = download_and_process_image(test_url)
    print(f"Processed image path: {result}")