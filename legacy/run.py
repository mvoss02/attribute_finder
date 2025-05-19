from loguru import logger
import polars as pl

from data_preprocessing import json
from response import get_attribute
from config import data_config
from assets.attributes_config import AttributeParser
import asyncio


def _combine_image_urls(df: pl.DataFrame):
    # Step 1: Select all columns starting with 'Bild_URL_'
    bild_url_cols = [col for col in df.columns if col.startswith("Bild_URL_")]

    # Step 2: Concatenate them into a single string column, skipping nulls
    df = df.with_columns([
        pl.concat_str([pl.col(c) for c in bild_url_cols], separator=",", ignore_nulls=True).alias("Bild_URL")
    ])

    return df


async def _process_row(row):
    # Get the Attibute Parser and the corresponding descriptions for each id (Wertemenge)
    attribute_parser = AttributeParser(json_file_path=data_config.attributes_data_path)

    # Process each row
    return await get_attribute.get_response(
        attribute_id= row['ArticleColorID'] if row['attribute_id'] == 'farbe' else row['attribute_id'],
        product_id=row['LID'],
        supplier_colour=row['LiefFarbe'] if row['attribute_id'] == 'farbe' else None,
        temperature=0.0,
        categories=row['ids'] if row['attribute_id'] != 'farbe' else None,
        categories_descriptions=attribute_parser.get_all_value_descriptions(row['attribute_id']) if row['attribute_id'] != 'farbe' else None,
        product_category=row['category_description'] if row['attribute_id'] != 'farbe' else None,
        attribute_description=row['attribute_description'] if row['attribute_id'] != 'farbe' else None,
        attribute_orientation=row['attribute_orientation'] if row['attribute_id'] != 'farbe' else None,
        brand=row['Marke'],
        target_group=row['Geschlecht'],
        image_url=row['Bild_URL'],
        is_color=data_config.is_color
    )

async def main():
    for i in range(data_config.number_of_runs):
        logger.info(f'This is run number: {i + 1}')
        # Load data from the API and merge with attributes
        data_loading.process_and_load_data(api_url=data_config.api_url,
                                    raw_data_path=data_config.raw_data_path, 
                                    number_of_articles=data_config.number_of_articles)

        # Get response from LLM
        logger.info("Getting article and attribute data")

        # Read the data
        articles = pl.read_parquet(data_config.raw_data_path + '/articles.parquet')

        # logger.debug(f'Final data columns: {articles.columns}')
        # logger.debug(f'Final data: {articles}')

        if articles.height == 0:
            logger.warning('It appears that all article + attribute combinations have been processed. We will not continue executing this run, since the articles df is empty!')
            break

        # Convert URL columns
        logger.info('Combining all image URLs')
        articles = _combine_image_urls(df=articles)

        # Convert Polars DataFrame to list of rows (dictionaries)
        rows = articles.to_dicts()

        # Call async _process_row for each row
        responses = await asyncio.gather(*[_process_row(row) for row in rows])

        # Add the responses as a new column to the original DataFrame
        articles_with_response = articles.with_columns([
            pl.Series(name="response", values=responses)
        ])

        # Log any failed responses here if needed
        def check_for_failure(row):
            if row['response'] is None:
                logger.warning(f'Failed to process row: {row}')

        # Apply the check for failures
        articles_with_response.with_columns([
            pl.struct(articles_with_response.columns).map_elements(lambda row: check_for_failure(row), return_dtype=None)
        ])

        # Save the responses to a parquet file
        articles_with_response.write_parquet(data_config.output_data_path + '/articles_with_response.parquet')

        logger.info(f"Finished processing all articles. Data has been saved to {data_config.output_data_path + '/articles_with_response.parquet'}")

        # Posting data to DB
        post_data.post_articles_to_db(api_url=data_config.api_url, output_data_path=data_config.output_data_path)

        logger.info("Finished posting data to DB")


if __name__ == '__main__':
    asyncio.run(main())