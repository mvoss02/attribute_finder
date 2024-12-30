import io
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
from PIL import Image

# Read in data which has been processed by the response service
response_data = pd.read_csv('../data/output_data/output_data.csv', low_memory=False)
response_data = response_data.loc[~response_data['response'].isna()]


def visualize_by_attribute(df, num_samples=4):
    # Group by attribute
    grouped = df.groupby('Attribut Id')

    for attr_id, group in grouped:
        try:
            # Add main title with options
            options = group['Identifier'].unique()

            if attr_id == 'farbe':
                plt.suptitle(f'Attribute: {attr_id}', fontsize=14, y=0.99)
            else:
                plt.suptitle(
                    f"Attribute: {attr_id}\n Options: {', '.join(options)}",
                    fontsize=14,
                    y=0.99,
                )

            # Select random samples
            samples = group.sample(n=min(num_samples, len(group)))

            for idx, (_, row) in enumerate(samples.iterrows(), 1):
                try:
                    # Create subplot
                    plt.subplot(num_samples, 1, idx)

                    # Download and display image
                    response = requests.get(row['Bild_URL_1'])
                    img = Image.open(io.BytesIO(response.content))
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    plt.imshow(img)
                    plt.axis('off')

                    # Add metadata
                    metadata = (
                        f"Marke: {row['Labelgruppe_norm']} | "
                        f"Geschlecht: {row['Geschlecht']} | "
                        f"LiefArtNr: {row['LiefArtNr']} | "
                        f"Farbe: {row['LiefFarbe']}\n"
                        f"WGR: {row['WgrBez']}\n"
                        f"Attribut (LLM): {textwrap.fill(str(row['response']), width=80)}"
                    )
                    plt.title(metadata, loc='left', pad=20, fontsize=10)

                except Exception as e:
                    print(f"Error processing image {row['LiefArtNr']}: {e}")

            plt.tight_layout(rect=[0, 0, 1, 0.98])

            # Save to attribute-specific file
            output_dir = Path('../data/visuals')
            output_dir.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_dir / f'samples_{attr_id}.png', bbox_inches='tight')
            plt.close()

        except Exception as e:
            print(f'Error processing attribute {attr_id}: {e}')


# Usage
visualize_by_attribute(response_data, num_samples=4)
