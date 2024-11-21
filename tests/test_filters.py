"""
Test filtering, sorting, and pagination functionality for characters API.
"""
import json
import pytest

class TestFiltering:
    """Tests for filtering functionality."""

    def test_house_filtering(self, client, mock_characters, mocker):
        """Test house name filtering with various cases."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        test_cases = [
            ('stark', 1),  # lowercase
            ('STARK', 1),  # uppercase
            ('House Stark', 1),  # with prefix
            ('nonexistent', 0)  # no matches
        ]

        for house, expected_count in test_cases:
            response = client.get(f'/api/v1/characters/?house={house}')
            data = json.loads(response.data)

            assert response.status_code == 200
            assert len(data['characters']) == expected_count
            if expected_count > 0:
                assert data['characters'][0]['house'].lower().replace('house ', '').strip() == 'stark'

    def test_age_filtering(self, client, mock_characters, mocker):
        """Test age range filtering."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        test_cases = [
            ('age_more_than=24', 1, lambda x: x > 24),
            ('age_less_than=25', 1, lambda x: x < 25),
            ('age_more_than=23&age_less_than=26', 2, lambda x: 23 < x < 26)
        ]

        for params, expected_count, condition in test_cases:
            response = client.get(f'/api/v1/characters/?{params}')
            data = json.loads(response.data)

            assert response.status_code == 200
            assert len(data['characters']) == expected_count
            assert all(condition(char['age']) for char in data['characters'])

    def test_exact_matches(self, client, mocker):
        """Test exact matching for name and role."""
        characters = [
            {'id': 1, 'name': 'Jon Snow', 'house': 'Stark', 'age': 25, 'role': 'King'},
            {'id': 2, 'name': 'Jon Doe', 'house': 'Stark', 'age': 30, 'role': 'Knight'},
            {'id': 3, 'name': 'Daenerys', 'house': 'Targaryen', 'age': 25, 'role': 'Queen'}
        ]
        mocker.patch('app.routes.CHARACTERS', characters)

        # Test exact name match
        response = client.get('/api/v1/characters/?name=jon snow')
        data = json.loads(response.data)
        assert len(data['characters']) == 1
        assert data['characters'][0]['name'] == 'Jon Snow'

        # Test exact role match
        response = client.get('/api/v1/characters/?role=king')
        data = json.loads(response.data)
        assert len(data['characters']) == 1
        assert data['characters'][0]['role'] == 'King'

class TestSorting:
    """Tests for sorting functionality."""

    def test_sorting_orders(self, client, mock_characters, mocker):
        """Test ascending and descending sorting."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        # Test both directions for age sorting
        orders = {
            'asc': lambda x, y: x <= y,
            'desc': lambda x, y: x >= y
        }

        for order, comparator in orders.items():
            response = client.get(f'/api/v1/characters/?sort_by=age&sort_order={order}')
            data = json.loads(response.data)

            assert response.status_code == 200
            # Verify sorting order
            chars = data['characters']
            for i in range(len(chars)-1):
                assert comparator(chars[i]['age'], chars[i+1]['age'])

    def test_invalid_sort_parameters(self, client, mock_characters, mocker):
        """Test handling of invalid sort parameters."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        # Test invalid sort field
        response = client.get('/api/v1/characters/?sort_by=invalid_field')
        assert response.status_code == 400
        assert 'Invalid sort_by value' in json.loads(response.data)['message']

class TestPagination:
    """Tests for pagination functionality."""

    def test_pagination_parameters(self, client, mock_characters, mocker):
        """Test pagination with various parameters."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        # Test basic pagination
        response = client.get('/api/v1/characters/?limit=1&skip=1')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert len(data['characters']) == 1
        assert data['metadata']['skip'] == 1
        assert data['metadata']['limit'] == 1
        assert data['characters'][0]['name'] == 'Daenerys Targaryen'

class TestCombinedOperations:
    """Tests for combining multiple operations."""

    def test_filter_with_sort(self, client, mock_characters, mocker):
        """Test combining filters with sorting."""
        mocker.patch('app.routes.CHARACTERS', mock_characters)

        response = client.get('/api/v1/characters/?age_more_than=20&sort_by=age&sort_order=desc')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert len(data['characters']) > 0
        # Verify descending age order
        chars = data['characters']
        for i in range(len(chars)-1):
            assert chars[i]['age'] >= chars[i+1]['age']
            assert chars[i]['age'] > 20