"""
Database seeding script.
"""
from app import create_app
from app.models import db, User, CharacterModel
from app.utils import seed_default_characters
from werkzeug.security import generate_password_hash

def seed_database():
    """Seed the database with initial data"""
    app = create_app()

    with app.app_context():
        try:
            # Create admin user
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    password_hash=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin)

            # Create test user
            if not User.query.filter_by(username='user').first():
                user = User(
                    username='user',
                    password_hash=generate_password_hash('user123'),
                    role='user'
                )
                db.session.add(user)

            # Commit users first
            db.session.commit()
            print("✅ Users seeded successfully!")

            # Seed default characters
            seed_default_characters()
            print("✅ Database seeding completed!")

        except Exception as e:
            print(f"❌ Error seeding database: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    seed_database()