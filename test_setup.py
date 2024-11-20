"""
Test the application setup.
"""
import os


def test_environment():
    """Verify the environment setup."""
    # Print current directory
    print("Current directory:", os.getcwd())

    # Check if app directory exists
    assert os.path.exists('app'), "app directory not found"

    # Check if essential files exist
    essential_files = [
        'app/__init__.py',
        'app/models.py',
        'app/routes.py',
        'app/utils.py',
        'run.py'
    ]

    for file in essential_files:
        assert os.path.exists(file), f"{file} not found"
        print(f"Found {file}")


if __name__ == '__main__':
    test_environment()