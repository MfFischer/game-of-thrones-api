"""
API routes and resources.
"""
from flask import request
from flask_restx import Namespace, Resource, fields

from .models import CharacterSchema, get_character_model
from .utils import CHARACTERS

# Create namespace with detailed description
characters_ns = Namespace(
    'characters',
    description='Operations related to Game of Thrones characters'
)

# Create Swagger model
character_model = get_character_model(characters_ns)

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

        if house:
            filtered_chars = [
                char for char in filtered_chars
                if house in char['house'].lower()
            ]

        if name:
            filtered_chars = [
                char for char in filtered_chars
                if name in char['name'].lower()
            ]

        if role:
            filtered_chars = [
                char for char in filtered_chars
                if role in char['role'].lower()
            ]

        if age_more_than is not None:
            filtered_chars = [
                char for char in filtered_chars
                if char['age'] >= age_more_than
            ]

        if age_less_than is not None:
            filtered_chars = [
                char for char in filtered_chars
                if char['age'] <= age_less_than
            ]

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
    @characters_ns.expect(character_model)
    @characters_ns.response(201, 'Character created successfully', character_model)
    @characters_ns.response(400, 'Invalid input', error_response)
    def post(self):
        """
        Create a new character.

        Adds a new character to the database. All fields are required.
        """
        data = request.get_json()

        # Validate input data
        schema = CharacterSchema()
        errors = schema.validate(data)
        if errors:
            characters_ns.abort(400, errors=errors)

        # Add new character to list
        CHARACTERS.append(data)

        return data, 201


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

        Retrieves detailed information about a specific character.
        """
        character = next(
            (char for char in CHARACTERS if char['id'] == id),
            None
        )

        if not character:
            characters_ns.abort(404, message=f"Character {id} doesn't exist")

        return character

    @characters_ns.doc('update_character')
    @characters_ns.expect(character_model)
    @characters_ns.response(200, 'Character updated successfully', character_model)
    def put(self, id):
        """
        Update a character by ID.

        Updates all fields of an existing character.
        """
        data = request.get_json()

        # Validate input data
        schema = CharacterSchema()
        errors = schema.validate(data)
        if errors:
            characters_ns.abort(400, errors=errors)

        # Find character index
        char_idx = next(
            (idx for idx, char in enumerate(CHARACTERS) if char['id'] == id),
            None
        )

        if char_idx is None:
            characters_ns.abort(404, message=f"Character {id} doesn't exist")

        # Update character
        CHARACTERS[char_idx].update(data)
        return CHARACTERS[char_idx]

    @characters_ns.doc('delete_character')
    @characters_ns.response(204, 'Character deleted')
    def delete(self, id):
        """
        Delete a character by ID.

        Permanently removes a character from the database.
        """
        char_idx = next(
            (idx for idx, char in enumerate(CHARACTERS) if char['id'] == id),
            None
        )

        if char_idx is None:
            characters_ns.abort(404, message=f"Character {id} doesn't exist")

        CHARACTERS.pop(char_idx)
        return '', 204