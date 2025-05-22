import os
import pytest
import configparser
import requests
from unittest.mock import patch, mock_open, MagicMock, call
from click.testing import CliRunner
from ftf_cli.commands.login import login, use_existing_profile, validate_and_clean_url, authenticate_and_store
import click


@pytest.fixture
def runner():
    """Provide a Click CLI test runner that can be used across tests."""
    return CliRunner()


@pytest.fixture
def mock_credentials_file():
    """Mock an existing credentials file with sample profiles."""
    mock_config = configparser.ConfigParser()
    mock_config['facetsdemo'] = {
        'control_plane_url': 'https://demo.facets.cloud',
        'username': 'demouser',
        'token': 'demotoken'
    }
    mock_config['default'] = {
        'control_plane_url': 'https://default.facets.cloud',
        'username': 'defaultuser',
        'token': 'defaulttoken'
    }
    
    # Convert to string format as it would appear in a file
    config_str = ""
    for section in mock_config.sections():
        config_str += f"[{section}]\n"
        for key, value in mock_config[section].items():
            config_str += f"{key} = {value}\n"
        config_str += "\n"
    
    return config_str


class MockResponse:
    """Mock HTTP response for testing."""
    def __init__(self, status_code=200):
        self.status_code = status_code
    
    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")


@pytest.mark.parametrize("url,expected", [
    ("http://example.com/path", "http://example.com"),
    ("https://test.cloud/api/v1", "https://test.cloud"),
    ("https://domain.com:8080/path", "https://domain.com:8080")
])
def test_validate_and_clean_url(url, expected):
    """Test URL validation and cleaning."""
    assert validate_and_clean_url(url) == expected


def test_validate_and_clean_url_invalid():
    """Test URL validation fails with invalid URL."""
    with pytest.raises(click.exceptions.UsageError):
        validate_and_clean_url("invalid-url")


@patch('os.path.exists')
@patch('configparser.ConfigParser.read')
@patch('builtins.open', new_callable=mock_open)
@patch('ftf_cli.commands.login.fetch_user_details')
@patch('ftf_cli.commands.login.set_default_profile')
@patch('os.environ', {})
def test_use_existing_profile_success(
    mock_set_default, mock_fetch, mock_exists, 
    runner, mock_credentials_file
):
    """Test successful login with existing profile."""
    # Setup mocks
    mock_exists.return_value = True
    mock_fetch.return_value = MockResponse()
    
    # Setup configparser mock to return our profiles
    mock_config = MagicMock()
    mock_config.sections.return_value = ['facetsdemo', 'default']
    mock_config.__getitem__.side_effect = lambda x: {
        'control_plane_url': 'https://demo.facets.cloud', 
        'username': 'demouser', 
        'token': 'demotoken'
    } if x == 'facetsdemo' else {
        'control_plane_url': 'https://default.facets.cloud', 
        'username': 'defaultuser', 
        'token': 'defaulttoken'
    }
    
    # Mock the configparser instance
    with patch('configparser.ConfigParser', return_value=mock_config), \
         patch('click.confirm', return_value=True), \
         patch('click.prompt', return_value='1'), \
         patch('click.echo'):
        
        # Test function
        result = use_existing_profile()
        
        # Assert expectations
        assert result == True
        mock_set_default.assert_called_once_with('facetsdemo')
        assert os.environ.get('FACETS_PROFILE') == 'facetsdemo'


@patch('os.path.exists')
def test_use_existing_profile_no_credentials_file(mock_exists, runner):
    """Test when no credentials file exists."""
    mock_exists.return_value = False
    
    result = use_existing_profile()
    
    assert result is False


@patch('os.path.exists')
def test_use_existing_profile_no_profiles(mock_exists, runner):
    """Test when credentials file exists but has no profiles."""
    mock_exists.return_value = True
    
    # Mock empty config
    mock_config = MagicMock()
    mock_config.sections.return_value = []
    
    with patch('configparser.ConfigParser', return_value=mock_config):
        result = use_existing_profile()
        assert result is False


@patch('os.path.exists')
def test_use_existing_profile_user_declines(mock_exists, runner):
    """Test when user declines to use existing profile."""
    mock_exists.return_value = True
    
    # Setup mock config with profiles
    mock_config = MagicMock()
    mock_config.sections.return_value = ['facetsdemo', 'default']
    
    with patch('configparser.ConfigParser', return_value=mock_config), \
         patch('click.confirm', return_value=False), \
         patch('click.echo'):
        
        result = use_existing_profile()
        assert result is False


@patch('os.path.exists')
def test_use_existing_profile_authentication_failure(mock_exists, runner):
    """Test when authentication fails with existing profile."""
    mock_exists.return_value = True
    
    # Mock config with profiles
    mock_config = MagicMock()
    mock_config.sections.return_value = ['facetsdemo', 'default']
    mock_config.__getitem__.side_effect = lambda x: {
        'control_plane_url': 'https://demo.facets.cloud', 
        'username': 'demouser', 
        'token': 'demotoken'
    }
    
    # Create mock response that raises an exception
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Authentication failed")
    
    with patch('configparser.ConfigParser', return_value=mock_config), \
         patch('ftf_cli.commands.login.fetch_user_details', return_value=mock_response), \
         patch('click.confirm', return_value=True), \
         patch('click.prompt', return_value='1'), \
         patch('click.echo'), \
         pytest.raises(click.exceptions.UsageError):
        
        use_existing_profile()


def test_authenticate_and_store_success():
    """Test successful authentication and credential storage."""
    # Create mock response
    mock_response = MagicMock()
    
    with patch('ftf_cli.commands.login.fetch_user_details', return_value=mock_response), \
         patch('ftf_cli.commands.login.store_credentials') as mock_store, \
         patch('ftf_cli.commands.login.set_default_profile') as mock_set_default, \
         patch('os.environ', {}), \
         patch('click.echo'):
        
        authenticate_and_store("https://test.facets.cloud", "testuser", "testtoken", "testprofile")
        
        # Assert the credentials were stored correctly
        mock_store.assert_called_once_with("testprofile", {
            'control_plane_url': 'https://test.facets.cloud',
            'username': 'testuser',
            'token': 'testtoken',
        })
        mock_set_default.assert_called_once_with("testprofile")
        assert os.environ.get('FACETS_PROFILE') == 'testprofile'


def test_authenticate_and_store_authentication_failure():
    """Test authentication failure during store credential process."""
    # Mock response with error
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Authentication failed")
    
    with patch('ftf_cli.commands.login.fetch_user_details', return_value=mock_response), \
         pytest.raises(click.exceptions.UsageError):
        
        authenticate_and_store("https://test.facets.cloud", "testuser", "invalid-token", "testprofile")


@patch('ftf_cli.commands.login.use_existing_profile')
@patch('ftf_cli.commands.login.authenticate_and_store')
@patch('ftf_cli.commands.login.validate_and_clean_url')
def test_login_new_profile(mock_validate_url, mock_auth_store, mock_use_existing, runner):
    """Test login with a new profile."""
    # Mock use_existing_profile to return False (no existing profile used)
    mock_use_existing.return_value = False
    mock_validate_url.return_value = "https://test.facets.cloud"
    
    result = runner.invoke(login, [
        "--profile", "newprofile",
        "--control-plane-url", "https://test.facets.cloud",
        "--username", "testuser",
        "--token", "testtoken"
    ])
    
    assert result.exit_code == 0
    mock_use_existing.assert_called_once()
    mock_validate_url.assert_called_once_with("https://test.facets.cloud")
    mock_auth_store.assert_called_once_with(
        "https://test.facets.cloud", 
        "testuser", 
        "testtoken", 
        "newprofile"
    )


@patch('ftf_cli.commands.login.use_existing_profile')
def test_login_existing_profile(mock_use_existing, runner):
    """Test login when an existing profile is used."""
    # Mock use_existing_profile to return True (existing profile used)
    mock_use_existing.return_value = True
    
    result = runner.invoke(login, [])
    
    assert result.exit_code == 0
    mock_use_existing.assert_called_once()


@patch('ftf_cli.commands.login.use_existing_profile')
@patch('ftf_cli.commands.login.get_control_plane_url')
@patch('ftf_cli.commands.login.get_username')
@patch('ftf_cli.commands.login.get_token')
@patch('ftf_cli.commands.login.get_profile')
@patch('ftf_cli.commands.login.validate_and_clean_url')
@patch('ftf_cli.commands.login.authenticate_and_store')
def test_login_with_interactive_prompts(
    mock_auth_store, mock_validate_url, mock_get_profile, mock_get_token,
    mock_get_username, mock_get_url, mock_use_existing, runner
):
    """Test login with interactive prompts."""
    # Set up mocks
    mock_use_existing.return_value = False
    mock_get_url.return_value = "https://test.facets.cloud"
    mock_get_username.return_value = "testuser"
    mock_get_token.return_value = "testtoken"
    mock_get_profile.return_value = "testprofile"
    mock_validate_url.return_value = "https://test.facets.cloud"
    
    result = runner.invoke(login, [])
    
    assert result.exit_code == 0
    mock_validate_url.assert_called_once_with("https://test.facets.cloud")
    mock_auth_store.assert_called_once_with(
        "https://test.facets.cloud", 
        "testuser", 
        "testtoken", 
        "testprofile"
    )


@patch('ftf_cli.commands.login.use_existing_profile')
@patch('ftf_cli.commands.login.validate_and_clean_url')
def test_login_with_invalid_url(mock_validate_url, mock_use_existing, runner):
    """Test login fails with invalid URL."""
    # Mock use_existing_profile to return False (no existing profile used)
    mock_use_existing.return_value = False
    mock_validate_url.side_effect = click.exceptions.UsageError("Invalid URL")
    
    result = runner.invoke(login, [
        "--control-plane-url", "invalid-url",
        "--username", "testuser",
        "--token", "testtoken"
    ])
    
    assert result.exit_code != 0
    mock_validate_url.assert_called_once_with("invalid-url")


@patch('ftf_cli.commands.login.use_existing_profile')
@patch('ftf_cli.commands.login.get_control_plane_url')
@patch('ftf_cli.commands.login.get_username')
@patch('ftf_cli.commands.login.get_token')
@patch('ftf_cli.commands.login.get_profile')
@patch('ftf_cli.commands.login.validate_and_clean_url')
@patch('ftf_cli.commands.login.authenticate_and_store')
def test_login_full_flow_with_parameters(
    mock_auth, mock_validate, mock_get_profile, mock_get_token, 
    mock_get_username, mock_get_url, mock_use_existing, runner
):
    """Test the full login flow with all parameters provided."""
    # Setup mocks
    mock_use_existing.return_value = False
    mock_get_url.return_value = "https://test.facets.cloud"
    mock_get_username.return_value = "testuser"
    mock_get_token.return_value = "testtoken"
    mock_get_profile.return_value = "testprofile"
    mock_validate.return_value = "https://test.facets.cloud"
    
    result = runner.invoke(login, [
        "--profile", "testprofile",
        "--control-plane-url", "https://test.facets.cloud",
        "--username", "testuser",
        "--token", "testtoken"
    ])
    
    assert result.exit_code == 0
    mock_use_existing.assert_called_once()
    mock_get_url.assert_called_once_with("https://test.facets.cloud")
    mock_get_username.assert_called_once_with("testuser")
    mock_get_token.assert_called_once_with("testtoken")
    mock_get_profile.assert_called_once_with("testprofile")
    mock_validate.assert_called_once_with("https://test.facets.cloud")
    mock_auth.assert_called_once_with(
        "https://test.facets.cloud", 
        "testuser", 
        "testtoken", 
        "testprofile"
    )


@patch('ftf_cli.commands.login.use_existing_profile')
@patch('ftf_cli.commands.login.get_control_plane_url')
@patch('ftf_cli.commands.login.get_username')
@patch('ftf_cli.commands.login.get_token')
@patch('ftf_cli.commands.login.get_profile')
@patch('ftf_cli.commands.login.validate_and_clean_url')
def test_login_with_network_error(
    mock_validate, mock_get_profile, mock_get_token, 
    mock_get_username, mock_get_url, mock_use_existing, runner
):
    """Test login handling of network errors during authentication."""
    # Setup mocks
    mock_use_existing.return_value = False
    mock_get_url.return_value = "https://test.facets.cloud"
    mock_get_username.return_value = "testuser"
    mock_get_token.return_value = "testtoken"
    mock_get_profile.return_value = "testprofile"
    mock_validate.return_value = "https://test.facets.cloud"
    
    # Create a mock that raises a network error
    with patch('ftf_cli.commands.login.authenticate_and_store') as mock_auth:
        mock_auth.side_effect = requests.exceptions.ConnectionError("Network error")
        
        result = runner.invoke(login, [
            "--username", "testuser",
            "--token", "testtoken"
        ])
        
        assert result.exit_code != 0 