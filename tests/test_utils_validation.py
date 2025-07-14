import pytest
import click
from ftf_cli.utils import check_no_array_or_invalid_pattern_in_spec, check_conflicting_ui_properties
import os
import tempfile
import yaml
from ftf_cli.utils import validate_yaml


def test_no_array_type_pass():
    spec = {"cpu": {"type": "number"}, "memory": {"type": "number"}}
    # Should pass silently
    check_no_array_or_invalid_pattern_in_spec(spec)


def test_array_type_raises():
    spec = {"disks": {"type": "array"}}
    with pytest.raises(click.UsageError) as excinfo:
        check_no_array_or_invalid_pattern_in_spec(spec)
    assert "Invalid array type found" in str(excinfo.value)


def test_pattern_properties_value_not_dict_raises():
    spec = {"some_field": {"patternProperties": {"^pattern$": {"type": "array"}}}}
    with pytest.raises(click.UsageError) as excinfo:
        check_no_array_or_invalid_pattern_in_spec(spec)
    assert (
            'patternProperties at spec.some_field with pattern "^pattern$" must be of type object or string'
            in str(excinfo.value)
    )


def test_valid_pattern_properties_nested_strings_pass():
    spec = {
        "some_field": {
            "patternProperties": {
                "^[a-zA-Z0-9_-]+$": {
                    "type": "object",
                    "properties": {
                        "cidr": {
                            "type": "string",
                            "pattern": "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$",
                        }
                    },
                    "required": ["cidr"],
                }
            }
        }
    }
    # Should pass silently
    check_no_array_or_invalid_pattern_in_spec(spec)


def test_nested_structure_with_array_type_raises():
    spec = {"level1": {"level2": {"field": {"type": "array"}}}}
    with pytest.raises(click.UsageError) as excinfo:
        check_no_array_or_invalid_pattern_in_spec(spec)
    assert "Invalid array type found at spec.level1.level2.field" in str(excinfo.value)


# Tests for check_conflicting_ui_properties function
def test_no_conflicting_properties_pass():
    """Test that valid configurations pass without errors."""
    spec = {
        "field1": {"type": "string"},
        "field2": {"type": "string", "x-ui-yaml-editor": True},
        "field3": {"type": "object", "patternProperties": {"^.*$": {"type": "object"}}},
        "field4": {"type": "string", "x-ui-override-disable": True},
        "field5": {"type": "string", "x-ui-overrides-only": True},
        "field6": {"type": "object", "patternProperties": {"^.*$": {"type": "string"}}, "x-ui-yaml-editor": True}
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_pattern_properties_object_type_with_yaml_editor_raises():
    """Test that patternProperties with object type + x-ui-yaml-editor conflict is detected."""
    spec = {
        "field": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "object"}},
            "x-ui-yaml-editor": True
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_conflicting_ui_properties(spec)
    assert "Configuration conflict at spec.field" in str(excinfo.value)
    assert "patternProperties of type 'object'" in str(excinfo.value)
    assert "x-ui-yaml-editor: true" in str(excinfo.value)


def test_override_disable_with_overrides_only_raises():
    """Test that x-ui-override-disable + x-ui-overrides-only conflict is detected."""
    spec = {
        "field": {
            "type": "string",
            "x-ui-override-disable": True,
            "x-ui-overrides-only": True
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_conflicting_ui_properties(spec)
    assert "Configuration conflict at spec.field" in str(excinfo.value)
    assert "x-ui-override-disable: true" in str(excinfo.value)
    assert "x-ui-overrides-only: true" in str(excinfo.value)
    assert "cannot be overridden and will only have a default value" in str(excinfo.value)
    assert "must be specified at environment level via overrides" in str(excinfo.value)


def test_nested_conflicting_properties_raises():
    """Test that conflicts in nested structures are detected with correct path."""
    spec = {
        "level1": {
            "level2": {
                "field": {
                    "type": "string",
                    "x-ui-override-disable": True,
                    "x-ui-overrides-only": True
                }
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_conflicting_ui_properties(spec)
    assert "Configuration conflict at spec.level1.level2.field" in str(excinfo.value)


def test_pattern_properties_string_type_with_yaml_editor_pass():
    """Test that patternProperties with string type + x-ui-yaml-editor is allowed."""
    spec = {
        "field": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "string"}},
            "x-ui-yaml-editor": True
        }
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_pattern_properties_with_yaml_editor_false_pass():
    """Test that patternProperties with x-ui-yaml-editor: false is allowed."""
    spec = {
        "field": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "object"}},
            "x-ui-yaml-editor": False
        }
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_override_disable_false_with_overrides_only_true_pass():
    """Test that x-ui-override-disable: false with x-ui-overrides-only: true is allowed."""
    spec = {
        "field": {
            "type": "string",
            "x-ui-override-disable": False,
            "x-ui-overrides-only": True
        }
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_override_disable_true_with_overrides_only_false_pass():
    """Test that x-ui-override-disable: true with x-ui-overrides-only: false is allowed."""
    spec = {
        "field": {
            "type": "string",
            "x-ui-override-disable": True,
            "x-ui-overrides-only": False
        }
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_multiple_conflicts_in_different_fields():
    """Test that the function detects the first conflict encountered."""
    spec = {
        "field1": {
            "type": "object",
            "patternProperties": {"^.*$": {"type": "object"}},
            "x-ui-yaml-editor": True
        },
        "field2": {
            "type": "string",
            "x-ui-override-disable": True,
            "x-ui-overrides-only": True
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_conflicting_ui_properties(spec)
    # Should detect one of the conflicts (order may vary based on dict iteration)
    assert "Configuration conflict at spec." in str(excinfo.value)


def test_empty_spec_pass():
    """Test that empty spec passes validation."""
    spec = {}
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_non_dict_values_ignored():
    """Test that non-dict values are ignored gracefully."""
    spec = {
        "field1": "string_value",
        "field2": 123,
        "field3": {"type": "string"}
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_pattern_properties_mixed_types_with_yaml_editor():
    """Test behavior when patternProperties has mixed types (string and object)."""
    spec = {
        "field": {
            "type": "object",
            "patternProperties": {
                "^string_.*$": {"type": "string"},
                "^object_.*$": {"type": "object"}
            },
            "x-ui-yaml-editor": True
        }
    }
    # Should raise error because one of the patternProperties is object type
    with pytest.raises(click.UsageError) as excinfo:
        check_conflicting_ui_properties(spec)
    assert "Configuration conflict at spec.field" in str(excinfo.value)
    assert "patternProperties of type 'object'" in str(excinfo.value)


def test_pattern_properties_only_string_types_with_yaml_editor_pass():
    """Test that multiple patternProperties all with string type + yaml-editor passes."""
    spec = {
        "field": {
            "type": "object",
            "patternProperties": {
                "^config_.*$": {"type": "string"},
                "^setting_.*$": {"type": "string"}
            },
            "x-ui-yaml-editor": True
        }
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_facets_yaml_with_valid_iac_block():
    data = {
        "intent": "test",
        "flavor": "default",
        "version": "1.0",
        "description": "desc",
        "spec": {},
        "clouds": ["aws"],
        "iac": {
            "validated_files": ["variables.tf", "tekton.tf"]
        }
    }
    # Should pass validation
    validate_yaml(data)


def test_facets_yaml_with_iac_not_object():
    data = {
        "intent": "test",
        "flavor": "default",
        "version": "1.0",
        "description": "desc",
        "spec": {},
        "clouds": ["aws"],
        "iac": "not-an-object"
    }
    with pytest.raises(click.UsageError) as excinfo:
        validate_yaml(data)
    assert "iac" in str(excinfo.value)


def test_facets_yaml_with_iac_validated_files_not_array():
    data = {
        "intent": "test",
        "flavor": "default",
        "version": "1.0",
        "description": "desc",
        "spec": {},
        "clouds": ["aws"],
        "iac": {
            "validated_files": "not-an-array"
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        validate_yaml(data)
    assert "validated_files" in str(excinfo.value)


def test_facets_yaml_with_iac_validated_files_array_of_non_strings():
    data = {
        "intent": "test",
        "flavor": "default",
        "version": "1.0",
        "description": "desc",
        "spec": {},
        "clouds": ["aws"],
        "iac": {
            "validated_files": [1, 2, 3]
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        validate_yaml(data)
    assert "validated_files" in str(excinfo.value)
