import pytest
from unittest.mock import patch, mock_open
from click.testing import CliRunner
from ftf_cli.commands.expose_provider import (
    expose_provider,
    generate_output_lookup,
    deflatten_dict,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_facets_yaml():
    return {
        "intent": "example-intent",
        "outputs": {"default": {"type": "@outputs/example-intent", "providers": {}}},
    }


@pytest.fixture
def mock_output_tf():
    return """
    output "example_output" {
        value = "${aws_s3_bucket.example_bucket}"
    }
    """


def test_generate_output_lookup():
    # Mock file operations
    mock_output_tf = """
    output "example_output" {
        value = "${aws_s3_bucket.example_bucket}"
    }
    """

    with patch("builtins.open", mock_open(read_data=mock_output_tf)), patch(
        "os.path.exists", return_value=True
    ):
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
        "key2.subkey2": "value3",
    }

    # Run the function
    result = deflatten_dict(flattened_dict)

    # Assert deflattened structure
    assert result == {
        "key1": "value1",
        "key2": {"subkey1": "value2", "subkey2": "value3"},
    }


@pytest.mark.skip(reason="This test is currently disabled")
def test_expose_provider_command(runner):
    # Mock necessary components
    mock_yaml_content = """
    intent: example-intent
    outputs:
      default:
        type: "@outputs/example-intent"
        providers: {}
    """

    with patch("os.path.exists", return_value=True), patch(
        "builtins.open", mock_open(read_data=mock_yaml_content)
    ), patch(
        "yaml.safe_load",
        return_value={
            "intent": "example-intent",
            "outputs": {
                "default": {"type": "@outputs/example-intent", "providers": {}}
            },
        },
    ), patch(
        "yaml.dump"
    ) as mock_yaml_dump, patch(
        "ftf_cli.commands.expose_provider.generate_output_lookup",
        return_value={"test_output": {"type": "string"}},
    ):

        # Run the command
        result = runner.invoke(
            expose_provider,
            [
                "--path",
                "./test_path",
                "--provider",
                "aws",
                "--output",
                "test_output",
                "--outputs",
                "test:test_output",
            ],
        )

        # Check command execution was successful
        assert result.exit_code == 0

        # Verify yaml.dump was called (to write updates to facets.yaml)
        mock_yaml_dump.assert_called()
