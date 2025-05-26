"""Tests for the login command."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import configparser
import sys
from requests.exceptions import HTTPError

from ftf_cli.commands.login import login, profile_exists, login_with_existing_profile


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_credentials_file():
    """Mock credentials file content."""
    return """[default]
control_plane_url = https://default.example.com
username = default_user
token = default_token

[test_profile]
control_plane_url = https://test.example.com
username = test_user
token = test_token
"""


def test_profile_exists_with_existing_profile(mock_credentials_file):
    """Test profile_exists returns True for existing profile."""
    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:
        mock_config_class.return_value = mock_config
        assert profile_exists('test_profile') is True
        assert profile_exists('default') is True


def test_profile_exists_with_non_existing_profile(mock_credentials_file):
    """Test profile_exists returns False for non-existing profile."""
    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:
        mock_config_class.return_value = mock_config
        assert profile_exists('non_existing') is False


def test_profile_exists_no_credentials_file():
    """Test profile_exists returns False when credentials file doesn't exist."""
    with patch('os.path.exists', return_value=False):
        assert profile_exists('any_profile') is False


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_with_existing_profile_success(mock_fetch, mock_set_default, mock_credentials_file):
    """Test successful login with existing profile."""
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:
        mock_config_class.return_value = mock_config
        result = login_with_existing_profile('test_profile')

        assert result is True
        mock_fetch.assert_called_once_with(
            'https://test.example.com',
            'test_user',
            'test_token'
        )
        mock_set_default.assert_called_once_with('test_profile')


@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_with_existing_profile_http_error(mock_fetch, mock_credentials_file):
    """Test login with existing profile when API returns HTTP error."""
    mock_fetch.side_effect = HTTPError("401 Unauthorized")

    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:
        mock_config_class.return_value = mock_config
        result = login_with_existing_profile('test_profile')

        assert result is False


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_command_with_existing_profile(mock_fetch, mock_set_default, runner, mock_credentials_file):
    """Test login command with existing profile automatically logs in."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    # Mock configparser directly instead of file operations
    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:

        mock_config_class.return_value = mock_config

        result = runner.invoke(login, ['-p', 'test_profile'])

        assert result.exit_code == 0
        assert "Using existing profile 'test_profile'" in result.output
        assert "✔ Successfully logged in." in result.output


def test_login_command_with_non_existing_profile_user_cancels(runner):
    """Test login command with non-existing profile when user cancels creation."""
    with patch('os.path.exists', return_value=False):
        # Simulate user clicking "No" to profile creation
        result = runner.invoke(login, ['-p', 'new_profile'], input='n\n')

        assert result.exit_code == 0
        assert "Profile 'new_profile' doesn't exist. Do you want to create it?" in result.output
        assert "Login cancelled." in result.output


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'store_credentials')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_command_with_non_existing_profile_user_creates(mock_fetch, mock_store, mock_set_default, runner):
    """Test login command with non-existing profile when user creates it."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    with patch('os.path.exists', return_value=False):

        # Simulate user input: Yes to create profile, then credentials
        user_input = 'y\nhttps://new.example.com\nnew_user\nnew_token\n'
        result = runner.invoke(login, ['-p', 'new_profile'], input=user_input)

        assert result.exit_code == 0
        assert "Profile 'new_profile' doesn't exist. Do you want to create it?" in result.output
        # Should NOT show existing profiles list
        assert "Existing profiles found:" not in result.output
        assert ("Do you want to use an existing profile or login with a new profile?"
                not in result.output)
        # Should directly prompt for credentials
        assert "Control Plane URL:" in result.output
        assert "Username:" in result.output
        assert "Token:" in result.output
        assert "✔ Successfully logged in." in result.output
        mock_store.assert_called_once()
        mock_set_default.assert_called_once_with('new_profile')


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'store_credentials')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_command_with_all_credentials_provided(mock_fetch, mock_store, mock_set_default, runner):
    """Test login command when all credentials are provided via command line."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    result = runner.invoke(login, [
        '-p', 'cli_profile',
        '-c', 'https://cli.example.com',
        '-u', 'cli_user',
        '-t', 'cli_token'
    ])

    assert result.exit_code == 0
    assert "✔ Successfully logged in." in result.output


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_command_no_profile_with_existing_profiles(mock_fetch, mock_set_default, runner, mock_credentials_file):
    """Test login command with no profile specified when profiles exist."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:

        mock_config_class.return_value = mock_config

        # Simulate user choosing to use existing profile and selecting profile 2
        user_input = 'y\n2\n'
        result = runner.invoke(login, [], input=user_input)

        assert result.exit_code == 0
        assert "Existing profiles found:" in result.output
        assert "1. default" in result.output
        assert "2. test_profile" in result.output
        assert ("Do you want to use an existing profile or login with a new profile?"
                in result.output)
        assert "Using profile 'test_profile'" in result.output
        assert "✔ Successfully logged in." in result.output


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'store_credentials')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_command_no_profile_user_chooses_new_profile(mock_fetch, mock_store, mock_set_default, runner, mock_credentials_file):
    """Test login command with no profile specified when user chooses to create new profile."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    mock_config = configparser.ConfigParser()
    mock_config.read_string(mock_credentials_file)

    with patch('os.path.exists', return_value=True), \
         patch('configparser.ConfigParser') as mock_config_class:

        mock_config_class.return_value = mock_config

        # Simulate user choosing NOT to use existing profile, then providing credentials
        user_input = 'n\nhttps://new.example.com\nnew_user\nnew_token\nnew_profile\n'
        result = runner.invoke(login, [], input=user_input)

        assert result.exit_code == 0
        assert "Existing profiles found:" in result.output
        assert ("Do you want to use an existing profile or login with a new profile?"
                in result.output)
        assert "Control Plane URL:" in result.output
        assert "Username:" in result.output
        assert "Token:" in result.output
        assert "Profile [default]:" in result.output
        assert "✔ Successfully logged in." in result.output


@patch.object(sys.modules['ftf_cli.commands.login'], 'set_default_profile')
@patch.object(sys.modules['ftf_cli.commands.login'], 'store_credentials')
@patch.object(sys.modules['ftf_cli.commands.login'], 'fetch_user_details')
def test_login_command_no_profile_no_existing_profiles(mock_fetch, mock_store, mock_set_default, runner):
    """Test login command with no profile specified when no profiles exist."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_fetch.return_value = mock_response

    with patch('os.path.exists', return_value=False):

        # Simulate user providing credentials
        user_input = 'https://new.example.com\nnew_user\nnew_token\nnew_profile\n'
        result = runner.invoke(login, [], input=user_input)

        assert result.exit_code == 0
        # Should NOT show existing profiles list since none exist
        assert "Existing profiles found:" not in result.output
        assert ("Do you want to use an existing profile or login with a new profile?"
                not in result.output)
        # Should directly prompt for credentials
        assert "Control Plane URL:" in result.output
        assert "Username:" in result.output
        assert "Token:" in result.output
        assert "Profile [default]:" in result.output
        assert "✔ Successfully logged in." in result.output
