# Game of Thrones API Directory Structure

```python
game-of-thrones-api/
│
├── .venv/                     # Virtual environment directory
│
├── app/                       # Main application package
│   ├── __init__.py           # Application factory
│   ├── models.py             # Data models and schemas
│   ├── routes.py             # API routes and resources
│   └── utils.py              # Utility functions
│
├── data/                      # Data storage
│   └── characters.json       # Characters data file
│
├── tests/                     # Test directory
│   ├── __init__.py           # Test package initialization
│   ├── conftest.py           # Test configurations and fixtures
│   ├── test__init__.py       # Tests for app initialization
│   ├── test_crud.py          # CRUD operation tests
│   ├── test_filters.py       # Filter operation tests
│   ├── test_models.py        # Model tests
│   └── test_utils.py         # Utility function tests
│
├── .gitignore                # Git ignore file
├── directory-structure.md    # This file
├── pytest.ini               # Pytest configuration
├── README.md                # Project documentation
└── requirements.txt         # Project dependencies