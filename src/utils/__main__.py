from pathlib import Path

import pandas as pd

from utils.visualize_output import visualize_by_attribute


def main():
    # Using Path for platform-independent path handling
    data_path = (
        Path(__file__).parent.parent / 'data' / 'final_data' / 'final_combined_data.csv'
    )

    # Read in data
    data = pd.read_csv(data_path, low_memory=False)

    # Visualize a sample of products for each attribute in the dataset
    visualize_by_attribute(df=data, base_dir_str='output', num_samples=4)


if __name__ == '__main__':
    main()
