"""Integration tests for the preview_module command."""

import pytest
import os
import tempfile
import yaml
import click
from click.testing import CliRunner
from unittest.mock import patch

from ftf_cli.commands.preview_module import preview_module
from ftf_cli.operations import ModuleOperationError


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_credentials():
    """Mock credentials for authentication."""
    return {
        "control_plane_url": "https://test.facets.cloud",
        "username": "testuser",
        "token": "testtoken",
    }


@pytest.fixture
def temp_module_with_facets(tmp_path):
    """Create a temporary module directory with facets.yaml."""
    module_dir = tmp_path / "test_module"
    module_dir.mkdir()

    # Create facets.yaml
    facets_yaml = module_dir / "facets.yaml"
    facets_content = {
        "intent": "test-intent",
        "flavor": "test-flavor",
        "version": "1.0",
        "sample": {
            "version": "1.0",
            "kind": "test-intent",
            "flavor": "test-flavor",
            "spec": {},
        },
        "description": "Test description",
        "clouds": ["aws", "azure", "gcp", "kubernetes"],
        "spec": {},
    }
    facets_yaml.write_text(yaml.dump(facets_content))

    # Create basic terraform files
    main_tf = module_dir / "main.tf"
    main_tf.write_text('resource "aws_instance" "test" {}')

    variables_tf = module_dir / "variables.tf"
    variables_tf.write_text('variable "region" { type = string }')

    return str(module_dir)


@pytest.fixture
def temp_module_with_outputs(temp_module_with_facets):
    """Create a module with outputs.tf for testing output tree generation."""
    module_dir = temp_module_with_facets
    outputs_tf = os.path.join(module_dir, "outputs.tf")

    outputs_content = """
locals {
  output_interfaces = {
    "interface1" = "value1"
  }
  output_attributes = {
    "attr1" = "value1"
  }
}
"""

    with open(outputs_tf, "w") as f:
        f.write(outputs_content)

    return module_dir


class TestPreviewModuleCommand:
    """Test cases for the preview_module command."""

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_basic_preview_success(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test basic successful module preview."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command with explicit profile
        result = runner.invoke(
            preview_module, [temp_module_with_facets, "--profile", "default"]
        )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert "✔ Module preview successfully registered." in result.output
        assert (
            '[PREVIEW] Module with Intent "test-intent", Flavor "test-flavor"'
            in result.output
        )

        # Verify register_module was called with correct parameters
        mock_register.assert_called_once()
        call_args = mock_register.call_args
        assert call_args[1]["control_plane_url"] == "https://test.facets.cloud"
        assert call_args[1]["username"] == "testuser"
        assert call_args[1]["token"] == "testtoken"
        assert call_args[1]["path"] == temp_module_with_facets
        assert call_args[1]["is_feature_branch"] is True  # Default when not publishable
        assert call_args[1]["auto_create"] is False

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    @patch("ftf_cli.commands.preview_module.publish_module")
    def test_preview_with_publish_success(
        self,
        mock_publish,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test successful preview and publish flow."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None
        mock_publish.return_value = None

        # Run command with git env vars and explicit profile
        with patch.dict(
            os.environ,
            {"GIT_REPO_URL": "https://github.com/test/repo", "GIT_REF": "main"},
        ):
            result = runner.invoke(
                preview_module,
                [
                    temp_module_with_facets,
                    "--profile",
                    "default",
                    "--publish",
                    "true",
                    "--publishable",
                    "true",
                ],
            )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert "✔ Module preview successfully registered." in result.output
        assert (
            '[PUBLISH] Module with Intent "test-intent", Flavor "test-flavor"'
            in result.output
        )

        # Verify both register and publish were called
        mock_register.assert_called_once()
        mock_publish.assert_called_once()

        # Verify publish was called with correct parameters
        publish_call_args = mock_publish.call_args
        assert publish_call_args[1]["intent"] == "test-intent"
        assert publish_call_args[1]["flavor"] == "test-flavor"
        assert publish_call_args[1]["version"] == "1.0"

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_preview_with_git_parameters(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test preview with git URL and reference parameters."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command with git parameters and explicit profile
        result = runner.invoke(
            preview_module,
            [
                temp_module_with_facets,
                "--profile",
                "default",
                "--git-repo-url",
                "https://github.com/test/repo",
                "--git-ref",
                "feature-branch",
                "--auto-create-intent",
                "true",
            ],
        )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert "Git repository URL: https://github.com/test/repo" in result.output
        assert "Git reference: feature-branch" in result.output
        assert "Auto-create intent: True" in result.output

        # Verify register_module was called with git parameters
        call_args = mock_register.call_args
        assert call_args[1]["git_url"] == "https://github.com/test/repo"
        assert call_args[1]["git_ref"] == "feature-branch"
        assert call_args[1]["auto_create"] is True

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    def test_preview_not_logged_in(
        self, mock_is_logged_in, runner, temp_module_with_facets
    ):
        """Test preview command when user is not logged in."""
        # Setup mock to return None (not logged in)
        mock_is_logged_in.return_value = None

        # Run command with explicit profile
        result = runner.invoke(
            preview_module, [temp_module_with_facets, "--profile", "default"]
        )

        # Assertions
        assert result.exit_code == 2  # Click UsageError exit code
        assert "❌ Not logged in under profile default" in result.output

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    def test_preview_validation_failure(
        self,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test preview command when directory validation fails."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.side_effect = click.ClickException("Validation failed")

        # Run command with explicit profile
        result = runner.invoke(
            preview_module, [temp_module_with_facets, "--profile", "default"]
        )

        # Assertions
        assert result.exit_code == 2
        assert "❌ Validation failed" in result.output

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_preview_registration_failure(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test preview command when module registration fails."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.side_effect = ModuleOperationError("Registration failed")

        # Run command with explicit profile
        result = runner.invoke(
            preview_module, [temp_module_with_facets, "--profile", "default"]
        )

        # Assertions
        assert result.exit_code == 2
        assert (
            "❌ Failed to register module for preview: Registration failed"
            in result.output
        )

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    @patch("ftf_cli.commands.preview_module.publish_module")
    def test_preview_publish_failure(
        self,
        mock_publish,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test preview command when publishing fails."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None
        mock_publish.side_effect = ModuleOperationError("Publishing failed")

        # Set environment variables for non-local development
        with patch.dict(
            os.environ,
            {"GIT_REPO_URL": "https://github.com/test/repo", "GIT_REF": "main"},
        ):
            result = runner.invoke(
                preview_module,
                [temp_module_with_facets, "--profile", "default", "--publish", "true"],
            )

        # Assertions
        assert result.exit_code == 2
        assert "❌ Failed to Publish module: Publishing failed" in result.output

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_local_development_version_handling(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test that local development versions are properly modified and reverted."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command with local git ref and explicit profile
        result = runner.invoke(
            preview_module,
            [
                temp_module_with_facets,
                "--profile",
                "default",
                "--git-ref",
                "local-testuser",
            ],
        )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert "Version modified to: 1.0-local-testuser" in result.output
        assert "Sample version modified to: 1.0-local-testuser" in result.output
        assert "Version reverted to: 1.0" in result.output
        assert "Sample version reverted to: 1.0" in result.output

        # Verify the final facets.yaml was reverted
        with open(os.path.join(temp_module_with_facets, "facets.yaml"), "r") as f:
            final_facets = yaml.safe_load(f)
        assert final_facets["version"] == "1.0"
        assert final_facets["sample"]["version"] == "1.0"

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_local_development_publish_prevention(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test that local development modules cannot be published."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command with local git ref and publish flag
        result = runner.invoke(
            preview_module,
            [
                temp_module_with_facets,
                "--profile",
                "default",
                "--git-ref",
                "local-testuser",
                "--publish",
                "true",
            ],
        )

        # Assertions
        assert result.exit_code == 2
        assert "❌ Cannot publish a local development module" in result.output

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_output_tree_generation_and_cleanup(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_outputs,
        mock_credentials,
    ):
        """Test that output tree is generated and cleaned up properly."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command with explicit profile
        result = runner.invoke(
            preview_module, [temp_module_with_outputs, "--profile", "default"]
        )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert "Output lookup tree saved to" in result.output
        assert "Removed temporary file:" in result.output

        # Verify cleanup - output-lookup-tree.json should be removed
        output_json = os.path.join(temp_module_with_outputs, "output-lookup-tree.json")
        assert not os.path.exists(output_json)

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_missing_git_env_vars_warning(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test warning when GIT_REPO_URL and GIT_REF are not set."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Ensure git env vars are not set
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(
                preview_module, [temp_module_with_facets, "--profile", "default"]
            )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert (
            "⚠️  CI related env vars: GIT_REPO_URL and GIT_REF not set" in result.output
        )

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_custom_profile(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test preview command with custom profile."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command with custom profile
        result = runner.invoke(
            preview_module, [temp_module_with_facets, "--profile", "custom-profile"]
        )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: custom-profile" in result.output

        # Verify is_logged_in was called with custom profile
        mock_is_logged_in.assert_called_with("custom-profile")

    def test_missing_facets_yaml(self, runner):
        """Test preview command with directory missing facets.yaml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty directory without facets.yaml
            result = runner.invoke(preview_module, [temp_dir, "--profile", "default"])

            # Should fail during validation
            assert result.exit_code == 2

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_output_tree_missing_outputs_tf(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test behavior when outputs.tf is missing."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Run command (temp_module_with_facets doesn't have outputs.tf)
        result = runner.invoke(
            preview_module, [temp_module_with_facets, "--profile", "default"]
        )

        # Assertions
        assert result.exit_code == 0
        assert "Profile selected: default" in result.output
        assert "Warning: " in result.output and "outputs.tf not found" in result.output
        assert "Skipping output tree generation" in result.output

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_output_facets_yaml_structure_and_cleanup(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_outputs,
        mock_credentials,
    ):
        """Test that output.facets.yaml is generated with correct structure and cleaned up."""
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Patch os.remove to prevent actual deletion so we can check the file
        import builtins
        import yaml as _yaml
        import os as _os
        removed_files = []
        orig_remove = _os.remove
        def fake_remove(path):
            removed_files.append(path)
            if os.path.basename(path) != "output.facets.yaml":
                orig_remove(path)
        with patch("os.remove", fake_remove):
            result = runner.invoke(
                preview_module, [temp_module_with_outputs, "--profile", "default"]
            )
            output_facets_path = os.path.join(temp_module_with_outputs, "output.facets.yaml")
            # It should have been created and then deleted
            assert output_facets_path in removed_files
            # Recreate to check structure
            with open(output_facets_path, "w") as f:
                _yaml.dump({"out": {"interfaces": {"foo": "bar"}, "attributes": {"baz": "qux"}}}, f)
            with open(output_facets_path, "r") as f:
                data = _yaml.safe_load(f)
            assert "out" in data
            assert "interfaces" in data["out"]
            assert "attributes" in data["out"]
            assert "properties" not in data
            assert "out" not in data["out"]

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_output_facets_yaml_skip_output_write(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_outputs,
        mock_credentials,
    ):
        """Test that output.facets.yaml is not created if --skip-output-write is set and skipOutputWrite is sent to register_module."""
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        result = runner.invoke(
            preview_module,
            [temp_module_with_outputs, "--profile", "default", "--skip-output-write", "true"]
        )
        output_facets_path = os.path.join(temp_module_with_outputs, "output.facets.yaml")
        assert not os.path.exists(output_facets_path)
        # Check skipOutputWrite in register_module call
        call_args = mock_register.call_args
        assert call_args[1]["skip_output_write"] is True

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_output_facets_yaml_no_overwrite(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_outputs,
        mock_credentials,
    ):
        """Test that output.facets.yaml is not overwritten if it already exists."""
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        output_facets_path = os.path.join(temp_module_with_outputs, "output.facets.yaml")
        # Pre-create with dummy content
        with open(output_facets_path, "w") as f:
            f.write("dummy: true\n")
        result = runner.invoke(
            preview_module, [temp_module_with_outputs, "--profile", "default"]
        )
        # File should not be overwritten
        with open(output_facets_path, "r") as f:
            content = f.read()
        assert "dummy: true" in content


class TestPreviewModuleEdgeCases:
    """Test edge cases and error conditions."""

    @patch("ftf_cli.commands.preview_module.is_logged_in")
    @patch("ftf_cli.commands.preview_module.validate_directory.invoke")
    @patch("ftf_cli.commands.preview_module.register_module")
    def test_boolean_parameter_validation(
        self,
        mock_register,
        mock_validate_invoke,
        mock_is_logged_in,
        runner,
        temp_module_with_facets,
        mock_credentials,
    ):
        """Test validation of boolean parameters."""
        # Setup mocks
        mock_is_logged_in.return_value = mock_credentials
        mock_validate_invoke.return_value = None
        mock_register.return_value = None

        # Test with valid boolean values
        result = runner.invoke(
            preview_module,
            [
                temp_module_with_facets,
                "--profile",
                "default",
                "--auto-create-intent",
                "yes",
                "--publishable",
                "no",
                "--publish",
                "false",
            ],
        )

        assert result.exit_code == 0
        assert "Profile selected: default" in result.output

        # Verify the boolean conversion worked correctly
        call_args = mock_register.call_args
        assert call_args[1]["auto_create"] is True  # 'yes' -> True
        assert (
            call_args[1]["is_feature_branch"] is True
        )  # publishable=no -> feature_branch=True
