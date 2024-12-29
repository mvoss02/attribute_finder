from pathlib import Path

import pandas as pd
from config import openai_config
from get_attribute import get_response
from loguru import logger


def get_response_if_empty(row):
    """
    Check whether the resposnse has alread been ontained in a previous run.
    If not, get the response from the LLM API. Else skip the request. This
    saves time and resources.

    args:
        row: pd.Series

    returns:
        str: response
    """

    if pd.isna(row['response']):
        return get_response(
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
        )
    return row['response']


def run():
    logger.info('Hello from the attribute finder service!')
    output_path = Path('../../data/output_data/output_data.csv')
    input_path = Path('../../data/final_data/final_combined_data.csv')

    # Load or create output data
    if output_path.exists():
        logger.info('Loading existing output file')
        data = pd.read_csv(output_path)
    else:
        logger.info('Creating new output file from input data')
        data = pd.read_csv(input_path)
        data['response'] = pd.NA

    # TODO: Remove test case!
    data = data[:20]

    logger.info('Processing only rows without responses')
    data['response'] = data.apply(get_response_if_empty, axis=1)

    logger.info('Save the responses to the output file')
    data.to_csv(output_path, index=False)


if __name__ == '__main__':
    run()
