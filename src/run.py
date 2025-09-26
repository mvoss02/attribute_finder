import asyncio
import signal

from loguru import logger

from config.config import data_config
from config.paths import data_path_in, data_path_out
from utils.data_preprocessing import ftp_data_loader, ftp_data_post, json_article_loader
from utils.helper import cleanup_files
from utils.response import process_article

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler():
    global shutdown_requested
    logger.info("Received shutdown signal, will finish current work and exit gracefully...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


async def main(seconds_wait: str = 600, batch_size: int = 10):
    global shutdown_requested

    while True and not shutdown_requested:
        # Step 1: Load data from the API and merge with attributes (in batches)
        files_downloaded = ftp_data_loader.load_json_from_ftp(batch_size=batch_size)
        logger.info(f"Downloaded {files_downloaded} files in this batch")

        # Step 2: Create Article Reader Object and iterate over each article individually
        article_reader = json_article_loader.ArticleLoaderFromJson(
            json_dir_path=data_path_out
        )

        logger.debug(f"Here are the files we read in: {article_reader.article_files}. Batch size set: {data_config.batch_size}.")

        # Get a list of the article filenames that have been found on the FTP-Server and iterate through them (if any present)
        # Number of checks during work hours where no new data had been added
        number_of_idle_checks = 0

        list_article_filenames = article_reader.article_files
        if len(list_article_filenames) > 0:
            number_of_idle_checks = 0  # Back to 0

            for file_name in article_reader.article_files:
                # Check for shutdown request before processing each article
                if shutdown_requested:
                    logger.info("Shutdown requested, stopping article processing")
                    break

                logger.info(f"This is article file: {file_name}")

                # Step 3: Read raw article data
                logger.info("Getting article and attribute data")
                article = article_reader.load_article_data(
                    article_file_name=file_name
                )
                # logger.debug(f"This is the current article: {article}")

                # Step 4: Send full article dict to process each attribute and save as new JSON file
                processed_article = await process_article.process_article(
                    article=article
                )

                article_reader.save_article_as_json(
                    file_path=data_path_in,
                    article_file_name=file_name,
                    processed_article=processed_article,
                )

            # Step 5: Posting data to "in" folder and delete data from "out" folder on FTP-Server
            # Initialize ftp handler
            ftp_data_poster = ftp_data_post.FTPDataPoster()

            # Posting json files to FTP-Server
            logger.info('Posting data to the FTP Server (to "in/" folder)')
            ftp_data_poster.post_json_to_ftp()
            logger.info(f'Finished posting article (article id: {article["ProduktID"]}) to FTP ("in/" folder)')

            # Only do cleanup and FTP operations if we weren't interrupted
            if not shutdown_requested:
                # Deleting files on FTP-Server, which have been fully processed
                logger.info('Deleting data from FTP Server (from "out/" folder)')
                ftp_data_poster.move_to_done(
                    files=article_reader.article_files
                )
                logger.info(f'Finished moving article (article id: {article["ProduktID"]}) from FTP ("out/" folder) to "out/done/" folder')
                
                # Step 6: Delete article from ./data/out/ locally
                cleanup_files.cleanup_files(
                    dir_path_to_delete=data_path_out
                )

                # Step 7: Delete article from ./data/in/ locally
                cleanup_files.cleanup_files(
                    dir_path_to_delete=data_path_in
                )

                logger.info(f"Done processing {len(article_reader.article_files)} articles")

                # Check if there might be more files to process
                if files_downloaded == batch_size:
                    logger.info(f"Processed full batch of {batch_size} files. There might be more files available.")
                else:
                    logger.info(f"Processed {files_downloaded} files (less than batch size). Likely processed all available files.")

        else:
            # Add to the number of tries without new data during working hours
            number_of_idle_checks += 1
            logger.warning(f"No article file paths were found at {data_path_in}. This is check number {number_of_idle_checks * number_of_idle_checks} that resulted in no new data. Let us try in {seconds_wait * number_of_idle_checks} sec again!")

            if number_of_idle_checks >= 10:
                break  # Exits while True loop -> program ends -> container stops

            # Allows container to be considered idle
            await asyncio.sleep(seconds_wait * number_of_idle_checks)

        # Check for shutdown request at the end of each main loop iteration
        if shutdown_requested:
            logger.info("Shutdown requested, exiting main loop")
            break

    logger.info("Program exiting...")


if __name__ == "__main__":
    # Process X files at a time - can be changed under config
    asyncio.run(main(batch_size=data_config.batch_size))
