"""
API routes and resources.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from marshmallow import Schema, fields as ma_fields, validate
from sqlalchemy import func, and_, desc, asc
from datetime import datetime, UTC
from .models import (
    db,
    CharacterModel,
    User,
    get_character_model,
    get_auth_models
)
from .auth import token_required, admin_required, generate_token
from typing import Union, Tuple, Dict, Any, List
from sqlalchemy.exc import SQLAlchemyError

# Create namespaces
auth_ns = Namespace('auth', description='Authentication operations')
characters_ns = Namespace(
    'characters',
    description='Operations related to Game of Thrones characters'
)

# Get authentication models
auth_models = get_auth_models(auth_ns)

# Create Swagger models
character_model = get_character_model(characters_ns)

# Model for character creation (without ID)
character_create_model = characters_ns.model('CharacterCreate', {
    'name': fields.String(required=True, description='Character name'),
    'house': fields.String(required=True, description='House name'),
    'age': fields.Integer(required=True, description='Character age'),
    'role': fields.String(required=True, description='Character role')
})

# Create documentation models for responses
list_response = characters_ns.model('ListResponse', {
    'status': fields.String(description='Response status', example='success'),
    'metadata': fields.Raw(description='Response metadata including pagination info'),
    'filters_applied': fields.Raw(description='Active filters'),
    'sort_applied': fields.Raw(description='Active sorting'),
    'characters': fields.List(fields.Nested(character_model))
})

error_response = characters_ns.model('ErrorResponse', {
    'message': fields.String(description='Error message'),
    'errors': fields.Raw(description='Detailed error information')
})

def generate_new_id():
    """Generate a new unique ID for a character."""
    max_id = db.session.query(func.max(CharacterModel.id)).scalar()
    return 1 if max_id is None else max_id + 1

def normalize_house_name(house: str) -> str:
    """Normalize house name by removing 'House' prefix and extra spaces."""
    return house.lower().replace('house ', '').strip()

def sort_characters(characters, sort_field=None, sort_order='asc'):
    """
    Sort characters by specified field and order.

    Args:
        characters (list): List of character dictionaries
        sort_field (str): Field to sort by (name, age, house, role)
        sort_order (str): Sort order ('asc' or 'desc')
    """
    if not sort_field:
        return characters

    reverse = sort_order.lower() == 'desc'

    # Make sorting case-insensitive for string fields
    if sort_field in ['name', 'house', 'role']:
        return sorted(
            characters,
            key=lambda x: str(x.get(sort_field, '')).lower(),
            reverse=reverse
        )
    else:  # For numeric fields like age
        return sorted(
            characters,
            key=lambda x: x.get(sort_field, 0),
            reverse=reverse
        )


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc('register')
    @auth_ns.expect(auth_models['register_input'])
    @auth_ns.response(201, 'User registered successfully')
    @auth_ns.response(400, 'Bad Request', auth_models['error_response'])
    def post(self):
        """Register a new user"""
        try:
            # First check if content type is JSON
            if not request.is_json:
                return {'message': 'Content-Type must be application/json'}, 400

            # Then parse JSON data
            data = request.get_json()
            if data is None:  # This catches malformed JSON
                return {'message': 'Invalid JSON format'}, 400

            # Check for required fields
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return {'message': 'Username and password are required'}, 400

            # Check if user exists
            if User.query.filter_by(username=username).first():
                return {'message': 'Username already exists'}, 400

            # Create new user
            try:
                user = User(
                    username=username,
                    role=data.get('role', 'user')
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                return {'message': 'User registered successfully'}, 201

            except SQLAlchemyError as e:
                db.session.rollback()
                return {'message': 'Database error occurred', 'error': str(e)}, 500

        except Exception as e:
            return {'message': f'Registration failed: {str(e)}'}, 500


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login')
    @auth_ns.expect(auth_models['login_input'])
    @auth_ns.response(200, 'Success', auth_models['token_response'])
    @auth_ns.response(400, 'Bad Request', auth_models['error_response'])
    @auth_ns.response(401, 'Authentication failed', auth_models['error_response'])
    def post(self):
        """Login and receive JWT token"""
        try:
            # First check if content type is JSON
            if not request.is_json:
                return {'message': 'Content-Type must be application/json'}, 400

            # Then parse JSON data
            data = request.get_json()
            if data is None:  # This catches malformed JSON
                return {'message': 'Invalid JSON format'}, 400

            # Check for required fields
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return {'message': 'Username and password are required'}, 400

            # Find user in database
            user = User.query.filter_by(username=username).first()
            if not user:
                return {'message': 'Invalid credentials'}, 401

            # Verify password
            if not user.check_password(password):
                return {'message': 'Invalid credentials'}, 401

            # Generate token
            token = generate_token(username)
            return {
                'token': token,
                'type': 'Bearer',
                'expires_in': 3600,
                'username': username,
                'role': user.role
            }, 200

        except Exception as e:
            print(f"Login error: {str(e)}")
            return {'message': 'Internal server error'}, 500

@characters_ns.route('/')
class CharacterList(Resource):
    @characters_ns.doc('list_characters',
                      params={
                          'skip': {'description': 'Number of characters to skip', 'type': 'integer', 'default': 0},
                          'limit': {
                              'description': 'Maximum number of characters to return',
                              'type': 'integer',
                              'default': 20
                          },
                          'house': {'description': 'Filter by house name (case-insensitive)', 'type': 'string'},
                          'name': {'description': 'Filter by character name (case-insensitive)', 'type': 'string'},
                          'role': {'description': 'Filter by character role (case-insensitive)', 'type': 'string'},
                          'age_more_than': {'description': 'Filter by minimum age', 'type': 'integer'},
                          'age_less_than': {'description': 'Filter by maximum age', 'type': 'integer'},
                          'sort_by': {'description': 'Field to sort by (name, age, house, role)', 'type': 'string'},
                          'sort_order': {
                              'description': 'Sort order (asc or desc)',
                              'type': 'string', 'enum': ['asc', 'desc'],
                              'default': 'asc'
                          }
                      })
    @characters_ns.response(200, 'Success', list_response)
    def get(self):
        """
        Get list of characters with database-level filtering, sorting, and pagination.
        """
        try:
            # Get query parameters
            skip = request.args.get('skip', default=0, type=int)
            limit = request.args.get('limit', default=20, type=int)
            house = request.args.get('house', '').lower()
            name = request.args.get('name', '').lower()
            role = request.args.get('role', '').lower()
            age_more_than = request.args.get('age_more_than', type=int)
            age_less_than = request.args.get('age_less_than', type=int)
            sort_by = request.args.get('sort_by')
            sort_order = request.args.get('sort_order', default='asc')

            # If limit is 0, return all results
            if limit == 0:
                limit = None

            # Validate sort parameters
            valid_sort_fields = ['name', 'age', 'house', 'role']
            valid_sort_orders = ['asc', 'desc']

            if sort_by and sort_by not in valid_sort_fields:
                return {
                    'message': f"Invalid sort_by value. Must be one of: {', '.join(valid_sort_fields)}"
                }, 400

            if sort_order.lower() not in valid_sort_orders:
                return {
                    'message': f"Invalid sort_order value. Must be one of: {', '.join(valid_sort_orders)}"
                }, 400

            # Start with base query
            query = CharacterModel.query

            # Build filter conditions
            filters = []
            if house:
                filters.append(func.lower(CharacterModel.house).like(f'%{house}%'))
            if name:
                filters.append(func.lower(CharacterModel.name).like(f'%{name}%'))
            if role:
                filters.append(func.lower(CharacterModel.role).like(f'%{role}%'))
            if age_more_than is not None:
                filters.append(CharacterModel.age > age_more_than)
            if age_less_than is not None:
                filters.append(CharacterModel.age < age_less_than)

            # Apply filters
            if filters:
                query = query.filter(and_(*filters))

            # Get total count before pagination
            total_count = query.count()
            filtered_count = query.count()

            # Apply sorting
            if sort_by:
                sort_column = getattr(CharacterModel, sort_by)
                if sort_order == 'desc':
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))

            # Apply pagination
            if limit is not None:
                query = query.offset(skip).limit(limit)
            else:
                query = query.offset(skip)

            # Execute query
            characters = query.all()

            # Convert to dictionary format
            character_list = [{
                'id': char.id,
                'name': char.name,
                'house': char.house,
                'age': char.age,
                'role': char.role,
                'created_at': char.created_at.isoformat(),
                'updated_at': char.updated_at.isoformat()
            } for char in characters]

            return {
                'status': 'success',
                'metadata': {
                    'total_records': total_count,
                    'filtered_records': filtered_count,
                    'returned_records': len(character_list),
                    'skip': skip,
                    'limit': limit if limit is not None else 'all'
                },
                'filters_applied': {
                    'house': house if house else None,
                    'name': name if name else None,
                    'role': role if role else None,
                    'age_more_than': age_more_than,
                    'age_less_than': age_less_than
                },
                'sort_applied': {
                    'field': sort_by,
                    'order': sort_order
                },
                'characters': character_list
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }, 500

    @characters_ns.doc('create_character')
    @characters_ns.expect(character_create_model)
    @characters_ns.response(201, 'Character created successfully', character_model)
    @characters_ns.response(400, 'Invalid input', error_response)
    @characters_ns.response(401, 'Authentication required')
    @token_required
    def post(self):
        """Create a new character (requires authentication)."""
        try:
            data = request.get_json()

            # Create schema for validation
            class CharacterCreateSchema(Schema):
                name = ma_fields.Str(required=True, validate=validate.Length(min=1))
                house = ma_fields.Str(required=True)
                age = ma_fields.Int(required=True, validate=validate.Range(min=0))
                role = ma_fields.Str(required=True)

            # Validate input data
            schema = CharacterCreateSchema()
            errors = schema.validate(data)
            if errors:
                return {'message': 'Validation failed', 'errors': errors}, 400

            # Normalize the house name before creating the character
            normalized_house = normalize_house_name(data['house'])

            # Create new character with normalized house name
            new_character = CharacterModel(
                name=data['name'],
                # Capitalize the first letter of each word
                house=normalized_house.title(),
                age=data['age'],
                role=data['role'],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )

            db.session.add(new_character)
            db.session.commit()

            return {
                'id': new_character.id,
                'name': new_character.name,
                'house': new_character.house,
                'age': new_character.age,
                'role': new_character.role,
                'created_at': new_character.created_at.isoformat(),
                'updated_at': new_character.updated_at.isoformat()
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating character: {str(e)}'}, 500


@characters_ns.route('/<character_identifier>')
@characters_ns.param('character_identifier', 'Character ID or name')
@characters_ns.response(404, 'Character not found', error_response)
class Character(Resource):
    def _get_character_by_identifier(self, identifier: str) -> Union[CharacterModel, Tuple[Dict, int]]:
        """
        Helper method to get character by ID or name.
        """
        try:
            # Try to convert to integer for ID lookup
            char_id = int(identifier)
            character = CharacterModel.query.get(char_id)
            if character:
                return character
        except ValueError:
            # If conversion fails, search by name
            character = CharacterModel.query.filter(
                CharacterModel.name.ilike(f"%{identifier}%")
            ).first()
            if character:
                return character

            # Try exact name match if partial match fails
            character = CharacterModel.query.filter_by(name=identifier).first()
            if character:
                return character

        return {
            'message': 'Character not found',
            'detail': f"No character found with identifier '{identifier}'"
        }, 404

    @characters_ns.doc('get_character')
    @characters_ns.response(200, 'Success', character_model)
    def get(self, character_identifier):
        """
        Get a single character by ID or name.
        """
        try:
            result = self._get_character_by_identifier(character_identifier)
            if isinstance(result, tuple):
                return result

            character = result
            return {
                'id': character.id,
                'name': character.name,
                'house': character.house,
                'age': character.age,
                'role': character.role,
                'created_at': character.created_at.isoformat(),
                'updated_at': character.updated_at.isoformat()
            }
        except Exception as e:
            characters_ns.logger.error(f"Error retrieving character: {str(e)}")
            return {
                'message': 'Error retrieving character',
                'error': str(e)
            }, 500

    @characters_ns.doc('update_character')
    @characters_ns.expect(character_create_model)
    @characters_ns.response(200, 'Character updated successfully', character_model)
    @characters_ns.response(401, 'Authentication required')
    @token_required
    def put(self, character_identifier):
        """
        Update a character by ID or name (requires authentication).
        """
        try:
            result = self._get_character_by_identifier(character_identifier)
            if isinstance(result, tuple):
                return result

            character = result
            data = request.get_json()

            # Create schema for validation
            class CharacterCreateSchema(Schema):
                name = ma_fields.Str(required=True)
                house = ma_fields.Str(required=True)
                age = ma_fields.Int(required=True, validate=validate.Range(min=0))
                role = ma_fields.Str(required=True)

            # Validate input data
            schema = CharacterCreateSchema()
            errors = schema.validate(data)
            if errors:
                return {
                    'message': 'Validation failed',
                    'errors': errors
                }, 400

            # Normalize the house name before updating
            normalized_house = normalize_house_name(data['house'])

            # Update fields
            character.name = data['name']
            character.house = normalized_house.title()  # Capitalize first letter of each word
            character.age = data['age']
            character.role = data['role']
            character.updated_at = datetime.now(UTC)

            db.session.commit()

            return {
                'id': character.id,
                'name': character.name,
                'house': character.house,
                'age': character.age,
                'role': character.role,
                'created_at': character.created_at.isoformat(),
                'updated_at': character.updated_at.isoformat()
            }

        except SQLAlchemyError as e:
            db.session.rollback()
            characters_ns.logger.error(f"Database error updating character: {str(e)}")
            return {
                'message': 'Database error occurred',
                'error': str(e)
            }, 500
        except Exception as e:
            db.session.rollback()
            characters_ns.logger.error(f"Error updating character: {str(e)}")
            return {
                'message': 'Error updating character',
                'error': str(e)
            }, 500

    @characters_ns.doc('delete_character')
    @characters_ns.response(204, 'Character deleted')
    @characters_ns.response(401, 'Authentication required')
    @characters_ns.response(403, 'Admin privileges required')
    @characters_ns.response(404, 'Character not found')
    @admin_required
    def delete(self, character_identifier):
        """
        Delete a character by ID or name (requires admin privileges).
        """
        try:
            result = self._get_character_by_identifier(character_identifier)
            if isinstance(result, tuple):
                return result

            character = result

            # Store character info for response
            char_info = {
                'id': character.id,
                'name': character.name
            }

            # Delete the character
            db.session.delete(character)
            db.session.commit()

            # Return success message with deleted character info
            return {
                'message': 'Character deleted successfully',
                'deleted_character': char_info
            }, 200

        except SQLAlchemyError as e:
            db.session.rollback()
            characters_ns.logger.error(f"Database error deleting character: {str(e)}")
            return {
                'message': 'Database error occurred',
                'error': str(e)
            }, 500
        except Exception as e:
            db.session.rollback()
            characters_ns.logger.error(f"Error deleting character: {str(e)}")
            return {
                'message': 'Error deleting character',
                'error': str(e)
            }, 500


@characters_ns.route('/statistics')
class CharacterStatistics(Resource):
    """
    Character Statistics Resource.

    Provides endpoints to retrieve statistical information about characters,
    including demographics and distribution across houses and roles.
    """

    @characters_ns.doc('get_statistics')
    @characters_ns.response(200, 'Success')
    @characters_ns.response(500, 'Internal Server Error')
    def get(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive character statistics.

        Returns:
            dict: A dictionary containing three main statistical categories:
                - House statistics (member counts, age demographics)
                - Age distribution across all characters
                - Role distribution by house
        """
        try:
            return {
                'status': 'success',
                'statistics': {
                    'house_statistics': self._get_house_statistics(),
                    'age_distribution': self._get_age_distribution(),
                    'role_distribution': self._get_role_distribution()
                }
            }
        except Exception as e:
            # Log the error and return a generic error message
            characters_ns.logger.error(f"Error in get_statistics: {str(e)}")
            return {'status': 'error', 'message': 'Internal server error'}, 500

    def _get_house_statistics(self) -> List[Dict[str, Any]]:
        """
        Calculate statistical metrics for each house.

        Computes the following metrics per house:
        - Total member count
        - Average age of members
        - Age of youngest member
        - Age of oldest member
        """
        # Query database for house-specific statistics
        house_stats = db.session.query(
            CharacterModel.house,
            func.count(CharacterModel.id).label('member_count'),
            func.avg(CharacterModel.age).label('average_age'),
            func.min(CharacterModel.age).label('youngest'),
            func.max(CharacterModel.age).label('oldest')
        ).filter(
            # Exclude entries with no house assignment
            CharacterModel.house.isnot(None)
        ).group_by(
            CharacterModel.house
        ).all()

        # Format the statistics into a list of dictionaries
        return [{
            'house': stat.house,
            'member_count': stat.member_count,
            'average_age': round(float(stat.average_age or 0), 2),
            'youngest': stat.youngest,
            'oldest': stat.oldest
        } for stat in house_stats]

    def _get_age_distribution(self) -> List[Dict[str, Any]]:
        """
        Calculate the distribution of characters across age ranges.

        Age ranges are predefined as:
        - Under 20
        - 21-40
        - 41-60
        - Over 60
        """
        # Define age range boundaries and labels
        age_ranges = [
            (0, 20, 'Under 20'),
            (21, 40, '21-40'),
            (41, 60, '41-60'),
            (61, float('inf'), 'Over 60')
        ]

        distribution = []
        total_characters = CharacterModel.query.count()

        # Calculate distribution for each age range
        for min_age, max_age, label in age_ranges:
            # Build query with age filters
            query = CharacterModel.query.filter(
                CharacterModel.age.isnot(None),
                CharacterModel.age >= min_age
            )

            # Add upper bound for all ranges except the last one
            if max_age != float('inf'):
                query = query.filter(CharacterModel.age <= max_age)

            # Count characters in this range
            count = query.count()

            # Calculate percentage and round to 2 decimal places
            percentage = round((count / total_characters) * 100, 2) if total_characters > 0 else 0

            distribution.append({
                'range': label,
                'count': count,
                'percentage': percentage
            })

        return distribution

    def _get_role_distribution(self) -> List[Dict[str, Any]]:
        """
        Calculate the distribution of roles within each house.
        """
        # Query database for role distribution statistics
        role_stats = db.session.query(
            CharacterModel.house,
            CharacterModel.role,
            func.count(CharacterModel.id).label('count')
        ).filter(
            # Exclude entries with no role or house
            CharacterModel.role.isnot(None),
            CharacterModel.house.isnot(None)
        ).group_by(
            CharacterModel.house,
            CharacterModel.role
        ).order_by(
            CharacterModel.house,
            desc('count')  # Sort by count in descending order
        ).all()

        # Format the statistics into a list of dictionaries
        return [{
            'house': stat.house,
            'role': stat.role,
            'count': stat.count
        } for stat in role_stats]