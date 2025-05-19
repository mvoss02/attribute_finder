from loguru import logger

from data_preprocessing import json_article_loader
from response import get_attribute
from config import data_config
import asyncio


async def _process_article(article: dict) -> dict:
    """
    Returns the LLMs response for each attribute for a given article (helper function).

    Args:
        article (dict): the dictionary conatianing all the article's information.

    Returns:
        article (dict): the dictionary conatianing all the article's information, plus the LLMs' responses.
    """
    product_id = article.get('ProduktID')
    farb_id = article.get('FarbID')
    image_urls = [url for url in [article['Hauptbild'], article.get('Freisteller Back')] if url]
    product_category = article.get('Klassifikation', [{}])[0]['Bezeichnung']
    target_group = article.get('Geschlecht')

    for attribut in article.get('Klassifikations-Attribute', []):
        logger.info(f"Analysing article: {product_id} and the corresponding attribute is: {attribut.get('Bezeichner')}")
        
        # Get possible values and the corrsponding descriptions to these values
        possible_outcomes_description = {item["Identifier"]: item["Bezeichner"] for item in attribut.get("Attributwerte")}

        # Replace the key for this specific attribute inplace
        attribut["Ausgewaehlter Attributwert (Result)"] = await get_attribute.get_response(
            attribute_id=attribut.get("Identifier"),
            attribute_description=attribut.get("Bezeichner"),
            product_id=product_id,
            image_urls=image_urls,
            target_group=target_group,
            product_category=product_category,
            supplier_colour=farb_id if attribut.get("Identifier") == "farbe" else None,
            possible_options=possible_outcomes_description if attribut.get("Identifier") != "farbe" else None,
        )
        
        # Log any failed responses here if needed
        if attribut["Ausgewaehlter Attributwert (Result)"] is None or attribut["Ausgewaehlter Attributwert (Result)"] == "None":
            logger.warning(f'Failed to process article: {product_id} and the corresponding attribute: {attribut.get("Identifier")}')
        
    return article


async def main():
    # Step 1: Load data from the API and merge with attributes
    # TODO: Implement data loading from FTP
        
    # Step 2: Create Article Reader Object and iterate over each article individually
    article_reader = json_article_loader.ArticleLoaderFromJson(json_dir_path=data_config.raw_data_path)
    
    for file_name in article_reader.article_files:
        logger.info(f'This is article file: {file_name}')
        
        # Step 3: Read raw article data
        logger.info("Getting article and attribute data")
        article = article_reader.load_article_data(article_file_name=file_name)
        # logger.debug(f"This is the current article: {article}")

        # Step 4: Send full article dict to process each attribute
        article_with_responses = await _process_article(article=article)

        # Step 5: Posting data to FTP
        # TODO: Implement sending data back to FTP
        # post_data.post_articles_to_db(api_url=data_config.api_url, output_data_path=data_config.output_data_path)

        logger.info(f"Finished posting article (article id: {article['ProduktID']}) to FTP")
    
    logger.info('Done processing articles')

if __name__ == '__main__':
    asyncio.run(main())