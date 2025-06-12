import pytest
import click
from ftf_cli.utils import check_no_array_or_invalid_pattern_in_spec, check_conflicting_ui_properties


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
        "field5": {"type": "string", "x-ui-overrides-only": True}
    }
    # Should pass silently
    check_conflicting_ui_properties(spec)


def test_pattern_properties_with_yaml_editor_raises():
    """Test that patternProperties + x-ui-yaml-editor conflict is detected."""
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
    assert "patternProperties" in str(excinfo.value)
    assert "x-ui-yaml-editor: true" in str(excinfo.value)
    assert "mutually exclusive" in str(excinfo.value)


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

import os
from ftf_cli.utils import validate_no_provider_blocks


def test_module_without_provider_blocks_pass():
    """Test that modules without provider blocks pass validation."""
    test_path = os.path.join(os.path.dirname(__file__), "test_data", "module_without_provider")
    # Should pass silently and return True
    result = validate_no_provider_blocks(test_path)
    assert result is True


def test_module_with_provider_block_raises():
    """Test that modules with provider blocks fail validation."""
    test_path = os.path.join(os.path.dirname(__file__), "test_data", "module_with_provider")
    with pytest.raises(click.UsageError) as excinfo:
        validate_no_provider_blocks(test_path)
    assert "Provider blocks are not allowed in module files" in str(excinfo.value)
    assert "main.tf" in str(excinfo.value)
    assert "Use exposed providers in facets.yaml instead" in str(excinfo.value)


def test_module_with_multiple_provider_blocks_raises():
    """Test that modules with multiple provider blocks in different files fail validation."""
    test_path = os.path.join(os.path.dirname(__file__), "test_data", "module_multiple_providers")
    with pytest.raises(click.UsageError) as excinfo:
        validate_no_provider_blocks(test_path)
    assert "Provider blocks are not allowed in module files" in str(excinfo.value)
    # Should detect provider blocks in both files
    error_message = str(excinfo.value)
    assert ("main.tf" in error_message or "azure.tf" in error_message)
    assert "Use exposed providers in facets.yaml instead" in str(excinfo.value)


def test_empty_directory_pass():
    """Test that empty directory (no .tf files) passes validation."""
    test_path = os.path.join(os.path.dirname(__file__), "test_data")
    # Create an empty test directory
    empty_dir = os.path.join(test_path, "empty_module")
    os.makedirs(empty_dir, exist_ok=True)
    
    try:
        result = validate_no_provider_blocks(empty_dir)
        assert result is True
    finally:
        # Clean up
        if os.path.exists(empty_dir):
            os.rmdir(empty_dir)


def test_module_with_invalid_tf_files_continues():
    """Test that modules with invalid .tf files continue validation and report only parseable files."""
    test_path = os.path.join(os.path.dirname(__file__), "test_data")
    invalid_module_dir = os.path.join(test_path, "module_with_invalid_tf")
    os.makedirs(invalid_module_dir, exist_ok=True)
    
    # Create an invalid .tf file
    invalid_tf = os.path.join(invalid_module_dir, "invalid.tf")
    with open(invalid_tf, "w") as f:
        f.write("this is not valid HCL syntax {\n")
    
    # Create a valid .tf file without provider blocks
    valid_tf = os.path.join(invalid_module_dir, "valid.tf")
    with open(valid_tf, "w") as f:
        f.write('resource "aws_instance" "test" {\n  ami = "ami-123"\n}\n')
    
    try:
        # Should pass despite invalid file and print warning
        result = validate_no_provider_blocks(invalid_module_dir)
        assert result is True
    finally:
        # Clean up
        os.remove(invalid_tf)
        os.remove(valid_tf)
        os.rmdir(invalid_module_dir)



class TestValidateNoProviderBlocks:
    """Test the validate_no_provider_blocks utility function."""

    def test_validate_no_provider_blocks_passes_with_clean_files(self):
        """Test that validation passes when no provider blocks are present."""
        import tempfile
        import os
        from ftf_cli.utils import validate_no_provider_blocks
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create clean .tf files without provider blocks
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            # Create nested directory with clean files
            nested_dir = os.path.join(temp_dir, "modules")
            os.makedirs(nested_dir)
            nested_tf = os.path.join(nested_dir, "vpc.tf")
            with open(nested_tf, "w") as f:
                f.write('''
resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"
}
''')
            
            # Should pass without raising exception
            result = validate_no_provider_blocks(temp_dir)
            assert result is True

    def test_validate_no_provider_blocks_fails_with_provider_in_root(self):
        """Test that validation fails when provider block is in root directory."""
        import tempfile
        import os
        from ftf_cli.utils import validate_no_provider_blocks
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .tf file with provider block
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            # Should raise UsageError
            with pytest.raises(click.UsageError) as excinfo:
                validate_no_provider_blocks(temp_dir)
            
            assert "Provider blocks are not allowed in module files" in str(excinfo.value)
            assert "main.tf" in str(excinfo.value)

    def test_validate_no_provider_blocks_fails_with_provider_in_nested(self):
        """Test that validation fails when provider block is in nested directory."""
        import tempfile
        import os
        from ftf_cli.utils import validate_no_provider_blocks
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create clean root file
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            # Create nested directory with provider block
            nested_dir = os.path.join(temp_dir, "modules", "networking")
            os.makedirs(nested_dir)
            nested_tf = os.path.join(nested_dir, "vpc.tf")
            with open(nested_tf, "w") as f:
                f.write('''
provider "aws" {
  region = "us-east-1"
  alias  = "east"
}

resource "aws_vpc" "nested" {
  cidr_block = "10.0.0.0/16"
}
''')
            
            # Should raise UsageError
            with pytest.raises(click.UsageError) as excinfo:
                validate_no_provider_blocks(temp_dir)
            
            assert "Provider blocks are not allowed in module files" in str(excinfo.value)
            assert "modules/networking/vpc.tf" in str(excinfo.value)

    def test_validate_no_provider_blocks_fails_with_multiple_providers(self):
        """Test that validation fails and reports all files with provider blocks."""
        import tempfile
        import os
        from ftf_cli.utils import validate_no_provider_blocks
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create .tf file with provider block in root
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
provider "aws" {
  region = "us-west-2"
}
''')
            
            # Create nested directory with another provider block
            nested_dir = os.path.join(temp_dir, "modules")
            os.makedirs(nested_dir)
            nested_tf = os.path.join(nested_dir, "database.tf")
            with open(nested_tf, "w") as f:
                f.write('''
provider "postgresql" {
  host = "localhost"
}
''')
            
            # Should raise UsageError mentioning both files
            with pytest.raises(click.UsageError) as excinfo:
                validate_no_provider_blocks(temp_dir)
            
            error_message = str(excinfo.value)
            assert "Provider blocks are not allowed in module files" in error_message
            assert "main.tf" in error_message
            assert "modules/database.tf" in error_message

    def test_validate_no_provider_blocks_handles_unparseable_files(self):
        """Test that validation handles unparseable files gracefully."""
        import tempfile
        import os
        from ftf_cli.utils import validate_no_provider_blocks
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid .tf file
            main_tf = os.path.join(temp_dir, "main.tf")
            with open(main_tf, "w") as f:
                f.write('''
resource "aws_instance" "test" {
  ami = "ami-123456"
}
''')
            
            # Create invalid .tf file
            invalid_tf = os.path.join(temp_dir, "invalid.tf")
            with open(invalid_tf, "w") as f:
                f.write("this is not valid HCL syntax {{{")
            
            # Should pass (with warning) since the valid file has no provider blocks
            # and the invalid file is just warned about but doesn't fail validation
            result = validate_no_provider_blocks(temp_dir)
            assert result is True
