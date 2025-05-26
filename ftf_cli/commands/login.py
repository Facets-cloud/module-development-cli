"""Login command for the FTF CLI."""
import configparser
import os
from urllib.parse import urlparse

import click
import requests

from ftf_cli.utils import fetch_user_details, store_credentials, set_default_profile


@click.command()
@click.option("-p", "--profile", default=None, help="The profile name to use")
@click.option("-c", "--control-plane-url", help="The URL of the control plane")
@click.option("-u", "--username", help="Your username")
@click.option("-t", "--token", hide_input=True, help="Your access token")
def login(profile, username, token, control_plane_url):
    """Login and store credentials under a named profile."""

    # Flag to track if we should skip the existing profile selection
    skip_existing_profile_selection = False

    # If profile is explicitly specified, check if it exists and no other credentials are provided
    if profile and not (username or token or control_plane_url):
        if profile_exists(profile):
            # Profile exists, try to login with stored credentials
            if login_with_existing_profile(profile):
                return
        else:
            # Profile doesn't exist, ask user if they want to create it
            if not click.confirm(
                f"Profile '{profile}' doesn't exist. Do you want to create it?",
                default=True
            ):
                click.echo("Login cancelled.")
                return
            # User wants to create the profile, skip existing profile selection
            skip_existing_profile_selection = True

    # Skip existing profile selection if all args provided OR creating new profile
    if (not (username and token and control_plane_url and profile) and
        not skip_existing_profile_selection):
        # Try to use existing profile if not all arguments are provided
        if use_existing_profile():
            return

    # Get required credentials
    control_plane_url = get_control_plane_url(control_plane_url)
    username = get_username(username)
    token = get_token(token)
    profile = get_profile(profile)

    # Validate URL format
    control_plane_url = validate_and_clean_url(control_plane_url)

    # Authenticate and store credentials
    authenticate_and_store(control_plane_url, username, token, profile)


def profile_exists(profile_name):
    """Check if a profile exists in the credentials file."""
    cred_path = os.path.expanduser("~/.facets/credentials")
    if not os.path.exists(cred_path):
        return False

    config = configparser.ConfigParser()
    config.read(cred_path)
    return profile_name in config.sections()


def login_with_existing_profile(profile_name):
    """Attempt to login using an existing profile's stored credentials."""
    cred_path = os.path.expanduser("~/.facets/credentials")
    config = configparser.ConfigParser()
    config.read(cred_path)

    try:
        credentials = config[profile_name]
        click.echo(f"Using existing profile '{profile_name}'...")

        response = fetch_user_details(
            credentials["control_plane_url"],
            credentials["username"],
            credentials["token"],
        )
        response.raise_for_status()
        click.echo("✔ Successfully logged in.")

        # Make this the default profile
        os.environ["FACETS_PROFILE"] = profile_name
        set_default_profile(profile_name)
        click.echo(f"✔ Set '{profile_name}' as the default profile.")
        return True
    except requests.exceptions.HTTPError as e:
        click.echo(f"❌ Failed to login with profile '{profile_name}': {e}")
        click.echo("Please provide new credentials to update this profile.")
        return False
    except KeyError as e:
        click.echo(f"❌ Profile '{profile_name}' has incomplete credentials: {e}")
        click.echo("Please provide new credentials to update this profile.")
        return False


def use_existing_profile():
    """Check for and use existing profiles if available."""
    cred_path = os.path.expanduser("~/.facets/credentials")
    if not os.path.exists(cred_path):
        return False

    config = configparser.ConfigParser()
    config.read(cred_path)
    existing_profiles = config.sections()

    if not existing_profiles:
        return False

    # Display available profiles
    click.echo("Existing profiles found:")
    for idx, p in enumerate(existing_profiles, 1):
        click.echo(f"  {idx}. {p}")

    if not click.confirm(
        "Do you want to use an existing profile or login with a new profile?",
        default=False
    ):
        return False

    # Let user select a profile
    choices = {str(idx): p for idx, p in enumerate(existing_profiles, 1)}
    choice = click.prompt(
        "Select profile number",
        type=click.Choice(list(choices.keys())),
        show_choices=False,
    )
    profile = choices[choice]
    click.echo(f"Using profile '{profile}'")

    try:
        credentials = config[profile]
        response = fetch_user_details(
            credentials["control_plane_url"],
            credentials["username"],
            credentials["token"],
        )
        response.raise_for_status()
        click.echo("✔ Successfully logged in.")

        # Make this the default profile
        os.environ["FACETS_PROFILE"] = profile
        set_default_profile(profile)
        click.echo(f"✔ Set '{profile}' as the default profile.")
        return True
    except requests.exceptions.HTTPError as e:
        raise click.UsageError(f"❌ Failed to login: {e}")


def get_control_plane_url(control_plane_url):
    """Prompt for control plane URL if not provided."""
    return control_plane_url or click.prompt("Control Plane URL")


def get_username(username):
    """Prompt for username if not provided."""
    return username or click.prompt("Username")


def get_token(token):
    """Prompt for token if not provided."""
    return token or click.prompt("Token", hide_input=True)


def get_profile(profile):
    """Prompt for profile if not provided."""
    if profile is None:
        return click.prompt("Profile", default="default")
    return profile


def validate_and_clean_url(control_plane_url):
    """Validate URL format and clean it."""
    if not control_plane_url.startswith(("http://", "https://")):
        raise click.UsageError(
            "❌ Invalid URL. Please ensure the URL starts with http:// or https://"
        )

    parsed_url = urlparse(control_plane_url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def authenticate_and_store(control_plane_url, username, token, profile):
    """Authenticate with the control plane and store credentials."""
    try:
        response = fetch_user_details(control_plane_url, username, token)
        response.raise_for_status()

        click.echo("✔ Successfully logged in.")

        # Store credentials
        credentials = {
            "control_plane_url": control_plane_url,
            "username": username,
            "token": token,
        }
        store_credentials(profile, credentials)

        # Set as default profile
        os.environ["FACETS_PROFILE"] = profile
        set_default_profile(profile)

        click.echo(f"✔ Set '{profile}' as the default profile.")
    except requests.exceptions.HTTPError as e:
        raise click.UsageError(f"❌ Failed to login: {e}")
