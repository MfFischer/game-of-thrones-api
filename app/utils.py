"""
Helper functions for the application.
"""
import json
from pathlib import Path
from typing import List, Dict


def load_characters() -> List[Dict]:
    """
    Load character data from JSON file.
    """
    try:
        data_file = Path('data/characters.json')
        print(f"Current working directory: {Path.cwd()}")
        print(f"Attempting to load file from: {data_file.absolute()}")

        if not data_file.exists():
            print(f"Warning: {data_file.absolute()} not found!")
            # Create sample data if file doesn't exist
            sample_data = [
                {
                    "id": 1,
                    "name": "Jon Snow",
                    "house": "Stark",
                    "age": 25,
                    "role": "Lord Commander"
                },
                {
                    "id": 2,
                    "name": "Daenerys Targaryen",
                    "house": "Targaryen",
                    "age": 24,
                    "role": "Queen"
                }
            ]
            # Create data directory if it doesn't exist
            data_file.parent.mkdir(exist_ok=True)
            # Write sample data to file
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=4)
            print("Created sample data file")
            return sample_data

        with open(data_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"Successfully loaded {len(data)} characters")
            return data

    except Exception as e:
        print(f"Error loading characters: {str(e)}")
        return []


# Global variable to store characters
CHARACTERS = load_characters()