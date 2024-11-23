"""
API routes and resources.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from marshmallow import Schema, fields as ma_fields, validate
from sqlalchemy import func, and_, or_, desc, asc, distinct
from datetime import datetime, UTC
from .models import db, CharacterModel, User, get_character_model, get_auth_models
from .auth import token_required, admin_required, generate_token, verify_token

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
    @auth_ns.response(400, 'Registration failed', auth_models['error_response'])
    def post(self):
        """Register a new user"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            role = data.get('role', 'user')  # Default role is 'user'

            if not username or not password:
                return {'message': 'Username and password are required', 'status': 400}, 400

            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return {'message': 'Username already exists', 'status': 400}, 400

            # Create new user
            user = User(
                username=username,
                role=role
            )
            user.set_password(password)  # This uses the method from your User model

            db.session.add(user)
            db.session.commit()

            return {'message': 'User registered successfully'}, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Registration failed: {str(e)}', 'status': 400}, 400


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('login')
    @auth_ns.expect(auth_models['login_input'])
    @auth_ns.response(200, 'Success', auth_models['token_response'])
    @auth_ns.response(401, 'Authentication failed', auth_models['error_response'])
    def post(self):
        """Login and receive JWT token"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return {'message': 'Username and password are required', 'status': 401}, 401

            # Debug print
            print(f"Login attempt for user: {username}")

            # Find user in database
            user = User.query.filter_by(username=username).first()

            if not user:
                print(f"User {username} not found in database")
                return {'message': 'Invalid credentials', 'status': 401}, 401

            # Debug print
            print(f"Found user: {user.username}, role: {user.role}")

            if not user.check_password(password):
                print(f"Invalid password for user: {username}")
                return {'message': 'Invalid credentials', 'status': 401}, 401

            # Generate token
            try:
                token = generate_token(username)
                return {
                    'token': token,
                    'type': 'Bearer',
                    'expires_in': 3600,  # 1 hour
                    'username': username,
                    'role': user.role
                }, 200
            except Exception as e:
                print(f"Token generation error: {str(e)}")
                return {'message': 'Error generating token', 'status': 500}, 500

        except Exception as e:
            print(f"Login error: {str(e)}")
            return {'message': f'Login failed: {str(e)}', 'status': 401}, 401


@characters_ns.route('/')
class CharacterList(Resource):
    @characters_ns.doc('list_characters',
                      params={
                          'skip': {'description': 'Number of characters to skip', 'type': 'integer', 'default': 0},
                          'limit': {'description': 'Maximum number of characters to return', 'type': 'integer', 'default': 20},
                          'house': {'description': 'Filter by house name (case-insensitive)', 'type': 'string'},
                          'name': {'description': 'Filter by character name (case-insensitive)', 'type': 'string'},
                          'role': {'description': 'Filter by character role (case-insensitive)', 'type': 'string'},
                          'age_more_than': {'description': 'Filter by minimum age', 'type': 'integer'},
                          'age_less_than': {'description': 'Filter by maximum age', 'type': 'integer'},
                          'sort_by': {'description': 'Field to sort by (name, age, house, role)', 'type': 'string'},
                          'sort_order': {'description': 'Sort order (asc or desc)', 'type': 'string', 'enum': ['asc', 'desc'], 'default': 'asc'}
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

            # Create new character
            new_character = CharacterModel(
                name=data['name'],
                house=data['house'],
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


@characters_ns.route('/<int:id>')
@characters_ns.param('id', 'Character identifier')
@characters_ns.response(404, 'Character not found', error_response)
class Character(Resource):
    @characters_ns.doc('get_character')
    @characters_ns.response(200, 'Success', character_model)
    def get(self, id):
        """Get a single character by ID."""
        try:
            character = CharacterModel.query.get_or_404(id)
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
            return {'message': f'Error retrieving character: {str(e)}'}, 500

    @characters_ns.doc('update_character')
    @characters_ns.expect(character_create_model)
    @characters_ns.response(200, 'Character updated successfully', character_model)
    @characters_ns.response(401, 'Authentication required')
    @token_required
    def put(self, id):
        """Update a character by ID (requires authentication)."""
        try:
            character = CharacterModel.query.get_or_404(id)
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
                return {'message': 'Validation failed', 'errors': errors}, 400

            # Update fields
            character.name = data['name']
            character.house = data['house']
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

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating character: {str(e)}'}, 500

    @characters_ns.doc('delete_character')
    @characters_ns.response(204, 'Character deleted')
    @characters_ns.response(401, 'Authentication required')
    @characters_ns.response(403, 'Admin privileges required')
    @admin_required
    def delete(self, id):
        """Delete a character by ID (requires admin privileges)."""
        try:
            character = CharacterModel.query.get_or_404(id)
            db.session.delete(character)
            db.session.commit()
            return '', 204

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting character: {str(e)}'}, 500



@characters_ns.route('/search')
class CharacterSearch(Resource):
    @characters_ns.doc('search_characters',
                      params={
                          'q': {'description': 'Search term', 'type': 'string'},
                          'fields': {'description': 'Fields to search (comma-separated)', 'type': 'string'},
                      })
    @characters_ns.response(200, 'Success', list_response)
    def get(self):
        """Advanced search with relevance scoring."""
        try:
            search_term = request.args.get('q', '').lower()
            fields = request.args.get('fields', 'name,house,role').split(',')

            if not search_term:
                return {'message': 'Search term is required'}, 400

            # Build dynamic search conditions
            conditions = []
            for field in fields:
                if hasattr(CharacterModel, field):
                    conditions.append(
                        func.lower(getattr(CharacterModel, field)).like(f'%{search_term}%')
                    )

            if not conditions:
                return {'message': 'No valid search fields specified'}, 400

            # Calculate relevance score
            relevance_score = None
            for condition in conditions:
                if relevance_score is None:
                    relevance_score = condition
                else:
                    relevance_score = relevance_score + condition

            # Execute search query with relevance scoring
            results = db.session.query(
                CharacterModel,
                relevance_score.label('relevance')
            ).filter(
                or_(*conditions)
            ).order_by(
                desc('relevance')
            ).all()

            return {
                'status': 'success',
                'metadata': {
                    'total_results': len(results),
                    'search_term': search_term,
                    'fields_searched': fields
                },
                'results': [{
                    'id': char.id,
                    'name': char.name,
                    'house': char.house,
                    'age': char.age,
                    'role': char.role,
                    'relevance': float(relevance),
                    'created_at': char.created_at.isoformat(),
                    'updated_at': char.updated_at.isoformat()
                } for char, relevance in results]
            }

        except Exception as e:
            return {'message': f'Error performing search: {str(e)}'}, 500