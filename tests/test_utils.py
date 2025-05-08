from ftf_cli.utils import generate_output_tree


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
