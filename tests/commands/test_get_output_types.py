import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from ftf_cli.commands.get_output_types import get_output_types


class TestGetOutputTypesCommand:
    """Test cases for get_output_types command."""

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
    def sample_api_response(self):
        return [
            {
                "name": "database",
                "namespace": "@outputs",
                "properties": {"type": "object"}
            },
            {
                "name": "cache",
                "namespace": "@outputs", 
                "properties": {"type": "object"}
            },
            {
                "name": "sqs",
                "namespace": "@custom",
                "properties": {"type": "object"}
            },
        ]

    def test_successful_get_output_types(
        self, runner, mock_credentials, sample_api_response
    ):
        """Test successfully getting output types with namespaces."""
        with patch(
            "ftf_cli.commands.get_output_types.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_types,
                ["--profile", "test"]
            )

            # Print output for debugging
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            # Assertions
            assert result.exit_code == 0
            assert "Registered output types:" in result.output
            assert "- @custom/sqs" in result.output
            assert "- @outputs/cache" in result.output
            assert "- @outputs/database" in result.output

            # Verify API call was made
            mock_requests.assert_called_once_with(
                "https://test.example.com/cc-ui/v1/tf-outputs",
                auth=("testuser", "testtoken"),
            )

    def test_no_output_types(self, runner, mock_credentials):
        """Test when no output types are registered."""
        with patch(
            "ftf_cli.commands.get_output_types.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup empty API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_types,
                ["--profile", "test"]
            )

            assert result.exit_code == 0
            assert "No output types registered." in result.output

    def test_missing_namespace_fallback(self, runner, mock_credentials):
        """Test fallback to @outputs when namespace is missing."""
        api_response_no_namespace = [
            {
                "name": "legacy_output",
                # Missing namespace field
                "properties": {"type": "object"}
            }
        ]

        with patch(
            "ftf_cli.commands.get_output_types.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_response_no_namespace
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_types,
                ["--profile", "test"]
            )

            assert result.exit_code == 0
            assert "- @outputs/legacy_output" in result.output

    def test_not_logged_in_error(self, runner):
        """Test error when user is not logged in."""
        with patch(
            "ftf_cli.commands.get_output_types.is_logged_in", return_value=False
        ):
            result = runner.invoke(
                get_output_types,
                ["--profile", "test"]
            )

            assert result.exit_code != 0
            assert "Not logged in" in result.output

    def test_api_error(self, runner, mock_credentials):
        """Test error when API call fails."""
        with patch(
            "ftf_cli.commands.get_output_types.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup failed API response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_types,
                ["--profile", "test"]
            )

            assert result.exit_code != 0
            assert "Failed to fetch output types" in result.output
            assert "Status code: 500" in result.output
