# 🐉 Game of Thrones Character API

A RESTful API built with Flask-RESTX that manages Game of Thrones character data. This API provides CRUD operations, filtering, sorting, and pagination capabilities.

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Server](#-running-the-server)
- [API Documentation](#-api-documentation)
- [Examples](#-examples)

## ✨ Features
- CRUD operations for characters
- Pagination support
- Advanced filtering options
- Sorting capabilities
- Swagger UI documentation
- Data persistence
- Input validation
- Case-insensitive search

## 🔧 Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Installation

1. Clone the repository
```bash
git clone https://github.com/MfFischer/game-of-thrones-api.git
cd game-of-thrones-api
```

2. Create and activate virtual environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

## 🏃‍♂️ Running the Server

1. Start the server
```bash
python run.py
```

2. Access the Swagger UI documentation at:
```
http://localhost:5000/docs
```

## 📚 API Documentation

### Endpoints

#### 1. List Characters
```http
GET /api/v1/characters/
```
Get a list of characters with filtering and pagination options.

**Query Parameters:**
- `skip` (int): Number of records to skip
- `limit` (int): Number of records to return
- `house` (string): Filter by house name
- `name` (string): Filter by character name
- `role` (string): Filter by character role
- `age_more_than` (int): Filter by minimum age
- `age_less_than` (int): Filter by maximum age
- `sort_by` (string): Field to sort by (name, age, house, role)
- `sort_order` (string): Sort direction (asc, desc)

**Example:**
```http
GET /api/v1/characters/?house=stark&age_more_than=18&sort_by=age&sort_order=desc
```

#### 2. Get Single Character
```http
GET /api/v1/characters/{id}
```
Get details of a specific character.

**Example:**
```http
GET /api/v1/characters/1
```

#### 3. Create Character
```http
POST /api/v1/characters/
```
Create a new character.

**Request Body:**
```json
{
  "name": "Jon Snow",
  "house": "Stark",
  "age": 17,
  "role": "Lord Commander "
}
```

#### 4. Update Character
```http
PUT /api/v1/characters/{id}
```
Update an existing character.

**Request Body:**
```json
{
  "name": "Jon Snow",
  "house": "Stark",
  "age": 17,
  "role": "Lord Commander"
}
```

#### 5. Delete Character
```http
DELETE /api/v1/characters/{id}
```
Delete a character by ID.

## 💡 Examples

### Filtering Characters
```http
# Get all Stark house members over 18
GET /api/v1/characters/?house=stark&age_more_than=18

# Search by name
GET /api/v1/characters/?name=jon%20snow

# Complex filtering
GET /api/v1/characters/?house=stark&age_more_than=18&age_less_than=30
```

### Sorting Characters
```http
# Sort by age descending
GET /api/v1/characters/?sort_by=age&sort_order=desc

# Sort by house name ascending
GET /api/v1/characters/?sort_by=house&sort_order=asc
```

### Pagination
```http
# Get first 10 characters
GET /api/v1/characters/?limit=10&skip=0

# Get next 10 characters
GET /api/v1/characters/?limit=10&skip=10
```

## 🗄️ Project Structure
```
game-of-thrones-api/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── utils.py
├── data/
│   └── characters.json
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## 🔐 Error Handling

The API uses standard HTTP response codes:
- `200`: Success
- `201`: Created
- `204`: No Content (successful deletion)
- `400`: Bad Request
- `404`: Not Found
- `500`: Server Error

Error responses include detailed messages:
```json
{
  "message": "Error description",
  "errors": {
    "field": ["specific error details"]
  }
}
```

## 🛠️ Technical Approach

1. **Architecture**
   - Flask-RESTX for API framework
   - Marshmallow for data validation
   - JSON file for data persistence
   - Swagger UI for documentation

2. **Design Decisions**
   - Auto-generated IDs for new characters
   - Case-insensitive searching
   - Normalized house names
   - Deduplication of results
   - Comprehensive error handling

## 👥 Contributing

Feel free to submit issues and pull requests.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.