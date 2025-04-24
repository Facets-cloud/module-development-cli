import pytest
import click
from ftf_cli.utils import check_no_array_or_invalid_pattern_in_spec

def test_no_array_type_pass():
    spec = {
        "cpu": {"type": "number"},
        "memory": {"type": "number"}
    }
    # Should pass silently
    check_no_array_or_invalid_pattern_in_spec(spec)

def test_array_type_raises():
    spec = {
        "disks": {"type": "array"}
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_no_array_or_invalid_pattern_in_spec(spec)
    assert "Invalid array type found" in str(excinfo.value)

def test_pattern_properties_value_not_dict_raises():
    spec = {
        "some_field": {
            "patternProperties": {
                "^pattern$": "not_a_dict"
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_no_array_or_invalid_pattern_in_spec(spec)
    assert "patternProperties at spec.some_field with pattern \"^pattern$\" must be an object." in str(excinfo.value)

def test_valid_pattern_properties_nested_strings_pass():
    spec = {
        "some_field": {
            "patternProperties": {
                "^[a-zA-Z0-9_-]+$": {
                    "type": "object",
                    "properties": {
                        "cidr": {
                            "type": "string",
                            "pattern": "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$"
                        }
                    },
                    "required": ["cidr"]
                }
            }
        }
    }
    # Should pass silently
    check_no_array_or_invalid_pattern_in_spec(spec)

def test_nested_structure_with_array_type_raises():
    spec = {
        "level1": {
            "level2": {
                "field": {
                    "type": "array"
                }
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_no_array_or_invalid_pattern_in_spec(spec)
    assert "Invalid array type found at spec.level1.level2.field" in str(excinfo.value)
