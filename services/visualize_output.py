import io
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
from loguru import logger
from PIL import Image


def visualize_by_attribute(df, num_samples=4):
    base_dir = Path('../data/visuals')

    # Group by attribute
    grouped = df.groupby('Attribut Id')

    for attr_id, group in grouped:
        # Create attribute directory
        attr_dir = base_dir / attr_id
        attr_dir.mkdir(parents=True, exist_ok=True)

        # Sample products
        samples = group.sample(n=min(num_samples, len(group)))

        logger.info(f'Processing attribute {attr_id} with {len(samples)} samples')

        for _, row in samples.iterrows():
            try:
                # Create single figure
                plt.figure(figsize=(10, 12))

                # Add attribute info
                if attr_id == 'farbe':
                    plt.suptitle(f'Attribute: {attr_id}', fontsize=14, y=0.98)
                else:
                    options = group['Identifier'].unique()
                    plt.suptitle(
                        f"Attribute: {attr_id}\nOptions: {', '.join(options)}",
                        fontsize=14,
                        y=0.98,
                    )

                # Display image
                response = requests.get(row['Bild_URL_1'])
                img = Image.open(io.BytesIO(response.content))
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                plt.imshow(img)
                plt.axis('off')

                # Add metadata in two parts
                metadata_basic = (
                    f"Marke: {row['Labelgruppe_norm']} | "
                    f"Geschlecht: {row['Geschlecht']} | "
                    f"ID: {row['LiefArtNr']} | "
                    f"Farbe: {row['LiefFarbe']}\n"
                    f"Kategorie: {row['WgrBez']}"
                )

                llm_response = textwrap.fill(str(row['response']), width=60)

                plt.title(metadata_basic, loc='left', pad=20, fontsize=10)

                # Center the LLM response text below image
                plt.figtext(
                    0.5, 0.22, 'LLM Response:', fontsize=14, weight='bold', ha='center'
                )

                plt.figtext(0.5, 0.20, llm_response, fontsize=12, ha='center', va='top')

                # Make room for text below image
                plt.subplots_adjust(bottom=0.3)

                # Save individual file
                plt.savefig(
                    attr_dir / f'product_{row["LiefArtNr"]}.png', bbox_inches='tight'
                )
                plt.close()

            except Exception as e:
                print(f"Error processing product {row['LiefArtNr']}: {e}")


if __name__ == '__main__':
    # Read in data which has been processed by the response service
    response_data = pd.read_csv('../data/output_data/output_data.csv', low_memory=False)
    response_data = response_data.loc[~response_data['response'].isna()]

    visualize_by_attribute(response_data, num_samples=300)
