# 🐉 Game of Thrones Character API

A RESTful API built with Flask-RESTX that manages Game of Thrones character data with SQLite database and JWT authentication.

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Server](#-running-the-server)
- [Authentication](#-authentication)
- [API Documentation](#-api-documentation)


## ✨ Features
- CRUD operations for characters
- JWT-based authentication and authorization
- SQLite database for data persistence
- Role-based access control (Admin/User)
- Pagination support
- Advanced filtering options
- Sorting capabilities
- Swagger UI documentation
- Input validation
- Case-insensitive search
- Database-level operations

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

4. Initialize the database
```bash
python scripts/init_db.py
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### Default Users
- Admin: username: `admin`, password: `admin123`
- User: username: `user`, password: `user123`

### Authentication Flow
1. Register a new user:
```http
POST /api/v1/auth/register
{
    "username": "your_username",
    "password": "your_password",
    "role": "user"  # or "admin"
}
```

2. Login to get JWT token:
```http
POST /api/v1/auth/login
{
    "username": "your_username",
    "password": "your_password"
}
```

3. Use the token in subsequent requests:
```http
Authorization: Bearer <your_token>
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

#### Authentication Endpoints

##### 1. Register User
```http
POST /api/v1/auth/register
```
Register a new user.

**Request Body:**
```json
{
    "username": "newuser",
    "password": "password123",
    "role": "user"
}
```

##### 2. Login
```http
POST /api/v1/auth/login
```
Login and receive JWT token.

**Request Body:**
```json
{
    "username": "newuser",
    "password": "password123"
}
```

#### Character Endpoints

##### 1. Get All Characters
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

##### 2. Get Single Character
```http
GET /api/v1/characters/{id}
```

##### 3. Create Character (Authenticated)
```http
POST /api/v1/characters/
```

##### 4. Update Character (Authenticated)
```http
PUT /api/v1/characters/{id}
```

##### 5. Delete Character (Admin Only)
```http
DELETE /api/v1/characters/{id}
```

## 🗄️ Project Structure
```
game-of-thrones-api/
│
├── .venv/                     # Virtual environment directory
│
├── app/                       # Main application package
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── config.py
│   └── auth.py
│
├── data/                     
│   ├── got_api.db        
│   └── characters.json       
│
├── tests/                     
│   ├── __init__.py           
│   ├── conftest.py           
│   ├── test__init__.py       
│   ├── test_crud.py          
│   ├── test_filters.py       
│   ├── test_models.py        
│   └── test_utils.py         
│
├── .gitignore                
├── directory-structure.md    
├── pytest.ini               
├── README.md                
└── requirements.txt
```        

## 🛠️ Technical Approach

1. **Architecture**
   - Flask-RESTX for API framework
   - SQLite for database
   - SQLAlchemy for ORM
   - JWT for authentication
   - Marshmallow for validation
   - Swagger UI for documentation

2. **Database Design**
   - Proper indexing on commonly queried fields
   - Database-level constraints
   - Efficient query optimization
   - Transaction management

3. **Security Features**
   - JWT token authentication
   - Password hashing
   - Role-based access control
   - Protected routes

## 🧪 Testing

This project includes comprehensive unit tests covering all endpoints and major functionality.

### Running Tests

Install test dependencies:
```bash
pip install -r requirements.txt
```

Run tests with coverage:
```bash
pytest --cov=app tests/
```

Generate HTML coverage report:
```bash
pytest --cov=app --cov-report=html tests/
```

The report will be available in the htmlcov directory.

### Test Structure

tests/conftest.py: Test fixtures and configuration
tests/test_crud.py: Tests for CRUD operations
tests/test_filters.py: Tests for filtering and sorting functionality
### Test Coverage

### Test Coverage
- ✅ Authentication flows
- ✅ All CRUD operations
- ✅ Database operations
- ✅ Input validation
- ✅ Error handling
- ✅ Authorization checks

### Running Specific Tests

Run specific test files:
```bash
pytest tests/test_crud.py
```

Run specific test function:
```bash
pytest tests/test_crud.py::test_create_character
```

Run with verbose output:
```bash
pytest -v tests/
```

## 👥 Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.