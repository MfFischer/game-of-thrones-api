"""
API routes and resources.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from marshmallow import Schema, fields as ma_fields, validate

from .models import get_character_model
from .utils import CHARACTERS, save_characters

# Create namespace with detailed description
characters_ns = Namespace(
    'characters',
    description='Operations related to Game of Thrones characters'
)

def generate_new_id():
    """
    Generate a new unique ID for a character.

    Returns:
        int: New unique ID
    """
    if not CHARACTERS:
        return 1
    return max(char['id'] for char in CHARACTERS) + 1

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

def normalize_house_name(house: str) -> str:
    """
    Normalize house name by removing 'House' prefix and extra spaces.

    Args:
        house (str): House name to normalize

    Returns:
        str: Normalized house name
    """
    return house.lower().replace('house ', '').strip()

def sort_characters(characters, sort_field=None, sort_order='asc'):
    """
    Sort characters by specified field and order.

    Args:
        characters (list): List of character dictionaries
        sort_field (str): Field to sort by (name, age, house, role)
        sort_order (str): Sort order ('asc' or 'desc')

    Returns:
        list: Sorted list of characters
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

@characters_ns.route('/')
class CharacterList(Resource):
    """Resource for handling multiple characters."""

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
        Get list of characters with filtering, sorting, and pagination.

        Returns a paginated list of characters that can be filtered and sorted by various criteria.
        """
        # Get query parameters
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=20, type=int)

        # Filter parameters
        house = request.args.get('house', '').lower()
        name = request.args.get('name', '').lower()
        role = request.args.get('role', '').lower()
        age_more_than = request.args.get('age_more_than', type=int)
        age_less_than = request.args.get('age_less_than', type=int)

        # Sort parameters
        sort_by = request.args.get('sort_by', type=str)
        sort_order = request.args.get('sort_order', default='asc', type=str)

        # Validate sort parameters
        valid_sort_fields = ['name', 'age', 'house', 'role']
        valid_sort_orders = ['asc', 'desc']

        if sort_by and sort_by not in valid_sort_fields:
            characters_ns.abort(
                400,
                message=f"Invalid sort_by value. Must be one of: {', '.join(valid_sort_fields)}"
            )

        if sort_order.lower() not in valid_sort_orders:
            characters_ns.abort(
                400,
                message=f"Invalid sort_order value. Must be one of: {', '.join(valid_sort_orders)}"
            )

        # Apply filters
        filtered_chars = CHARACTERS.copy()

        if name:
            filtered_chars = [
                char for char in filtered_chars
                # Exact match (case-insensitive)
                if name == char['name'].lower()
            ]

        if house:
            # Normalize house names
            normalized_house = normalize_house_name(house)
            filtered_chars = [
                char for char in filtered_chars
                if normalized_house == normalize_house_name(char['house'])
            ]

        if role:
            filtered_chars = [
                char for char in filtered_chars
                # Exact match (case-insensitive)
                if role in char['role'].lower()
            ]

        if age_more_than is not None:
            filtered_chars = [
                char for char in filtered_chars
                if char['age'] > age_more_than
            ]

        if age_less_than is not None:
            filtered_chars = [
                char for char in filtered_chars
                if char['age'] < age_less_than
            ]

        # Remove duplicates based on all fields except ID
        def char_key(c):
            return (c['name'].lower(),
                   normalize_house_name(c['house']),
                   c['age'],
                   c['role'].lower())

        seen = set()
        unique_chars = []
        for char in filtered_chars:
            k = char_key(char)
            if k not in seen:
                seen.add(k)
                unique_chars.append(char)

        filtered_chars = unique_chars

        # Apply sorting
        sorted_chars = sort_characters(filtered_chars, sort_by, sort_order)

        # Apply pagination
        paginated_chars = sorted_chars[skip:skip + limit]

        return {
            'status': 'success',
            'metadata': {
                'total_records': len(CHARACTERS),
                'filtered_records': len(filtered_chars),
                'returned_records': len(paginated_chars),
                'skip': skip,
                'limit': limit
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
            'characters': paginated_chars
        }

    @characters_ns.doc('create_character')
    @characters_ns.expect(character_create_model)
    @characters_ns.response(201, 'Character created successfully', character_model)
    @characters_ns.response(400, 'Invalid input', error_response)
    def post(self):
        """
        Create a new character.

        Creates a new character with auto-generated ID. Required fields:
        - name (string)
        - house (string)
        - age (integer)
        - role (string)
        """
        data = request.get_json()

        # Create schema for validation without ID
        class CharacterCreateSchema(Schema):
            name = ma_fields.Str(required=True, validate=validate.Length(min=1))
            house = ma_fields.Str(required=True)
            age = ma_fields.Int(required=True, validate=validate.Range(min=0))
            role = ma_fields.Str(required=True)

        # Validate input data
        schema = CharacterCreateSchema()
        errors = schema.validate(data)
        if errors:
            characters_ns.abort(400, errors=errors)

        # Add auto-generated ID
        new_character = {
            'id': generate_new_id(),
            **data
        }

        CHARACTERS.append(new_character)

        try:
            save_characters(CHARACTERS)
        except Exception as e:
            print(f"Error saving character: {str(e)}")
            # Continue execution since character was added to memory

        return new_character, 201


@characters_ns.route('/<int:id>')
@characters_ns.param('id', 'Character identifier')
@characters_ns.response(404, 'Character not found', error_response)
class Character(Resource):
    """Resource for handling single character operations."""

    @characters_ns.doc('get_character')
    @characters_ns.response(200, 'Success', character_model)
    def get(self, id):
        """
        Get a single character by ID.

        Retrieves detailed information about a particular character.
        """
        character = next(
            (char for char in CHARACTERS if char['id'] == id),
            None
        )

        if not character:
            characters_ns.abort(404, message=f"Character {id} doesn't exist")

        return character

    @characters_ns.doc('update_character')
    @characters_ns.expect(character_create_model)
    @characters_ns.response(200, 'Character updated successfully', character_model)
    def put(self, id):
        """
        Update a character by ID.
        """
        data = request.get_json()

        # Create schema for validation without ID
        class CharacterCreateSchema(Schema):
            name = ma_fields.Str(required=True)
            house = ma_fields.Str(required=True)
            age = ma_fields.Int(required=True, validate=validate.Range(min=0))
            role = ma_fields.Str(required=True)

        # Validate input data
        schema = CharacterCreateSchema()
        errors = schema.validate(data)
        if errors:
            characters_ns.abort(400, errors=errors)

        # Normalize house name
        data['house'] = data['house'].replace('House ', '').strip()

        # Find character index
        char_idx = next(
            (idx for idx, char in enumerate(CHARACTERS) if char['id'] == id),
            None
        )

        if char_idx is None:
            characters_ns.abort(404, message=f"Character {id} doesn't exist")

        # Update character while preserving ID
        CHARACTERS[char_idx] = {
            'id': id,
            **data
        }

        # Save to file
        save_characters(CHARACTERS)

        return CHARACTERS[char_idx]

    @characters_ns.doc('delete_character')
    @characters_ns.response(204, 'Character deleted')
    def delete(self, id):
        """Delete a character by ID."""
        char_idx = next(
            (idx for idx, char in enumerate(CHARACTERS) if char['id'] == id),
            None
        )

        if char_idx is None:
            characters_ns.abort(404, message=f"Character {id} doesn't exist")

        try:
            CHARACTERS.pop(char_idx)
            save_characters(CHARACTERS)
        except Exception as e:
            print(f"Error saving after delete: {str(e)}")
            # Still return 204 as the delete was successful in memory

        return '', 204