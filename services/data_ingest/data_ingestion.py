from typing import List
import pandas as pd
from loguru import logger

def read_csv(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)

def merge_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, left_on: List[str], right_on: List[str], merge_how: str) -> pd.DataFrame:
    return pd.merge(df1, df2, left_on=left_on, right_on=right_on, how=merge_how)

def keep_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    return df[columns]

def save_data(df: pd.DataFrame, file_path: str) -> None:
    df.to_csv(file_path, index=False)


if __name__ == "__main__":
    from services.response.config import config
    
    logger.info("Reading data from input files")
    product_data = read_csv(config.product_file_path_input)
    attribute_data = read_csv(config.attribute_file_path_input)
    category_data = read_csv(config.category_file_path_input)
    
    logger.info("Remove unnecessary columns")
    product_data = keep_columns(product_data, config.product_columns)
    attribute_data = keep_columns(attribute_data, config.attribute_columns)
    category_data = keep_columns(category_data, config.category_columns)
    
    logger.info("Merging dataframes")
    attribute_data = merge_dataframes(attribute_data, category_data, left_on=['Katzuordnung'], right_on=['Kategorie'], merge_how='left')
    product_data = merge_dataframes(product_data, attribute_data, left_on=['WGR_norm', 'Kategorie'], right_on=['wgrNorm', 'Kategorie'], merge_how='left')
    
    logger.info("Saving final dataset")
    save_data(product_data, config.final_dataset_file_path)
    
    logger.info("Finished saving final dataset")