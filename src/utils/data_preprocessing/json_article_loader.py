import json
import os

from loguru import logger


class ArticleLoaderFromJson:
    def __init__(self, json_dir_path: str = None):
        """
        Initialize the article loader. Load a single article from the JSON. There is one JSON per article.

        Args:
            json_dir_path: Path to a JSON dir containing the articles
        """
        self.json_dir_path = json_dir_path

        # Step 1: Check if directory exists, create if not
        if not os.path.isdir(json_dir_path):
            logger.info(f'Directory {json_dir_path} does not exist, creating it...')
            os.makedirs(json_dir_path, exist_ok=True)

        # Step 2: List all files in the directory
        self._article_files = [f for f in os.listdir(json_dir_path)
            if os.path.isfile(os.path.join(json_dir_path, f))]

        logger.info(f'Successfully imported article files from this path: {json_dir_path}')

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

    def save_article_as_json(self, file_path: str, article_file_name: str, processed_article: dict) -> None:
        """
        Save the processed article as json

        Args:
            file_path (str): the file path where the article should be stored
            article_file_name (str): the file name
            processed_article (dict): the dictioanry of the final article

        Returns:
            None
        """

        # Step 1: Check if directory exists, create if not
        if not os.path.isdir(file_path):
            logger.info(f'Directory {file_path} does not exist, creating it...')
            os.makedirs(file_path, exist_ok=True)

        # Step 2: Save article at teh given file_path
        with open(file_path / article_file_name, 'w', encoding='utf-8') as f:
            json.dump(processed_article, f, indent=2, ensure_ascii=False)

        logger.info(f'Successfully saved article at: "{file_path / article_file_name}"')

    @property
    def article_files(self) -> list:
        return self._article_files
