import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from ftf_cli.commands.get_output_type_details import get_output_type_details


class TestGetOutputTypeDetailsCommand:
    """Test cases for get_output_type_details command."""

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
                "source": "CUSTOM",
                "inferredFromModule": False,
                "properties": {
                    "type": "object",
                    "properties": {
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
                                "reader": {"type": "object"},
                            },
                        },
                    },
                },
                "lookupTree": '{"out": {"attributes": {"host": {}, "port": {}}, "interfaces": {"reader": {}}}}',
            },
            {
                "name": "sqs",
                "namespace": "@custom",
                "source": "CUSTOM",
                "inferredFromModule": True,
                "properties": {
                    "attributes": {
                        "queue_arn": {"type": "string"},
                        "queue_url": {"type": "string"},
                    },
                    "interfaces": {},
                },
                "lookupTree": '{"out": {"attributes": {"queue_arn": {}, "queue_url": {}}, "interfaces": {}}}',
            },
        ]

    def test_successful_get_output_type_details(
        self, runner, mock_credentials, sample_api_response
    ):
        """Test successfully getting output type details with namespace."""
        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@outputs/database", "--profile", "test"]
            )

            # Print output for debugging
            if result.exit_code != 0:
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    print(f"Exception: {result.exception}")

            # Assertions
            assert result.exit_code == 0
            assert "=== Output Type Details: @outputs/database ===" in result.output
            assert "Name: database" in result.output
            assert "Namespace: @outputs" in result.output
            assert "Source: CUSTOM" in result.output
            assert "Inferred from Module: False" in result.output
            assert "--- Properties ---" in result.output
            assert "--- Lookup Tree ---" in result.output
            assert '"host"' in result.output
            assert '"port"' in result.output

    def test_custom_namespace_output(
        self, runner, mock_credentials, sample_api_response
    ):
        """Test getting details for custom namespace output."""
        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@custom/sqs", "--profile", "test"]
            )

            assert result.exit_code == 0
            assert "=== Output Type Details: @custom/sqs ===" in result.output
            assert "Name: sqs" in result.output
            assert "Namespace: @custom" in result.output
            assert "queue_arn" in result.output

    def test_output_not_found(
        self, runner, mock_credentials, sample_api_response
    ):
        """Test error when output type is not found."""
        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_api_response
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@outputs/nonexistent", "--profile", "test"]
            )

            assert result.exit_code != 0
            assert "Output type @outputs/nonexistent not found" in result.output
            assert "Available outputs:" in result.output

    def test_invalid_output_type_format(self, runner, mock_credentials):
        """Test error when output type format is invalid."""
        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ):
            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "invalid_format", "--profile", "test"]
            )

            assert result.exit_code != 0
            assert "Invalid format" in result.output
            assert "Expected format: @namespace/name" in result.output

    def test_missing_properties(self, runner, mock_credentials):
        """Test handling output with missing properties."""
        api_response_no_properties = [
            {
                "name": "no_props",
                "namespace": "@outputs",
                "source": "CUSTOM",
                # Missing properties
                "lookupTree": '{"out": {"attributes": {}, "interfaces": {}}}',
            }
        ]

        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_response_no_properties
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@outputs/no_props", "--profile", "test"]
            )

            assert result.exit_code == 0
            assert "No properties defined." in result.output

    def test_missing_lookup_tree(self, runner, mock_credentials):
        """Test handling output with missing lookup tree."""
        api_response_no_lookup = [
            {
                "name": "no_lookup",
                "namespace": "@outputs",
                "properties": {"type": "object"},
                # Missing lookupTree
            }
        ]

        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_response_no_lookup
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@outputs/no_lookup", "--profile", "test"]
            )

            assert result.exit_code == 0
            assert "--- Lookup Tree ---" in result.output
            # Should show default empty structure
            assert '"attributes": {}' in result.output
            assert '"interfaces": {}' in result.output

    def test_not_logged_in_error(self, runner):
        """Test error when user is not logged in."""
        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=False
        ):
            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@outputs/database", "--profile", "test"]
            )

            assert result.exit_code != 0
            assert "Not logged in" in result.output

    def test_api_error(self, runner, mock_credentials):
        """Test error when API call fails."""
        with patch(
            "ftf_cli.commands.get_output_type_details.is_logged_in", return_value=mock_credentials
        ), patch("requests.get") as mock_requests:

            # Setup failed API response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_requests.return_value = mock_response

            result = runner.invoke(
                get_output_type_details,
                ["--output-type", "@outputs/database", "--profile", "test"]
            )

            assert result.exit_code != 0
            assert "Failed to fetch output types" in result.output
            assert "Status code: 500" in result.output
