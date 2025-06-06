import json, os
from loguru import logger


class ArticleLoaderFromJson:
    def __init__(self, json_dir_path: str = None):
        """
        Initialize the article loader. Load a single article from the JSON. There is one JSON per article.
        
        Args:
            json_dir_path: Path to a JSON dir containing the articles
        """
        self.json_dir_path = json_dir_path
        
        # Step 1: Check if directory exists
        if os.path.isdir(json_dir_path):
            
            # Step 2: List all files in the directory (excluding subdirectories)
            self._article_files = [f for f in os.listdir(json_dir_path)
                if os.path.isfile(os.path.join(json_dir_path, f))]

            logger.info(f'Successfully imported article files from this path: {json_dir_path}')
        else:
            raise ValueError("The provided directory path does not exist!")
        
    def load_article_data(self, article_file_name: str) -> dict:
        """
        Load the json content of a specific article file.

        Args:
            article_file_name (str): Name of a specific article file (.json)
        """
        logger.info(f"Loading JSON content of this specific file: {article_file_name}")
        
        # Get full path - combination of dir path and article name
        full_path = os.path.join(self.json_dir_path, article_file_name)
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @property
    def article_files(self) -> list:
        return self._article_files
            