"""
Helper functions for the application.
"""

from typing import List, Dict
from app.models import db, CharacterModel

def get_default_characters() -> List[Dict]:
    """Return default character data for seeding the database."""
    return [
        {
            "name": "Jon Snow",
            "house": "Stark",
            "age": 25,
            "role": "Lord Commander of the Night's Watch"
        },
        {
            "name": "Daenerys Targaryen",
            "house": "Targaryen",
            "age": 24,
            "role": "Queen of the Seven Kingdoms"
        }
    ]

def seed_default_characters() -> None:
    """Seed the database with default characters if empty."""
    try:
        # Only seed if no characters exist
        if CharacterModel.query.count() == 0:
            default_chars = get_default_characters()

            for char_data in default_chars:
                character = CharacterModel(**char_data)
                db.session.add(character)

            db.session.commit()
            print(f"Successfully seeded {len(default_chars)} default characters")
        else:
            print("Database already contains characters, skipping default seeding")

    except Exception as e:
        db.session.rollback()
        print(f"Error seeding default characters: {str(e)}")

