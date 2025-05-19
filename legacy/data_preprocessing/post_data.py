import json
import polars as pl
from loguru import logger
import requests
from config import data_config
from pathlib import Path


def _parquet_to_json(parquet_file_path: str, json_file_path: str) -> None:
    logger.info(f'Loading parquet file: {parquet_file_path}')
    df = pl.read_parquet(parquet_file_path)

    if not data_config.is_color:
        df = df.select(['ArticleID', 'attribute_id', 'ids', 'response'])
        df = df.rename({'attribute_id': 'AttributeID', 'ids': 'identifier'})
    else:
        df = df.select(['ArticleColorID', 'response'])


    logger.info(f'Saving DataFrame to JSON file: {json_file_path}')
    df.write_json(json_file_path)

def post_articles_to_db(api_url: str, output_data_path: str = 'data/output_data') -> None:
    # Define the paths
    json_file_path = str(output_data_path) + '/articles_with_response.json'
    parquet_file_path = str(output_data_path) + '/articles_with_response.parquet'

    logger.info('Converting parquet file to JSON file')
    _parquet_to_json(parquet_file_path=parquet_file_path, 
                     json_file_path=json_file_path)
    
    # Read the JSON file
    logger.info('Reading JSON file for posting')
    with open(json_file_path, 'r') as f:
        json_data = json.load(f)

    # Set up headers
    headers = {
        'Content-Type': 'application/json'
    }

    if not data_config.is_color:
        for data_point in json_data:
            # Check if identifier is a string that looks like JSON
            if 'identifier' in data_point and isinstance(data_point['identifier'], str):
                try:
                    # Parse the string as JSON
                    data_point['identifier'] = json.loads(data_point['identifier'])
                except json.JSONDecodeError as e:
                    logger.error(f'Could not decode the identifier as JSON object. Error: {e}')
                    pass
            
            # Convert None values to empty strings or appropriate default values
            for key, value in data_point.items():
                if key == 'response' and value is None:
                    data_point[key] = "None"
                    logger.warning(f'Response is None for data point: {data_point}')
                elif key == 'identifier' and value is None:
                    data_point[key] = ["None"]
                    logger.warning(f'Identifier are None for data point: {data_point}')
                elif value is None:
                    data_point[key] = "None"
                    logger.warning(f'Key {key} is None for data point: {data_point}')
            
            # Post the data
            post_url = api_url + '/attributes_articles_mapped_unique'
            logger.info(f'Posting data to API: {post_url}')
            try:
                response = requests.post(url=post_url, json=data_point, headers=headers)
                response.raise_for_status()
                logger.success(f'Successfully posted data. Status code: {response.status_code}')
            except requests.exceptions.RequestException as e:
                logger.error(f'Error posting data (data point: {data_point}) to {post_url}: {e}')
                raise
    else:
        for data_point in json_data:
            # Check if response is a string that looks like JSON
            if 'response' in data_point and isinstance(data_point['response'], str):
                try:
                    # Parse the string as JSON
                    data_point['response'] = json.loads(data_point['response'])
                except json.JSONDecodeError as e:
                    logger.error(f'Could not decode the response as JSON object. Error: {e}')
                    pass
            
            # Convert None values to empty strings or appropriate default values
            for key, value in data_point.items():
                if key == 'response' and value is None:
                    data_point[key] = ["None"]
                    logger.warning(f'Response is None for data point: {data_point}')
                elif value is None:
                    data_point[key] = ["None"]
                    logger.warning(f'Key {key} is None for data point: {data_point}')
            
            # Post the data
            post_url = api_url + '/colors_articles_mapped_unique'
            logger.info(f'Posting data to API: {post_url}')
            try:
                response = requests.post(url=post_url, json=data_point, headers=headers)
                response.raise_for_status()
                logger.success(f'Successfully posted color data. Status code: {response.status_code}')
            except requests.exceptions.RequestException as e:
                logger.error(f'Error posting color data (data point: {data_point}) to {post_url}: {e}')
                raise


if __name__ == '__main__':
    logger.info('Getting articles from the data source (__main__ block)')

    # Using Path for platform-independent path handling
    output_data_path = (
        Path(__file__).parent.parent.parent / data_config.output_data_path
    )

    post_articles_to_db(api_url=data_config.api_url, output_data_path=output_data_path)