import pandas as pd
from loguru import logger
from services.response.response import get_response


def main():
    logger.info('Hello from the attribute finder service!')
    
    logger.info('Read in data from the input file')
    data = pd.read_csv('data/final_data/final_combined_data.csv')
    
    
    
    


if __name__ == "__main__":
    
    
    main()
