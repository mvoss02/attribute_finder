import asyncio
import os

from loguru import logger

from response import get_attribute, preprocess_images
from config.config import data_config
from data_preprocessing import ftp_data_loader, json_article_loader, ftp_data_post
from helper import working_hours


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
            item.get("Identifier"): item.get("Bezeichner")
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


async def main(seconds_wait: str = 600, batch_size: int = 10):
    # Define a counter which keeps track of the number of tries outside of working hours
    tries_outside_working_hours = 0
    
    logger.info(f'Checking whether we are operating during work hours/days... This is try number: {tries_outside_working_hours}')
    
    while True:
        if working_hours.is_working_hours(timezone_str="Europe/Berlin"):
            # Set the number of tries outside of working hours back to 0
            tries_outside_working_hours = 0
            
            # Step 1: Load data from the API and merge with attributes (in batches)
            files_downloaded = ftp_data_loader.load_json_from_ftp(batch_size=batch_size)
            logger.info(f"Downloaded {files_downloaded} files in this batch")
                
            # Step 2: Create Article Reader Object and iterate over each article individually
            article_reader = json_article_loader.ArticleLoaderFromJson(json_dir_path=data_config.raw_data_path)
            
            logger.debug(f'Here are the files we read in: {article_reader.article_files}. Batch size set: {data_config.batch_size}.')
            
            # Get a list of the article filenames that have been found on the FTP-Server and iterate through them (if any present)
            number_of_idle_checks = 0 # Number of checks during work hours where no new data had been added
            
            list_article_filenames = article_reader.article_files
            if len(list_article_filenames) > 0:
                number_of_idle_checks = 0 # Back to 0
                
                for file_name in article_reader.article_files:
                    logger.info(f'This is article file: {file_name}')
                    
                    # Step 3: Read raw article data
                    logger.info("Getting article and attribute data")
                    article = article_reader.load_article_data(article_file_name=file_name)
                    # logger.debug(f"This is the current article: {article}")

                    # Step 4: Send full article dict to process each attribute and save as new JSON file
                    processed_article = await _process_article(article=article)  
                    
                    article_reader.save_article_as_json(file_path=data_config.output_data_path, article_file_name=file_name, processed_article=processed_article)

                    # Step 5: Posting data to "out" folder and delete data from "in" folder on FTP-Server
                    logger.info('Posting data to the FTP Server (to "out/" folder)')
                    ftp_data_post.post_json_to_ftp()
                    logger.info(f'Finished posting article (article id: {article["ProduktID"]}) to FTP ("out/" folder)')
                
                    logger.info('Deleting data from FTP Server (from "in/" folder)')
                    # TODO: Change ftp_data_post such that we have one connection where we can delete and post
                    logger.info(f'Finished deleting article (article id: {article["ProduktID"]}) from FTP ("in/" folder)')
                
                # Step 6: Delete article from ./data/in/ locally
                logger.info(f'Deleting all the json from {data_config.raw_data_path}')
                
                if not os.path.exists(data_config.raw_data_path):
                    logger.info(f"Directory '{data_config.raw_data_path}' does not exist")
                else:
                    for filename in os.listdir(data_config.raw_data_path):
                        file_path = os.path.join(data_config.raw_data_path, filename)
                        try:
                            if os.path.isfile(file_path):  # Ensure it's a file, not a subdirectory
                                os.remove(file_path)
                                logger.info(f"Deleted: {file_path}")
                        except Exception as e:
                            logger.info(f"Error deleting {file_path}: {e}")
                
                # Step 7: Delete article from ./data/out/ locally
                logger.info(f'Deleting all the json from {data_config.output_data_path}')
                
                if not os.path.exists(data_config.output_data_path):
                    logger.info(f"Directory '{data_config.output_data_path}' does not exist")
                else:
                    for filename in os.listdir(data_config.output_data_path):
                        file_path = os.path.join(data_config.output_data_path, filename)
                        try:
                            if os.path.isfile(file_path):  # Ensure it's a file, not a subdirectory
                                os.remove(file_path)
                                logger.info(f"Deleted: {file_path}")
                        except Exception as e:
                            logger.info(f"Error deleting {file_path}: {e}")
                
                logger.info(f'Done processing {len(article_reader.article_files)} articles')
                
                # Check if there might be more files to process
                if files_downloaded == batch_size:
                    logger.info(f"Processed full batch of {batch_size} files. There might be more files available.")
                else:
                    logger.info(f"Processed {files_downloaded} files (less than batch size). Likely processed all available files.")

            else: 
                number_of_idle_checks += 1 # Add to the number of tries without new data during working hours
                logger.warning(f'No article file paths were found at {data_config.raw_data_path}. This is check number {number_of_idle_checks} that resulted in no new data. Let us try in {seconds_wait * number_of_idle_checks} sec again!')
                await asyncio.sleep(seconds_wait) # Allows container to be considered idle
        else:
            tries_outside_working_hours += 1 # Add to the number of tries outside of working hours
            logger.warning(f"We are currently not operating during work hours... Let us try in {seconds_wait * tries_outside_working_hours} sec again!")
            await asyncio.sleep(seconds_wait * tries_outside_working_hours) # Allows container to be considered idle


if __name__ == "__main__":
    asyncio.run(main(batch_size=data_config.batch_size))  # Process X files at a time - can be changed under config
    