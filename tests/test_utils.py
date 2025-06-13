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


import pytest
from ftf_cli.utils import properties_to_lookup_tree, transform_properties_to_terraform


class TestPropertiesToLookupTree:
    """Test cases for properties_to_lookup_tree function."""

    def test_simple_object_properties(self):
        """Test with simple object properties."""
        properties = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "active": {"type": "boolean"}
            }
        }
        expected = {
            "out": {
                "name": {},
                "age": {},
                "active": {}
            }
        }
        assert properties_to_lookup_tree(properties) == expected

    def test_nested_object_properties(self):
        """Test with nested object properties."""
        properties = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"}
                            }
                        },
                        "settings": {
                            "type": "object",
                            "properties": {
                                "theme": {"type": "string"}
                            }
                        }
                    }
                },
                "metadata": {"type": "string"}
            }
        }
        expected = {
            "out": {
                "user": {
                    "profile": {
                        "name": {},
                        "email": {}
                    },
                    "settings": {
                        "theme": {}
                    }
                },
                "metadata": {}
            }
        }
        assert properties_to_lookup_tree(properties) == expected

    def test_array_properties(self):
        """Test with array properties - should simplify to empty objects."""
        properties = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }
        expected = {
            "out": {
                "tags": {},
                "users": {}
            }
        }
        assert properties_to_lookup_tree(properties) == expected

    def test_mixed_types(self):
        """Test with mixed property types."""
        properties = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "object",
                            "properties": {
                                "host": {"type": "string"},
                                "port": {"type": "number"},
                                "enabled": {"type": "boolean"}
                            }
                        },
                        "cache_servers": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "version": {"type": "string"},
                "features": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        expected = {
            "out": {
                "config": {
                    "database": {
                        "host": {},
                        "port": {},
                        "enabled": {}
                    },
                    "cache_servers": {}
                },
                "version": {},
                "features": {}
            }
        }
        assert properties_to_lookup_tree(properties) == expected

    def test_expected_attributes_interfaces_structure(self):
        """Test with the expected attributes/interfaces structure."""
        properties = {
            "type": "object",
            "properties": {
                "attributes": {
                    "type": "object",
                    "properties": {
                        "cluster_name": {"type": "string"},
                        "version": {"type": "string"},
                        "endpoint": {"type": "string"}
                    }
                },
                "interfaces": {
                    "type": "object",
                    "properties": {
                        "reader": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "host": {"type": "string"},
                                "port": {"type": "number"}
                            }
                        },
                        "writer": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "host": {"type": "string"},
                                "port": {"type": "number"}
                            }
                        }
                    }
                }
            }
        }
        expected = {
            "out": {
                "attributes": {
                    "cluster_name": {},
                    "version": {},
                    "endpoint": {}
                },
                "interfaces": {
                    "reader": {
                        "username": {},
                        "password": {},
                        "host": {},
                        "port": {}
                    },
                    "writer": {
                        "username": {},
                        "password": {},
                        "host": {},
                        "port": {}
                    }
                }
            }
        }
        assert properties_to_lookup_tree(properties) == expected

    def test_empty_object(self):
        """Test with empty object properties."""
        properties = {
            "type": "object",
            "properties": {}
        }
        expected = {"out": {}}
        assert properties_to_lookup_tree(properties) == expected

    def test_primitive_type_only(self):
        """Test with primitive type (should return empty structure)."""
        properties = {"type": "string"}
        expected = {"out": {}}
        assert properties_to_lookup_tree(properties) == expected

    def test_invalid_input_not_dict(self):
        """Test with invalid input - not a dictionary."""
        with pytest.raises(ValueError, match="Properties must be a dictionary"):
            properties_to_lookup_tree("invalid")

        with pytest.raises(ValueError, match="Properties must be a dictionary"):
            properties_to_lookup_tree(["list", "input"])

        with pytest.raises(ValueError, match="Properties must be a dictionary"):
            properties_to_lookup_tree(123)

    def test_invalid_nested_schema(self):
        """Test with invalid nested schema object."""
        properties = {
            "type": "object",
            "properties": {
                "invalid_field": "not_a_dict"
            }
        }
        with pytest.raises(ValueError, match="Schema object must be a dictionary"):
            properties_to_lookup_tree(properties)


class TestTransformPropertiesToTerraform:
    """Test cases for transform_properties_to_terraform function."""

    def test_simple_object(self):
        """Test transforming simple object properties to Terraform."""
        properties = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "active": {"type": "boolean"}
            }
        }
        result = transform_properties_to_terraform(properties)

        # Check that it's an object block
        assert result.startswith("object({")
        assert result.endswith("})")

        # Check that all fields are present
        assert "name = string" in result
        assert "age = number" in result
        assert "active = bool" in result

    def test_nested_object(self):
        """Test transforming nested object properties to Terraform."""
        properties = {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "number"}
                    }
                }
            }
        }
        result = transform_properties_to_terraform(properties)

        # Should contain nested object structure
        assert "config = object({" in result
        assert "host = string" in result
        assert "port = number" in result

    def test_array_types(self):
        """Test transforming array properties to Terraform."""
        properties = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "counts": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "simple_array": {
                    "type": "array"
                }
            }
        }
        result = transform_properties_to_terraform(properties)

        assert "tags = list(string)" in result
        assert "counts = list(number)" in result
        assert "simple_array = list(any)" in result

    def test_primitive_types(self):
        """Test all primitive type conversions."""
        # String type
        assert transform_properties_to_terraform({"type": "string"}) == "string"

        # Number type
        assert transform_properties_to_terraform({"type": "number"}) == "number"

        # Boolean type
        assert transform_properties_to_terraform({"type": "boolean"}) == "bool"

        # Unknown type
        assert transform_properties_to_terraform({"type": "unknown"}) == "any"

    def test_non_dict_input(self):
        """Test with non-dictionary input."""
        assert transform_properties_to_terraform("invalid") == "any"
        assert transform_properties_to_terraform(123) == "any"
        assert transform_properties_to_terraform(None) == "any"

    def test_indentation_levels(self):
        """Test that indentation is properly applied at different levels."""
        properties = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        result = transform_properties_to_terraform(properties, level=1)

        # Check indentation patterns (should have proper spacing)
        lines = result.split('\n')
        # Should have different indentation levels
        assert any('  level1 = object({' in line for line in lines)
        assert any('    level2 = object({' in line for line in lines)
        assert any('      field = string' in line for line in lines)
