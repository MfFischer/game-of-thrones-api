"""
Entry point for the Game of Thrones API application.
"""
import os
import sys

# Add the absolute path to Python path
project_root = r"C:\Users\User\PycharmProjects\game-of-thrones-api"
sys.path.insert(0, project_root)

try:
    from app import create_app

    app = create_app()

    if __name__ == '__main__':
        print("Starting Game of Thrones API...")
        print(f"Project root: {project_root}")
        print("\nAvailable routes:")
        print("- API Documentation: http://localhost:5000/docs")
        print("- API Health Check: http://localhost:5000/")
        print("- Characters Endpoint: http://localhost:5000/api/v1/characters/")

        app.run(debug=True)

except ImportError as e:
    print(f"\nError: {e}")
    print("\nDebug information:")
    print(f"Current directory: {os.getcwd()}")
    print("\nPython path:")
    for path in sys.path:
        print(f"- {path}")