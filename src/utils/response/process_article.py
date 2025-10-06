from loguru import logger

from utils.response import get_attribute, preprocess_images


async def process_article(article: dict) -> dict:
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
        
        # TODO: Think of better logic here - currently only color attribute does not have possible outcomes when Hexcode is requested
        if attribut.get("Identifier", None) == "farbHex":
            possible_outcomes_description = None
        else:
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
                possible_options=possible_outcomes_description,  # Dictioanry of attribute:description
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
