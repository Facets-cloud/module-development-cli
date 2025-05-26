import pytest
import click
from ftf_cli.utils import check_no_array_or_invalid_pattern_in_spec, check_conflicting_ui_properties
from ftf_cli.utils import check_no_array_or_invalid_pattern_in_spec, check_properties_have_required_fields, validate_yaml


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


# Tests for property title and description validation
def test_properties_with_title_and_description_pass():
    """Test that properties with both title and description pass validation."""
    spec = {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "title": "Project ID",
                "description": "The project in context to create google cloud resources"
            },
            "service_account": {
                "type": "string",
                "title": "Service Account",
                "description": "The service account to impersonate"
            }
        }
    }
    # Should pass silently
    check_properties_have_required_fields(spec)


def test_property_missing_title_raises():
    """Test that property missing title raises error."""
    spec = {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "title": "Project ID",
                "description": "The project in context to create google cloud resources"
            },
            "service_account": {
                "type": "string",
                "description": "The service account to impersonate"
                # Missing title
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_properties_have_required_fields(spec)
    assert "Missing required 'title' field for property 'service_account'" in str(excinfo.value)
    assert "spec.properties.service_account" in str(excinfo.value)


def test_property_missing_description_raises():
    """Test that property missing description raises error."""
    spec = {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "title": "Project ID",
                "description": "The project in context to create google cloud resources"
            },
            "service_account": {
                "type": "string",
                "title": "Service Account"
                # Missing description
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_properties_have_required_fields(spec)
    assert "Missing required 'description' field for property 'service_account'" in str(excinfo.value)
    assert "spec.properties.service_account" in str(excinfo.value)


def test_property_missing_both_title_and_description_raises():
    """Test that property missing both title and description raises error."""
    spec = {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "title": "Project ID",
                "description": "The project in context to create google cloud resources"
            },
            "service_account": {
                "type": "string"
                # Missing both title and description
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_properties_have_required_fields(spec)
    error_message = str(excinfo.value)
    assert "Missing required 'title', 'description' fields for property 'service_account'" in error_message
    assert "spec.properties.service_account" in error_message


def test_property_empty_fields_raises():
    """Test that property with empty title and description raises error."""
    spec = {
        "type": "object",
        "properties": {
            "project": {
                "type": "string",
                "title": "",  # Empty title
                "description": ""  # Empty description
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_properties_have_required_fields(spec)
    error_message = str(excinfo.value)
    assert "Missing required 'title', 'description' fields for property 'project'" in error_message


def test_override_disabled_properties_skip_validation():
    """Test that properties with x-ui-override-disable skip title and description validation."""
    spec = {
        "type": "object",
        "properties": {
            "internal_field": {
                "type": "string",
                "x-ui-override-disable": True
                # No title or description required for override-disabled fields
            },
            "user_field": {
                "type": "string",
                "title": "User Field",
                "description": "A user-facing field"
            }
        }
    }
    # Should pass silently
    check_properties_have_required_fields(spec)


def test_nested_override_disabled_objects_skip_validation():
    """Test that nested objects with x-ui-override-disable skip validation for all descendants."""
    spec = {
        "type": "object",
        "properties": {
            "user_config": {
                "type": "object",
                "title": "User Configuration",
                "description": "User-facing configuration",
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Name",
                        "description": "User name"
                    }
                }
            },
            "internal_config": {
                "type": "object",
                "x-ui-override-disable": True,
                # No title or description required for override-disabled objects
                "properties": {
                    "system_id": {
                        "type": "string"
                        # No title or description required - should be skipped due to parent override-disable
                    },
                    "nested_internal": {
                        "type": "object",
                        # No title or description required - should be skipped due to parent override-disable
                        "properties": {
                            "deep_field": {
                                "type": "string"
                                # No title or description required - should be skipped due to ancestor override-disable
                            }
                        }
                    }
                }
            }
        }
    }
    # Should pass silently - nested properties under override-disabled objects should not require validation
    check_properties_have_required_fields(spec)


def test_overrides_only_properties_require_validation():
    """Test that properties with x-ui-overrides-only still require title and description validation."""
    spec = {
        "type": "object",
        "properties": {
            "override_field": {
                "type": "string",
                "x-ui-overrides-only": True
                # Missing title and description - should fail validation
            },
            "user_field": {
                "type": "string",
                "title": "User Field",
                "description": "A user-facing field"
            }
        }
    }
    # Should fail because override_field is missing title and description
    with pytest.raises(click.UsageError) as excinfo:
        check_properties_have_required_fields(spec)
    error_message = str(excinfo.value)
    assert "Missing required 'title', 'description' fields for property 'override_field'" in error_message
    assert "spec.properties.override_field" in error_message


def test_overrides_only_properties_with_title_and_description_pass():
    """Test that properties with x-ui-overrides-only pass when they have title and description."""
    spec = {
        "type": "object",
        "properties": {
            "override_field": {
                "type": "string",
                "title": "Override Field",
                "description": "A field available for overrides",
                "x-ui-overrides-only": True
            },
            "user_field": {
                "type": "string",
                "title": "User Field",
                "description": "A user-facing field"
            }
        }
    }
    # Should pass silently
    check_properties_have_required_fields(spec)


def test_nested_object_properties_validation():
    """Test that nested object properties are also validated for title and description."""
    spec = {
        "type": "object",
        "properties": {
            "database": {
                "type": "object",
                "title": "Database Configuration",
                "description": "Database configuration",
                "properties": {
                    "host": {
                        "type": "string",
                        "title": "Database Host",
                        "description": "Database host"
                    },
                    "port": {
                        "type": "number",
                        "title": "Database Port"
                        # Missing description - should fail
                    }
                }
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        check_properties_have_required_fields(spec)
    assert "Missing required 'description' field for property 'port'" in str(excinfo.value)
    assert "spec.properties.database.properties.port" in str(excinfo.value)


def test_validate_yaml_with_missing_property_title():
    """Test that validate_yaml function catches missing property title."""
    yaml_data = {
        "intent": "test-intent",
        "flavor": "test-flavor",
        "version": "1.0",
        "description": "Test module description",
        "clouds": ["aws"],
        "spec": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "title": "Project ID",
                    "description": "The project in context"
                },
                "region": {
                    "type": "string",
                    "description": "The region to deploy resources"
                    # Missing title
                }
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        validate_yaml(yaml_data)
    assert "Missing required 'title' field for property 'region'" in str(excinfo.value)


def test_validate_yaml_with_missing_property_description():
    """Test that validate_yaml function catches missing property description."""
    yaml_data = {
        "intent": "test-intent",
        "flavor": "test-flavor",
        "version": "1.0",
        "description": "Test module description",
        "clouds": ["aws"],
        "spec": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "title": "Project ID",
                    "description": "The project in context"
                },
                "region": {
                    "type": "string",
                    "title": "Region"
                    # Missing description
                }
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        validate_yaml(yaml_data)
    assert "Missing required 'description' field for property 'region'" in str(excinfo.value)


def test_validate_yaml_with_overrides_only_missing_fields():
    """Test that validate_yaml fails when x-ui-overrides-only properties are missing title/description."""
    yaml_data = {
        "intent": "test-intent",
        "flavor": "test-flavor",
        "version": "1.0",
        "description": "Test module description",
        "clouds": ["aws"],
        "spec": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "title": "Project ID",
                    "description": "The project in context"
                },
                "override_field": {
                    "type": "string",
                    "description": "An override field",
                    "x-ui-overrides-only": True
                    # Missing title - should fail
                }
            }
        }
    }
    with pytest.raises(click.UsageError) as excinfo:
        validate_yaml(yaml_data)
    assert "Missing required 'title' field for property 'override_field'" in str(excinfo.value)


def test_validate_yaml_with_proper_property_fields_passes():
    """Test that validate_yaml passes when all properties have title and description."""
    yaml_data = {
        "intent": "test-intent",
        "flavor": "test-flavor",
        "version": "1.0",
        "description": "Test module description",
        "clouds": ["aws"],
        "spec": {
            "title": "Test Spec",  # Optional
            "description": "Test spec description",  # Optional
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "title": "Project ID",
                    "description": "The project in context to create google cloud resources"
                },
                "service_account": {
                    "type": "string",
                    "title": "Service Account",
                    "description": "The service account to impersonate"
                },
                "override_field": {
                    "type": "string",
                    "title": "Override Field",
                    "description": "A field available for overrides",
                    "x-ui-overrides-only": True
                }
            }
        }
    }
    # Should pass without raising an exception
    result = validate_yaml(yaml_data)
    assert result is True
