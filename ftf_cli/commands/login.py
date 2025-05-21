import click
from urllib.parse import urlparse
from ftf_cli.utils import fetch_user_details, store_credentials, set_default_profile
import requests
import os
import configparser


@click.command()
@click.option("-p", "--profile", default="default", help="The profile name to use")
@click.option("-c", "--control-plane-url", help="The URL of the control plane")
@click.option("-u", "--username", help="Your username")
@click.option("-t", "--token", hide_input=True, help="Your access token")
def login(profile, username, token, control_plane_url):
    """Login and store credentials under a named profile."""

    # Try to use existing profile first if available
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

    if not click.confirm("Do you want to use an existing profile or login with a new profile?", default=False):
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
    return profile or click.prompt("Profile", default="default")


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
