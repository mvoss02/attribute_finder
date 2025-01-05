from pathlib import Path

import pandas as pd
from loguru import logger

from response.get_attribute import get_response


def main():
    # Using Path for platform-independent path handling
    data_path = (
        Path(__file__).parent.parent.parent
        / 'data'
        / 'final_data'
        / 'final_combined_data.csv'
    )

    # Read in data
    data = pd.read_csv(data_path, low_memory=False)

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


if __name__ == '__main__':
    main()
