from typing import List

import pandas as pd
from loguru import logger

from src.config import data_config


def read_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def merge_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    left_on: List[str],
    right_on: List[str],
    merge_how: str,
) -> pd.DataFrame:
    return pd.merge(df1, df2, left_on=left_on, right_on=right_on, how=merge_how)


def keep_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    return df[columns]


def save_data(df: pd.DataFrame, file_path: str) -> None:
    df.to_csv(file_path, index=False)


def process_data() -> None:
    """
    Main function to process and merge all data.
    """
    logger.info('Reading data from input files')
    product_data = read_csv(data_config.product_file_path_input)
    attribute_data = read_csv(data_config.attribute_file_path_input)
    category_data = read_csv(data_config.category_file_path_input)

    logger.info('Remove unnecessary columns')
    product_data = keep_columns(product_data, data_config.product_columns)
    attribute_data = keep_columns(attribute_data, data_config.attribute_columns)
    category_data = keep_columns(category_data, data_config.category_columns)

    logger.info('Merging dataframes')
    attribute_data = merge_dataframes(
        attribute_data,
        category_data,
        left_on=['Katzuordnung'],
        right_on=['Kategorie'],
        merge_how='left',
    )
    product_data = merge_dataframes(
        product_data,
        attribute_data,
        left_on=['WGR_norm', 'Kategorie'],
        right_on=['wgrNorm', 'Kategorie'],
        merge_how='left',
    )

    # Aggregate values to list
    logger.info('Grouping the dataframe')
    grouped_data = (
        product_data.groupby(data_config.group_by_columns)[
            data_config.aggregation_column
        ]
        .agg(list)
        .reset_index()
    )

    logger.info('Saving final dataset')
    save_data(grouped_data, data_config.final_dataset_file_path)

    logger.info('Finished saving final datasets')


if __name__ == '__main__':
    process_data()
