from typing import Optional
import os
import json
import polars as pl
from loguru import logger
import requests
from pathlib import Path
from config import data_config
from assets.attributes_config import AttributeParser


def _merge_with_colors(articles: pl.DataFrame):
    # Add a column 'attributeId' to the df and set it to farbe
    articles = articles.with_columns(pl.lit('farbe').alias('attribute_id'))
    return articles

def _already_processed_articles_colors(api_url: str, articles: pl.DataFrame):
    logger.info('Requesting article + color combinations, that have been processed previously.')
    response = requests.get(api_url + f'/mapped_color_article_ids')

    if response.status_code == 200:
        logger.info('Unqiue ids have been successfully retrieved.')
        data = json.loads(response.text)

        if len(data) == 0:
            logger.info('Returning unfiltered articles, since unqiue list of article + color combinations is emtpy')
            return articles

        # Create a Polars DataFrame
        logger.info('Converting JSON object to Polars Dataframe')
        df_articles_color = pl.DataFrame(data, schema=["ArticleColorID"], orient="row")
        df_articles_color = df_articles_color.with_columns(
            pl.lit(1).alias("already_processed")
        )
        logger.info('df_articles_color has been successfully created')

        logger.info('Merging articles with combinations that have already been processed')
        articles = articles.join(other=df_articles_color, on=['ArticleColorID'], how='left')
        articles = articles.with_columns(pl.col("already_processed").fill_null(strategy="zero"))

        articles = articles.filter(pl.col('already_processed') != 1)

    else:
        logger.warning(f'Failed to get articles + attribute combinations from the API. Status code: {response.status_code}')
        logger.warning(f'Response object: {response.json()}')

    logger.info('Returning filtered articles')
    return articles

def _merge_with_attributes(articles: pl.DataFrame):
    logger.info('Getting the attributes')
    attribute_parser = AttributeParser(json_file_path=data_config.attributes_data_path)
    attributes = attribute_parser.get_dataframe()

    logger.info('Merging attributes with articles df')
    articles = articles.join(other=attributes, left_on=['WID'], right_on=['category_id'], how='left')

    logger.info('Succssesfully merged and eturning the articles with attributes')
    return articles

def _already_processed_articles_attributes(api_url: str, articles: pl.DataFrame):
    logger.info('Requesting article + attribute combinations, that have been processed previously.')
    response = requests.get(api_url + f'/mapped_attribute_article_ids')

    if response.status_code == 200:
        logger.info('Unqiue ids have been successfully retrieved.')
        data = json.loads(response.text)

        if len(data) == 0:
            logger.info('Returning unfiltered articles, since unqiue list of article + attribute combinations is emtpy')
            return articles

        # Create a Polars DataFrame
        logger.info('Converting JSON object to Polars Dataframe')
        df_articles_attributes = pl.DataFrame(data, schema=["ArticleID", "attribute"], orient="row")
        df_articles_attributes = df_articles_attributes.with_columns(
            pl.lit(1).alias("already_processed")
        )
        logger.info('df_articles_attributes has been successfully created')

        logger.info('Merging articles with combinations that have already been processed')

        articles = articles.join(other=df_articles_attributes, left_on=['ArticleID','attribute_id'], right_on=['ArticleID','attribute'], how='left')
        articles = articles.with_columns(pl.col("already_processed").fill_null(strategy="zero"))

        articles = articles.filter(pl.col('already_processed') != 1)

    else:
        logger.warning(f'Failed to get articles + attribute combinations from the API. Status code: {response.status_code}')
        logger.warning(f'Response object: {response.json()}')

    logger.info('Returning filtered articles')
    return articles

def _get_articles(api_url: str, raw_data_path: str = 'data/raw_data', number_of_articles: int = 5, local_data_path: Optional[str] = 'data/raw_data/articles.csv') -> None:
    # Swagger: http://srv-mfriebe-01:8000/docs

    if data_config.data_source == 'api':
        if not data_config.is_color:
            logger.info('Getting first the max offset for the regular attributes')
            response = requests.get(api_url + f'/articles_max_attribute_offset')
        else:
            logger.info('Getting first the max offset for color')
            response = requests.get(api_url + f'/articles_max_color_offset')

        if response.status_code == 200:
            # In case one wants to have a peek at the response
            #logger.debug(f'Response: {response.json()}')

            logger.info('Converting JSON resposne to int for max offset')
            data = json.loads(response.text)
            
            if data == None:
                logger.warning('Max offset returned None. Max_offset is set to 0!')
                max_offset = 0
            else:
                max_offset = int(data)

            logger.info(f'Current max_offset is equal to: {max_offset}')

            # In case one wants to have a peek at the data
            #test_articles = pl.read_parquet(raw_data_path + '/articles.parquet')
            #logger.debug(test_articles.head())
        else:
            logger.error(f'Failed to get max_offset. Status code: {response.status_code}')
            logger.error(f'Response object: {response.json()}') 
    
        # Getting data without! color attribute
        if not data_config.is_color:
            logger.info(f'Getting articles from the data source (endpoint: /articles_attributes/{number_of_articles}/{max_offset})')
            response = requests.get(api_url + f'/articles_attributes/{number_of_articles}/{max_offset}')

            logger.info(f'Status code: {response.status_code}')

            if response.status_code == 200:
                # In case one wants to have a peek at the response
                #logger.debug(f'Response: {response.json()}')

                logger.info('Converting response to DataFrame')
                data = json.loads(response.text)
                articles = pl.DataFrame(data)

                # In case one wants to have a peek at the data
                #test_articles = pl.read_parquet(raw_data_path + '/articles.parquet')
                #logger.debug(test_articles.head())
            else:
                logger.error(f'Failed to get articles. Status code: {response.status_code}')
                logger.error(f'Response object: {response.json()}')
        
        # Getting data solely for the color attribute
        else:
            logger.info(f'Getting articles from the data source (endpoint: /articles_colors/{number_of_articles}/{max_offset})')
            response = requests.get(api_url + f'/articles_colors/{number_of_articles}/{max_offset}')

            logger.info(f'Status code: {response.status_code}')

            if response.status_code == 200:
                # In case one wants to have a peek at the response
                #logger.debug(f'Response: {response.json()}')

                logger.info('Converting response to DataFrame')
                data = json.loads(response.text)
                articles = pl.DataFrame(data)

                # In case one wants to have a peek at the data
                #test_articles = pl.read_parquet(raw_data_path + '/articles.parquet')
                #logger.debug(test_articles.head())
            else:
                logger.error(f'Failed to get articles. Status code: {response.status_code}')
                logger.error(f'Response object: {response.json()}')
    else:
        if not os.path.exists(local_data_path):
            # In case the file does not exists, throw an error
            logger.error(f'Unfortunately, the file that has been supplied (path: {local_data_path}) does not exists. Please, check spelling and make sure the file exists.')
            raise FileNotFoundError('File not found.')
        
        logger.info(f'Getting articles from the local data source (path: {local_data_path})')
        articles = pl.read_csv(source=local_data_path)
    
    # If we do not want the color attribute, we merge the data with the attributes
    if not data_config.is_color:
        # Merging articles with attributes
        articles = _merge_with_attributes(articles=articles)

        # Check if article + attribute combination has already been processed
        logger.info('Merge articles with the article + attribute combinations which have already been processed')
        articles = _already_processed_articles_attributes(api_url=api_url, articles=articles)
    
    # Else we add just "farbe" as the attribute
    else:
        # Merging articles with colors
        articles = _merge_with_colors(articles=articles)

        # Check if article + color combination has already been processed
        logger.info('Merge articles with the article + color combinations which have already been processed')
        articles = _already_processed_articles_colors(api_url=api_url, articles=articles)


    # Saving articles
    logger.info('Saving filtered articles with attributes to parquet file')
    articles.write_parquet(str(raw_data_path) + '/articles.parquet')

def process_and_load_data(api_url: str,
                 raw_data_path: str = 'data/raw_data', 
                 number_of_articles: int = 5
                ) -> None:
    
    logger.info('Processing articles')
    _get_articles(api_url=api_url, raw_data_path=raw_data_path, number_of_articles=number_of_articles)
    logger.info('Data processing completed successfully')


if __name__ == '__main__':
    logger.info('Processing articles from the data source (__main__ block)')

    # Using Path for platform-independent path handling
    raw_data_path = (
        Path(__file__).parent.parent.parent / data_config.raw_data_path
    )
    local_data_path = (
        Path(__file__).parent.parent.parent / data_config.local_data_path
    )

    process_and_load_data(api_url=data_config.api_url,
                 raw_data_path=raw_data_path, 
                 number_of_articles=data_config.number_of_articles,
                 local_data_path=data_config.local_data_path if data_config.data_source == 'local' else None)
