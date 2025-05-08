import pytest
from click.testing import CliRunner
from ftf_cli.commands.add_variable import add_variable
from unittest.mock import patch, mock_open


@pytest.fixture
@patch("ftf_cli.utils.validate_facets_yaml")
def runner(mock_validate_facets_yaml, monkeypatch):
    # Mock ALLOWED_TYPES to control in the tests
    monkeypatch.setattr(
        "ftf_cli.utils.ALLOWED_TYPES",
        ["string", "number", "integer", "boolean", "array", "object", "enum"],
    )
    return CliRunner()


def mock_yaml_file_existence_and_content(yaml_content):
    # Mock the isfile to return True
    isfile_patch = patch("os.path.isfile", return_value=True)
    # Mock open to read the mocked yaml content
    open_patch = patch("builtins.open", mock_open(read_data=yaml_content))
    return isfile_patch, open_patch


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_variable_success(runner):
    yaml_content = """
    intent: test
    flavor: unit
    spec:
      type: object
      properties: {}
    """
    isfile_patch, open_patch = mock_yaml_file_existence_and_content(yaml_content)
    with isfile_patch, open_patch:
        result = runner.invoke(
            add_variable,
            [
                "--name",
                "test.name",
                "--type",
                "string",
                "--description",
                "A test variable",
                "--path",
                ".",
            ],
        )
        assert result.exit_code == 0
        assert (
            "Variable 'test.name' of type 'string' added with description 'A test variable' in path '.'"
            in result.output
        )


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_variable_invalid_type(runner):
    yaml_content = """
    intent: test
    flavor: unit
    spec:
      type: object
      properties: {}
    """
    isfile_patch, open_patch = mock_yaml_file_existence_and_content(yaml_content)
    with isfile_patch, open_patch:
        result = runner.invoke(
            add_variable,
            [
                "--name",
                "test.name",
                "--type",
                "invalid_type",
                "--description",
                "A test variable",
                "--path",
                ".",
            ],
        )
        assert result.exit_code != 0
        assert "not allowed." in result.output


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_variable_invalid_path(runner):
    with patch(
        "ftf_cli.utils.validate_facets_yaml",
        side_effect=Exception("facets.yaml file does not exist"),
    ):
        result = runner.invoke(
            add_variable,
            [
                "--name",
                "test.name",
                "--type",
                "string",
                "--description",
                "A test variable",
                "--path",
                "invalid_path",
            ],
        )
        assert result.exit_code != 0
        assert "facets.yaml file does not exist" in result.output


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_enum_variable_with_options(runner):
    yaml_content = """
    intent: test
    flavor: unit
    spec:
      type: object
      properties: {}
    """
    isfile_patch, open_patch = mock_yaml_file_existence_and_content(yaml_content)
    with isfile_patch, open_patch:
        result = runner.invoke(
            add_variable,
            [
                "--name",
                "test_enum",
                "--type",
                "enum",
                "--description",
                "An enum test variable",
                "--options",
                "opt1,opt2,opt3",
                "--path",
                ".",
            ],
        )
        assert result.exit_code == 0
        assert (
            "Variable 'test_enum' of type 'enum' added with description 'An enum test variable' in path '.'"
            in result.output
        )


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_enum_variable_without_options(runner):
    yaml_content = """
    intent: test
    flavor: unit
    spec:
      type: object
      properties: {}
    """
    isfile_patch, open_patch = mock_yaml_file_existence_and_content(yaml_content)
    with isfile_patch, open_patch:
        result = runner.invoke(
            add_variable,
            [
                "--name",
                "test_enum",
                "--type",
                "enum",
                "--description",
                "An enum test variable",
                "--path",
                ".",
            ],
        )
        assert result.exit_code != 0
        assert "Options must be specified for enum type." in result.output


@pytest.mark.skip(reason="This test is currently disabled")
def test_add_variable_empty_spec(runner):
    # YAML content with an empty spec section
    yaml_content = """
    intent: test
    flavor: unit
    spec:
    """
    isfile_patch, open_patch = mock_yaml_file_existence_and_content(yaml_content)
    with isfile_patch, open_patch:
        # Attempt to add a new variable to the empty spec
        result = runner.invoke(
            add_variable,
            [
                "--name",
                "new_variable",
                "--type",
                "string",
                "--description",
                "A new test variable",
                "--path",
                ".",
            ],
        )
        assert result.exit_code == 0
        assert (
            "Variable 'new_variable' of type 'string' added with description 'A new test variable' in path '.'"
            in result.output
        )
