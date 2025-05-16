from ftf_cli.utils import generate_output_tree
from ftf_cli.utils import generate_output_lookup_tree


def test_dict_input():
    """Test with a dictionary input."""
    input_data = {
        "key1": "value1",
        "key2": 123,
        "key3": {"nested_key1": True, "nested_key2": [1, 2, 3]},
    }
    expected_output = {
        "key1": {"type": "string"},
        "key2": {"type": "number"},
        "key3": {
            "nested_key1": {"type": "boolean"},
            "nested_key2": {"type": "array", "items": {"type": "number"}},
        },
    }
    assert generate_output_tree(input_data) == expected_output


def test_list_input():
    """Test with a list input."""
    input_data = [1, 2, 3]
    expected_output = {"type": "array", "items": {"type": "number"}}
    assert generate_output_tree(input_data) == expected_output


def test_empty_list():
    """Test with an empty list."""
    input_data = []
    expected_output = {"type": "array"}
    assert generate_output_tree(input_data) == expected_output


def test_boolean_input():
    """Test with a boolean input."""
    input_data = True
    expected_output = {"type": "boolean"}
    assert generate_output_tree(input_data) == expected_output


def test_number_input():
    """Test with a number input."""
    input_data = 42
    expected_output = {"type": "number"}
    assert generate_output_tree(input_data) == expected_output


def test_string_input():
    """Test with a string input."""
    input_data = "hello"
    expected_output = {"type": "string"}
    assert generate_output_tree(input_data) == expected_output


def test_unexpected_type():
    """Test with an unexpected type."""
    input_data = object()
    expected_output = {"type": "any"}
    assert generate_output_tree(input_data) == expected_output


# Tests for generate_output_lookup_tree

def test_lookup_tree_dict_input():
    """Test generate_output_lookup_tree with a dictionary input."""
    input_data = {
        "key1": "value1",
        "key2": 123,
        "key3": {"nested_key1": True, "nested_key2": [1, 2, 3]},
    }
    expected_output = {
        "key1": {},
        "key2": {},
        "key3": {
            "nested_key1": {},
            "nested_key2": {"type": "array", "items": {}},
        },
    }
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_empty_list():
    """Test generate_output_lookup_tree with an empty list."""
    input_data = []
    expected_output = {"type": "array"}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_boolean_input():
    """Test generate_output_lookup_tree with a boolean input."""
    input_data = True
    expected_output = {}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_number_input():
    """Test generate_output_lookup_tree with a number input."""
    input_data = 42
    expected_output = {}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_float_input():
    """Test generate_output_lookup_tree with a float input."""
    input_data = 3.14
    expected_output = {}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_string_input():
    """Test generate_output_lookup_tree with a string input."""
    input_data = "hello"
    expected_output = {}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_unexpected_type():
    """Test generate_output_lookup_tree with an unexpected type."""
    input_data = object()
    expected_output = {}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_nested_structures():
    """Test generate_output_lookup_tree with complex nested structures."""
    input_data = {
        "config": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "enabled": True,
            },
            "cache": {
                "servers": ["server1", "server2"],
                "timeout": 30.5,
            },
        },
        "metadata": "value",
    }
    expected_output = {
        "config": {
            "database": {
                "host": {},
                "port": {},
                "enabled": {},
            },
            "cache": {
                "servers": {"type": "array", "items": {}},
                "timeout": {},
            },
        },
        "metadata": {},
    }
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_list_with_dict_items():
    """Test generate_output_lookup_tree with a list containing dictionaries."""
    input_data = [{"name": "item1", "value": 100}, {"name": "item2", "value": 200}]
    expected_output = {"type": "array", "items": {"name": {}, "value": {}}}
    assert generate_output_lookup_tree(input_data) == expected_output


def test_lookup_tree_mixed_nested_lists():
    """Test generate_output_lookup_tree with mixed nested lists and objects."""
    input_data = {
        "items": [
            {
                "config": {"enabled": True, "count": 5},
                "tags": ["tag1", "tag2"],
            }
        ],
        "simple_list": [1, 2, 3],
    }
    expected_output = {
        "items": {
            "type": "array",
            "items": {
                "config": {"enabled": {}, "count": {}},
                "tags": {"type": "array", "items": {}},
            },
        },
        "simple_list": {"type": "array", "items": {}},
    }
    assert generate_output_lookup_tree(input_data) == expected_output
