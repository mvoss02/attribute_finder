from pathlib import Path

import pandas as pd
from config import openai_config, response_config
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

    # Load full input data
    logger.info('Loading input data')
    data = pd.read_csv(input_path)
    data['response'] = pd.NA

    # Merge existing responses if available
    if output_path.exists():
        logger.info('Loading and merging existing responses')
        existing_data = pd.read_csv(output_path)
        data.loc[data.index.isin(existing_data.index), 'response'] = existing_data[
            'response'
        ]

    # Create explicit copy for processing
    if response_config.is_test_run:
        try:
            # Handle case where sample size > available data
            sample_size = min(response_config.number_of_test_cases, len(data))
            process_indices = data.sample(n=sample_size).index
            logger.info(f'Processing {sample_size} test samples')
        except ValueError as e:
            logger.error(f'Sampling error: {e}')
            process_indices = data.index
    else:
        process_indices = data.index
        logger.info(f'Processing all {len(process_indices)} samples')

    # Process rows without responses
    logger.info('Processing rows without responses')
    for idx in process_indices:
        if pd.isna(data.loc[idx, 'response']):
            row = data.loc[idx]
            data.loc[idx, 'response'] = get_response_if_empty(row)

    logger.info('Saving complete dataset')
    data.to_csv(output_path, index=False)


if __name__ == '__main__':
    run()
