import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

import pytest
import yaml
from click.testing import CliRunner

from ftf_cli.commands.add_input import add_input, generate_inputs_variable


class TestAddInputCommand:
    """Test cases for add_input command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_credentials(self):
        return {
            "control_plane_url": "https://test.example.com",
            "username": "testuser",
            "token": "testtoken",
        }

    @pytest.fixture
    def sample_facets_yaml(self):
        return {
            "intent": "test_module",
            "flavor": "test_flavor",
            "version": "1.0.0",
            "inputs": {},
        }

    @pytest.fixture
    def sample_variables_tf(self):
        return """variable "instance" {
  description = "Instance configuration"
  type = object({
    kind    = string
    flavor  = string
    version = string
  })
}

variable "instance_name" {
  description = "Name of the instance"
  type = string
}

variable "environment" {
  description = "Environment name"
  type = string
}
"""

    @pytest.fixture
    def sample_api_response(self):
        return [
            {
                "name": "database",
                "namespace": "@outputs",
                "properties": {
                    "type": "object",
                    "properties": {
                        "attributes": {
                            "type": "object",
                            "properties": {
                                "host": {"type": "string"},
                                "port": {"type": "number"},
                                "name": {"type": "string"},
                            },
                        },
                        "interfaces": {
                            "type": "object",
                            "properties": {
                                "reader": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"},
                                        "connection_string": {"type": "string"},
                                    },
                                },
                                "writer": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"},
                                        "connection_string": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
            {
                "name": "cache",
                "namespace": "@outputs",
                "properties": {
                    "type": "object",
                    "properties": {
                        "attributes": {
                            "type": "object",
                            "properties": {
                                "endpoint": {"type": "string"},
                                "port": {"type": "number"},
                            },
                        },
                        "interfaces": {"type": "object", "properties": {}},
                    },
                },
            },
            {
                "name": "sqs",
                "namespace": "@custom",
                "properties": {
                    "attributes": {
                        "queue_arn": {"type": "string"},
                        "queue_url": {"type": "string"},
                        "queue_name": {"type": "string"},
                    },
                    "interfaces": {},
                },
            },
        ]

    @pytest.fixture
    def temp_dir(self, sample_facets_yaml, sample_variables_tf):
        """Create a temporary directory with facets.yaml and variables.tf files."""
        temp_dir = tempfile.mkdtemp()

        # Create facets.yaml
        facets_path = os.path.join(temp_dir, "facets.yaml")
        with open(facets_path, "w") as f:
            yaml.dump(sample_facets_yaml, f)

        # Create variables.tf
        variables_path = os.path.join(temp_dir, "variables.tf")
        with open(variables_path, "w") as f:
            f.write(sample_variables_tf)

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_successful_add_input(
        self, runner, mock_credentials, temp_dir, sample_api_response
    ):
        """Test successfully adding an input."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "db_connection",
                    "--display-name",
                    "Database Connection",
                    "--description",
                    "Database connection configuration",
                    "--output-type",
                    "@outputs/database",
                    "--profile",
                    "test",
                ],
            )

            # Print output for debugging
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            # Assertions
            assert result.exit_code == 0
            assert "✅ Input added to the" in result.output

            # Verify API call was made
            mock_requests.assert_called_once_with(
                "https://test.example.com/cc-ui/v1/tf-outputs",
                auth=("testuser", "testtoken"),
            )

    def test_missing_files_error(self, runner):
        """Test error when required files are missing."""
        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "ftf_cli.commands.add_input.is_logged_in",
            return_value={
                "control_plane_url": "test",
                "username": "test",
                "token": "test",
            },
        ):
            # Empty directory - no facets.yaml or variables.tf
            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs/database",
                ],
            )

            assert result.exit_code != 0
            assert "not found" in result.output

    def test_not_logged_in_error(self, runner, temp_dir):
        """Test error when user is not logged in."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=False
        ):
            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs/database",
                ],
            )

            assert result.exit_code != 0
            assert "Not logged in" in result.output

    def test_output_not_found_error(
        self, runner, mock_credentials, temp_dir, sample_api_response
    ):
        """Test error when requested output type is not found."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:
            # Setup API response
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs/nonexistent",  # This output doesn't exist
                    "--profile",
                    "test",
                ],
            )

            assert result.exit_code != 0
            assert "not found in registered outputs" in result.output

    def test_malformed_properties_fallback(self, runner, mock_credentials, temp_dir):
        """Test fallback behavior when output properties are malformed."""
        # API response with malformed properties
        malformed_api_response = [
            {
                "name": "malformed",
                "namespace": "@outputs",
                "properties": {
                    "type": "object",
                    "properties": {
                        "invalid_structure": {"type": "string"}
                        # Missing attributes/interfaces structure
                    },
                },
            }
        ]

        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:
            # Setup API response
            mock_response = MagicMock()
            mock_response.json.return_value = malformed_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs/malformed",
                    "--profile",
                    "test",
                ],
            )

            # Should succeed but show warning about malformed structure
            assert result.exit_code == 0
            assert "does not have expected structure" in result.output
            assert "Using default empty structure" in result.output

    def test_missing_properties_fallback(self, runner, mock_credentials, temp_dir):
        """Test fallback behavior when output has no properties."""
        # API response with missing properties
        no_properties_response = [
            {
                "name": "no_props",
                "namespace": "@outputs",
                # Missing properties field entirely
            }
        ]

        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:
            # Setup API response
            mock_response = MagicMock()
            mock_response.json.return_value = no_properties_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs/no_props",
                    "--profile",
                    "test",
                ],
            )

            # Should succeed but show warning about missing properties
            assert result.exit_code == 0
            assert "has no properties defined" in result.output
            assert "Using default empty structure" in result.output

    def test_existing_input_overwrite_warning(
        self, runner, mock_credentials, sample_api_response
    ):
        """Test warning when overwriting existing input."""
        # Create temp dir with existing input in facets.yaml
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_facets_yaml = {
                "intent": "test_module",
                "flavor": "test_flavor",
                "version": "1.0.0",
                "inputs": {
                    "existing_input": {
                        "type": "@outputs/database",
                        "displayName": "Existing Input",
                        "description": "Existing description",
                    }
                },
            }

            # Create files
            facets_path = os.path.join(temp_dir, "facets.yaml")
            with open(facets_path, "w") as f:
                yaml.dump(existing_facets_yaml, f)

            variables_path = os.path.join(temp_dir, "variables.tf")
            with open(variables_path, "w") as f:
                f.write('variable "instance" { type = string }')

            with patch(
                "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
            ), patch("requests.get") as mock_requests, patch(
                "ftf_cli.commands.add_input.run", return_value=MagicMock(returncode=0)
            ), patch(
                "ftf_cli.utils.ensure_formatting_for_object"
            ):
                # Setup API response
                mock_response = MagicMock()
                mock_response.json.return_value = sample_api_response
                mock_requests.return_value = mock_response

                result = runner.invoke(
                    add_input,
                    [
                        temp_dir,
                        "--name",
                        "existing_input",  # Same name as existing
                        "--display-name",
                        "Updated Input",
                        "--description",
                        "Updated description",
                        "--output-type",
                        "@outputs/database",
                        "--profile",
                        "test",
                    ],
                )

                assert result.exit_code == 0
                assert "already exists" in result.output
                assert "Will be overwritten" in result.output

    def test_nonexistent_path_error(self, runner):
        """Test error when path doesn't exist."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in",
            return_value={
                "control_plane_url": "test",
                "username": "test",
                "token": "test",
            },
        ):
            result = runner.invoke(
                add_input,
                [
                    "/nonexistent/path",
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs/database",
                ],
            )

            assert result.exit_code == 2  # Click validation error
            assert "does not exist" in result.output

    def test_invalid_output_type_format(self, runner, temp_dir):
        """Test error when output type format is invalid."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in",
            return_value={
                "control_plane_url": "test",
                "username": "test",
                "token": "test",
            },
        ):
            # Test missing @ prefix
            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "outputs/database",  # Missing @ prefix
                ],
            )

            assert result.exit_code != 0
            assert "Invalid format" in result.output
            assert "Expected format: @namespace/name" in result.output

    def test_invalid_output_type_format_missing_slash(self, runner, temp_dir):
        """Test error when output type format is missing slash."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in",
            return_value={
                "control_plane_url": "test",
                "username": "test",
                "token": "test",
            },
        ):
            # Test missing slash
            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@outputs_database",  # Missing slash
                ],
            )

            assert result.exit_code != 0
            assert "Invalid format" in result.output
            assert "Expected format: @namespace/name" in result.output

    def test_custom_namespace_success(
        self, runner, mock_credentials, temp_dir, sample_api_response
    ):
        """Test successfully adding an input with custom namespace."""
        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "queue_connection",
                    "--display-name",
                    "Queue Connection",
                    "--description",
                    "SQS queue connection configuration",
                    "--output-type",
                    "@custom/sqs",  # Custom namespace
                    "--profile",
                    "test",
                ],
            )

            # Print output for debugging
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            # Assertions
            assert result.exit_code == 0
            assert "✅ Input added to the" in result.output

    def test_direct_properties_structure(self, runner, mock_credentials, temp_dir):
        """Test handling outputs with direct attributes/interfaces in properties."""
        # API response with direct structure (like the sqs example)
        direct_structure_response = [
            {
                "name": "sqs",
                "namespace": "@custom",
                "properties": {
                    "attributes": {
                        "queue_arn": {"type": "string"},
                        "queue_url": {"type": "string"},
                    },
                    "interfaces": {},
                },
            }
        ]

        with patch(
            "ftf_cli.commands.add_input.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:
            # Setup API response
            mock_response = MagicMock()
            mock_response.json.return_value = direct_structure_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                add_input,
                [
                    temp_dir,
                    "--name",
                    "test_input",
                    "--display-name",
                    "Test Input",
                    "--description",
                    "Test description",
                    "--output-type",
                    "@custom/sqs",
                    "--profile",
                    "test",
                ],
            )

            # Should succeed without warnings
            assert result.exit_code == 0
            assert "does not have expected structure" not in result.output


class TestGenerateInputsVariable:
    """Test cases for generate_inputs_variable function."""

    def test_simple_schemas(self):
        """Test generating Terraform variable from simple schemas."""
        output_schemas = {
            "db": {
                "attributes": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "number"},
                    },
                },
                "interfaces": {
                    "type": "object",
                    "properties": {
                        "reader": {
                            "type": "object",
                            "properties": {"username": {"type": "string"}},
                        }
                    },
                },
            }
        }

        result = generate_inputs_variable(output_schemas)

        # Check basic structure
        assert 'variable "inputs"' in result
        assert (
            'description = "A map of inputs requested by the module developer."'
            in result
        )
        assert "type        = object({" in result

        # Check that db schema is included
        assert "db = object({" in result
        assert "attributes = object({" in result
        assert "interfaces = object({" in result

    def test_empty_schemas(self):
        """Test generating Terraform variable from empty schemas."""
        output_schemas = {}

        result = generate_inputs_variable(output_schemas)

        # Should still generate valid Terraform variable structure
        assert 'variable "inputs"' in result
        assert "type        = object({" in result
        # But with no content inside the object
        assert result.count("=") == 2  # Only the description and type assignments

    def test_multiple_schemas(self):
        """Test generating Terraform variable from multiple schemas."""
        output_schemas = {
            "database": {
                "attributes": {
                    "type": "object",
                    "properties": {"host": {"type": "string"}},
                },
                "interfaces": {"type": "object", "properties": {}},
            },
            "cache": {
                "attributes": {
                    "type": "object",
                    "properties": {"endpoint": {"type": "string"}},
                },
                "interfaces": {"type": "object", "properties": {}},
            },
        }

        result = generate_inputs_variable(output_schemas)

        # Check that both schemas are included
        assert "database = object({" in result
        assert "cache = object({" in result
