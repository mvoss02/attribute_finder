import pandas as pd
from config import openai_config
from get_attribute import get_response
from loguru import logger


def run():
    logger.info('Hello from the attribute finder service!')

    logger.info('Read in data from the input file')
    data = pd.read_csv('../../data/final_data/final_combined_data.csv')

    # TODO: Remove test case!
    data = data[20:25]

    logger.info('Iterate through the dataset and get attribute responses')
    data['response'] = data.apply(
        lambda row: get_response(
            product_id=row['LiefArtNr'],
            supplier_colour=row['LiefFarbe'],
            temperature=openai_config.temperature,
            categories=row['Identifier'],
            product_category=row['WgrBez'],
            brand=row['Labelgruppe_norm'],
            target_group=row['Geschlecht'],
            max_tokens=50,
            image_url=row['Bild_URL_1'],
            is_color=True if row['Attribut Id'] == 'farbe' else False,
        ),
        axis=1,
    )

    logger.info('Save the responses to the output file')
    data.to_csv('../../data/output_data/output_data.csv', index=False)


if __name__ == '__main__':
    run()
