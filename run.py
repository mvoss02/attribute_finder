import asyncio
import os

from loguru import logger

from response import get_attribute, preprocess_images
from config.config import data_config
from data_preprocessing import ftp_data_loader, json_article_loader, ftp_data_post


async def _process_article(article: dict) -> dict:
    """
    Returns the LLMs response for each attribute for a given article (helper function).

    Args:
        article (dict): the dictionary conatianing all the article's information.

    Returns:
        article (dict): the dictionary conatianing all the article's information, plus the LLMs' responses.
    """
    product_id = article.get("ProduktID")
    farb_id = article.get("FarbID")
    image_urls = [
        url
        for url in [
            article.get("Hauptbild"),
            article.get("Freisteller Back"),
            article.get("Modellbild"),
        ]
        if url
    ]
    product_category = article.get("Klassifikation", [{}])[0]["Bezeichnung"]
    target_group = article.get("Geschlecht")
    supplier_color_id = article.get("FarbID", None)

    for attribut in article.get("Klassifikations-Attribute", []):
        logger.info(f"Analysing article: {product_id} and the corresponding attribute is: {attribut.get('Bezeichner')}")

        # Get possible values and the corrsponding descriptions to these values
        possible_outcomes_description = {
            item.get(["Identifier"]): item.get(["Bezeichner"])
            for item in attribut.get("Attributwerte")
        }

        # Check if at least one image url has been supplied
        if len(image_urls) != 0:
            # Replace the key for this specific attribute inplace
            attribut[
                "Ausgewaehlter Attributwert (Result)"
            ] = await get_attribute.get_response(
                attribute_id=attribut.get(
                    "Identifier"
                ),  # The specific attribute identifier (e.g. "kragenform")
                attribute_description=attribut.get(
                    "Bezeichner"
                ),  # The attribute's description - how is "kragenform" defined, in terms of fashion?
                attribute_orientation=attribut.get(
                    "Orientierung"
                ),  # The orientation - where should the AI look to find correct attibute?
                product_id=product_id,  # The proeduct id
                # The image urls - there can be 1-3 images being supplied to us by Novomind
                image_urls=image_urls,
                target_group=target_group,  # The target group - men, women, children
                # The short description of the product category (e.g. "D-Hosen / D-Freizeithosen")
                product_category=product_category,
                supplier_colour=farb_id
                if attribut.get("Identifier") == "farbe"
                else None,  # The supplier's color id - Is only supplid if we want to analyze the color
                possible_options=possible_outcomes_description
                if attribut.get("Identifier") != "farbe"
                else None,  # Dictioanry of attribute:description
            )
        else:
            preprocess_images.write_failed_image(
                product_id=product_id, supplier_colour=supplier_color_id, url=image_urls
            )
            logger.error(f"No image urls where supplied for the following product id: {product_id}")

        # Log any failed responses here if needed
        if (
            attribut["Ausgewaehlter Attributwert (Result)"] is None
            or attribut["Ausgewaehlter Attributwert (Result)"] == "None"
        ):
            logger.warning(f"Failed to process article: {product_id} and the corresponding attribute: {attribut.get('Identifier')}")

    return article


async def main():
    logger.debug("THIS IS A TEST FOR THE DOCKER CONTAINER!")
    
    # Step 1: Load data from the API and merge with attributes
    ftp_data_loader.load_json_from_ftp()
        
    # Step 2: Create Article Reader Object and iterate over each article individually
    article_reader = json_article_loader.ArticleLoaderFromJson(json_dir_path=data_config.raw_data_path)
    
    logger.debug(f'Here are the files we read in: {article_reader.article_files}')
    
    # list_article_filenames = article_reader.article_files
    # if len(list_article_filenames) > 0:
    #     for file_name in article_reader.article_files:
    #         logger.info(f'This is article file: {file_name}')
            
    #         # Step 3: Read raw article data
    #         logger.info("Getting article and attribute data")
    #         article = article_reader.load_article_data(article_file_name=file_name)
    #         # logger.debug(f"This is the current article: {article}")

    #         # Step 4: Send full article dict to process each attribute
    #         # _ = await _process_article(article=article)
    #         # TODO: Edit the json directly

    #         # Step 5: Posting data to FTP
    #         logger.info('Posting data to the FTP Server')
    #         ftp_data_post.post_json_to_ftp()
    #         logger.info(f"Finished posting article (article id: {article['ProduktID']}) to FTP")
        
    #     # Step 6: Delete artcile from ./data/
    #     logger.info(f'Deleting all the json from {data_config.raw_data_path}')
        
    #     if not os.path.exists(data_config.raw_data_path):
    #         logger.info(f"Directory '{data_config.raw_data_path}' does not exist")
    #     else:
    #         for filename in os.listdir(data_config.raw_data_path):
    #             file_path = os.path.join(data_config.raw_data_path, filename)
    #             try:
    #                 if os.path.isfile(file_path):  # Ensure it's a file, not a subdirectory
    #                     os.remove(file_path)
    #                     logger.info(f"Deleted: {file_path}")
    #             except Exception as e:
    #                 logger.info(f"Error deleting {file_path}: {e}")
        
    #     logger.info('Done processing articles')

    # else:
    #     logger.warning(f'No article file paths were found at {data_config.raw_data_path}')


if __name__ == "__main__":
    asyncio.run(main())
