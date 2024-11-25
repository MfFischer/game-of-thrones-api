#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database seeding script for Game of Thrones API.

This script initializes the database with:
- Default admin and regular user accounts
- Default character data
- Any other initial data required for the application

Usage:
    python seed_db.py
"""

import sys
from app import create_app
from app.models import db, User, CharacterModel
from app.utils import seed_default_characters
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError


def create_user(username: str, password: str, role: str) -> bool:
    """
    Create a new user if it doesn't exist.
    """
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        print(f"ℹ️ User '{username}' already exists, skipping...")
        return False

    # Create new user
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    print(f"✅ Created {role} user: {username}")
    return True


def seed_database():
    """
    Seed the database with initial data.

    This function performs the following:
    1. Creates admin and regular user accounts if they don't exist
    2. Seeds default character data using utility function
    3. Commits all changes or rolls back on error

    Raises:
        Exception: If there's an error during seeding process
    """
    # Create Flask application
    app = create_app()

    with app.app_context():
        try:
            print("\n🌱 Starting database seeding process...")

            # Track number of changes
            changes_made = False

            # Create admin user
            admin_created = create_user('admin', 'admin123', 'admin')

            # Create test user
            user_created = create_user('user', 'user123', 'user')

            # Commit user changes if any were made
            if admin_created or user_created:
                db.session.commit()
                print("✅ User seeding completed successfully!")
                changes_made = True
            else:
                print("ℹ️ No new users needed to be created")

            # Get initial character count
            initial_count = CharacterModel.query.count()

            # Seed default characters
            seed_default_characters()

            # Check if characters were added
            final_count = CharacterModel.query.count()
            if final_count > initial_count:
                print(f"✅ Added {final_count - initial_count} new characters")
                changes_made = True
            else:
                print("ℹ️ No new characters needed to be added")

            if changes_made:
                print("\n✨ Database seeding completed successfully!")
            else:
                print("\nℹ️ Database already contained all required data")

        except SQLAlchemyError as e:
            print(f"\n❌ Database error during seeding: {str(e)}")
            db.session.rollback()
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Unexpected error during seeding: {str(e)}")
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    try:
        seed_database()
    except KeyboardInterrupt:
        print("\n\n⚠️ Seeding process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)