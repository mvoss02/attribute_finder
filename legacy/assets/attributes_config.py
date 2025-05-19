import json
import polars as pl
from typing import Dict, Optional, List


class AttributeParser:
    def __init__(self, json_file_path: str = None, json_data: str = None):
        """
        Initialize the AttributeParser with a file path to a JSON file or JSON string.
        
        Args:
            json_file_path: Path to a JSON file containing attribute data
            json_data: JSON string containing attribute data
        """
        if json_file_path:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        elif json_data:
            self.data = json.loads(json_data)
        else:
            raise ValueError("Either json_data or json_file_path must be provided")
        
        self.df = self._parse_to_dataframe()
        self.values_dict = self._extract_values_dict()
    
    def _parse_to_dataframe(self) -> pl.DataFrame:
        """
        Parse the JSON data into a Polars DataFrame, exploding categories.
        
        Returns:
            A Polars DataFrame with rows exploded by categories
        """
        rows = []
        
        for attribute_id, attribute_data in self.data.items():
            # Extract categories (Warengruppen)
            categories = attribute_data.get("Warengruppen", {})
            
            # Extract ids (Wertemengen)
            ids = attribute_data.get("Wertemengen", {})
            
            if categories:
                # Create a row for each category within the attribute
                for category_id, category_desc in categories.items():
                    row = {
                        "attribute_id": attribute_id,
                        "category_id": category_id,
                        "category_description": category_desc,
                        "attribute_description": attribute_data.get("Beschreibung", ""),
                        "attribute_orientation": attribute_data.get("Orientierung", ""),
                        "ids": json.dumps(list(ids.keys()) if ids else [])
                    }
                    rows.append(row)
            else:
                # If no categories, still create a row for the attribute
                row = {
                    "attribute_id": attribute_id,
                    "category_id": "",
                    "category_description": "",
                    "attribute_description": attribute_data.get("Beschreibung", ""),
                    "attribute_orientation": attribute_data.get("Orientierung", ""),
                    "ids": json.dumps(list(ids.keys()) if ids else [])
                }
                rows.append(row)
        
        # Create the DataFrame
        if rows:
            return pl.DataFrame(rows)
        else:
            # Return empty DataFrame with correct schema
            return pl.DataFrame(schema={
                "attribute_id": pl.Utf8,
                "category_id": pl.Utf8,
                "category_description": pl.Utf8,
                "attribute_description": pl.Utf8,
                "attribute_orientation": pl.Utf8,
                "ids": pl.Utf8
            })
    
    def _extract_values_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Extract a dictionary mapping attribute IDs to their Wertemengen values and descriptions.
        
        Returns:
            Dictionary with attribute IDs as keys and dictionaries of value-description pairs as values
        """
        values_dict = {}
        
        for attribute_id, attribute_data in self.data.items():
            if "Wertemengen" in attribute_data:
                values_dict[attribute_id] = attribute_data["Wertemengen"]
        
        return values_dict
    
    def get_dataframe(self) -> pl.DataFrame:
        """
        Get the Polars DataFrame representation of the attribute data.
        
        Returns:
            Polars DataFrame with the attribute data
        """
        return self.df
    
    def get_value_description(self, attribute_id: str, value: str) -> Optional[str]:
        """
        Get the description for a specific attribute value.
        
        Args:
            attribute_id: The ID of the attribute
            value: The value to get the description for
            
        Returns:
            The description string or None if not found
        """
        if attribute_id in self.values_dict and value in self.values_dict[attribute_id]:
            return self.values_dict[attribute_id][value]
        return None
    
    def get_all_value_descriptions(self, attribute_id: str) -> Dict[str, str]:
        """
        Get all value-description pairs for a specific attribute.
        
        Args:
            attribute_id: The ID of the attribute
            
        Returns:
            Dictionary mapping values to their descriptions
        """
        if attribute_id in self.values_dict:
            return self.values_dict[attribute_id]
        return {}
    
    def filter_by_category_id(self, category_id: str) -> pl.DataFrame:
        """
        Filter dataframe by a specific category ID.
        
        Args:
            category_id: The category ID to filter on
            
        Returns:
            Filtered DataFrame
        """
        return self.df.filter(pl.col("category_id") == category_id)
    
    def get_unique_attributes(self) -> List[str]:
        """
        Get a list of all unique attribute IDs.
        
        Returns:
            List of unique attribute IDs
        """
        return self.df["attribute_id"].unique().to_list()
    
    def get_unique_categories(self) -> List[str]:
        """
        Get a list of all unique category IDs.
        
        Returns:
            List of unique category IDs
        """
        return self.df["category_id"].unique().to_list()


# Example usage
if __name__ == "__main__":
    example_json = '''
    {
        "Leib/Hüfte": {
            "Warengruppen": {
                "11-02-01-14-0015": "D-Freizeithosen",
                "11-02-01-14-0020": "D-Jeans"
            },
            "Beschreibung": "Bezieht sich auf die Position des Bunds in Relation zur Taille des Trägers",
            "Orientierung": "Orientierungspunkt ist der Abstand zwischen dem Schritt und der Hüfte, oft hilft die Vorstellung wie eine Hose bei einem Model aussehen würde",
            "Wertemengen": {
                "niedrig": "Hosenbund liegt etwas unter dem Hüftknochen",
                "normal": "Hosenbund liegt etwa am Hüftknochen",
                "hoch": "Hosenbund liegt etwas über dem Hüftknochen"
            }
        },
        "Passform": {
            "Warengruppen": {
                "11-02-01-14-0015": "D-Freizeithosen",
                "11-02-01-14-0020": "D-Jeans"
            },
            "Beschreibung": "Bezieht sich auf die Art und Weise, wie die Hose entlang des Beins sitzt",
            "Orientierung": "Die Passform ist oft identifizierbar am Knöchelbereich",
            "Wertemengen": {
                "skinny": "Eng anliegend",
                "slim": "Eng anliegend, jedoch etwas größer geschnitten",
                "regular": "Weder eng anliegend noch locker",
                "loose": "Weit und locker liegend"
            }
        }
    }
    '''
    
    # Create parser and get DataFrame
    parser = AttributeParser(json_data=example_json)
    df = parser.get_dataframe()
    print("DataFrame with exploded categories:")
    print(df)
    
    # Filter by category
    print("\nFiltered by category ID '11-02-01-14-0015':")
    filtered_df = parser.filter_by_category_id("11-02-01-14-0015")
    print(filtered_df)
    
    # Get value description
    print("\nValue description for 'Passform', 'skinny':")
    desc = parser.get_value_description("Passform", "skinny")
    print(desc)