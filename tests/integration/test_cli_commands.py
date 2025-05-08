import os
import shutil
import subprocess
import pytest
import yaml

# Directories and paths should be adjusted based on actual project structure
MODULE_PATH = "test_module"


@pytest.fixture(scope="module")
def setup_module_folder():
    """Fixture to set up and tear down a temporary module directory for testing."""
    # Setup: Create a temporary directory for the module
    os.makedirs(MODULE_PATH, exist_ok=True)
    yield
    # Teardown: Remove the directory after tests are done
    shutil.rmtree(MODULE_PATH, ignore_errors=True)


def test_generate_module(setup_module_folder):
    """Test the generate-module command."""
    # Execute the generate-module command with test parameters
    result = subprocess.run(
        [
            "ftf",
            "generate-module",
            "--intent",
            "test_intent",
            "--flavor",
            "test_flavor",
            "--cloud",
            "aws",
            "--title",
            "Test Module",
            "--description",
            "A test description.",
        ],
        cwd=MODULE_PATH,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Generate module failed: {result.stderr}"
    module_path = os.path.join(MODULE_PATH, "test_intent", "test_flavor", "1.0")
    assert os.path.exists(module_path)
    assert os.path.exists(os.path.join(module_path, "main.tf"))
    assert os.path.exists(os.path.join(module_path, "variables.tf"))
    assert os.path.exists(os.path.join(module_path, "outputs.tf"))
    assert os.path.exists(os.path.join(module_path, "facets.yaml"))


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_variable(setup_module_folder):
    """Test the add-variable command."""
    # Navigate to the correct directory structure
    module_base = os.path.join(MODULE_PATH, "test_intent", "test_flavor", "1.0")
    os.makedirs(module_base, exist_ok=True)

    # Execute the add-variable command
    result = subprocess.run(
        [
            "ftf",
            "add-variable",
            "--name",
            "test_variable",
            "--type",
            "string",
            "--description",
            "A test variable.",
            module_base,
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Add variable failed: {result.stderr}"

    # Verify the variable addition in facets.yaml
    facets_file = os.path.join(module_base, "facets.yaml")
    with open(facets_file, "r") as file:
        facets_data = yaml.safe_load(file)

    assert (
        "test_variable" in facets_data["spec"]["properties"]
    ), "Variable 'test_variable' not found in facets.yaml"
    assert (
        facets_data["spec"]["properties"]["test_variable"]["type"] == "string"
    ), "Variable type is not 'string'"
    assert (
        facets_data["spec"]["properties"]["test_variable"]["description"]
        == "A test variable."
    ), "Variable description does not match"


@pytest.mark.skip(reason="This test is currently disabled")
def test_validate_directory(setup_module_folder):
    """Test the validate-directory command."""
    # Run validation on the generated module
    module_base = os.path.join(MODULE_PATH, "test_intent", "test_flavor", "1.0")
    result = subprocess.run(
        ["ftf", "validate-directory", module_base], capture_output=True, text=True
    )

    assert result.returncode == 0, f"Validation failed: {result.stderr}"
    assert (
        "Terraform validation successful." in result.stdout
    ), "Terraform validation was not successful"
    assert "Checkov validation passed." in result.stdout, "Checkov validation failed"
