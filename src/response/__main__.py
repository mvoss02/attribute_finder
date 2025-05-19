from pathlib import Path

import polars as pl
from loguru import logger

from response.get_attribute import get_response
from config import response_config


def main():
    # Using Path for platform-independent path handling
    data_path = (
        Path(__file__).parent.parent.parent
        / 'data'
        / 'final_data'
        / 'final_combined_data.csv'
    )

    # Read in data
    data = pl.read_parquet(data_path)

    # Pick n random observations if test case specified
    if response_config.is_test_run:
        random_sample = data.sample(n=response_config.number_of_test_cases)
    else:
        random_sample = data

    # Iterate through rows and get response
    for row in random_sample.iter_rows(named=True):
        result = get_response(
            product_id=row['LiefArtNr'],
            supplier_colour=row['LiefFarbe'] if row['Attribut Id'] == 'farbe' else None,
            temperature=0.0,
            categories=row['Identifier'],
            product_category=row['WgrBez'],
            brand=row['Labelgruppe_norm'],
            target_group=row['Geschlecht'],
            image_url=row['Bild_URL_1'],
            is_color=row['Attribut Id'] == 'farbe'
        )
        if result is None:
            logger.warning(f'Failed to process row')


if __name__ == '__main__':
    main()
