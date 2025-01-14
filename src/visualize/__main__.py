from pathlib import Path

import pandas as pd
from loguru import logger

from visualize.visualize_output import visualize_by_attribute


def main():
    # Using Path for platform-independent path handling
    response_data_path = (
        Path(__file__).parent.parent.parent / 'data' / 'output_data' / 'output_data.csv'
    )

    logger.info(f'Save visualizations to output directory, path: {response_data_path}')

    # Read in data
    response_data = pd.read_csv(response_data_path, low_memory=False)

    # Filter out rows without responses
    response_data = response_data.loc[~response_data['response'].isna()]

    # Visualize a sample of products for each attribute in the dataset
    visualize_by_attribute(df=response_data, base_dir_str='data/visuals', num_samples=4)


if __name__ == '__main__':
    main()
