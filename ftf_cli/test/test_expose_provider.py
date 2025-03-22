import os
import pytest
import yaml
from unittest.mock import patch, mock_open
from ftf_cli.commands.expose_provider import expose_provider, generate_output_lookup, deflatten_dict

@pytest.fixture
def mock_facets_yaml():
    return {
        "intent": "example-intent",
        "outputs": {
            "default": {
                "type": "@outputs/example-intent",
                "providers": {}
            }
        }
    }

@pytest.fixture
def mock_output_tf():
    return """
    output "example_output" {
        value = "${aws_s3_bucket.example_bucket}"
    }
    """

def test_generate_output_lookup(mocker, mock_output_tf):
    # Mock file operations
    mock_open_file = mocker.patch("builtins.open", mock_open(read_data=mock_output_tf))
    mocker.patch("os.path.exists", return_value=True)

    # Run the function
    output_tree = generate_output_lookup("mocked_path")

    # Assert output tree structure
    assert "example_output" in output_tree
    assert output_tree["example_output"]["type"] == "any"

def test_deflatten_dict():
    # Input flattened dictionary
    flattened_dict = {
        "key1": "value1",
        "key2.subkey1": "value2",
        "key2.subkey2": "value3"
    }

    # Run the function
    result = deflatten_dict(flattened_dict)

    # Assert deflattened structure
    assert result == {
        "key1": "value1",
        "key2": {
            "subkey1": "value2",
            "subkey2": "value3"
        }
    }