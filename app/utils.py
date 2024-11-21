"""
Helper functions for the application.
"""
import json
import os
from pathlib import Path
from typing import List, Dict

def get_data_file_path() -> Path:
    """Get the path to the characters.json file."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root / 'data' / 'characters.json'

def save_characters(characters: List[Dict]) -> None:
    """
    Save characters to JSON file.

    Args:
        characters (List[Dict]): List of character dictionaries to save
    """
    try:
        data_file = get_data_file_path()
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(characters, f, indent=4)
        print(f"Successfully saved {len(characters)} characters to file")
    except Exception as e:
        print(f"Error saving characters: {str(e)}")

def load_characters() -> List[Dict]:
    """
    Load character data from JSON file.

    Returns:
        List[Dict]: List of character dictionaries
    """
    try:
        data_file = get_data_file_path()
        print(f"Attempting to load file from: {data_file}")

        if not data_file.exists():
            print(f"Warning: {data_file} not found!")
            # Create sample data
            sample_data = [
                {
                    "id": 1,
                    "name": "Jon Snow",
                    "house": "Stark",
                    "age": 25,
                    "role": "Lord Commander of the Night's Watch"
                },
                {
                    "id": 2,
                    "name": "Daenerys Targaryen",
                    "house": "Targaryen",
                    "age": 24,
                    "role": "Queen of the Seven Kingdoms"
                },
                {
                    "id": 3,
                    "name": "Tyrion Lannister",
                    "house": "Lannister",
                    "age": 38,
                    "role": "Hand of the Queen"
                }
            ]

            # Ensure data directory exists
            data_dir = data_file.parent
            data_dir.mkdir(exist_ok=True)

            # Write sample data
            save_characters(sample_data)
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