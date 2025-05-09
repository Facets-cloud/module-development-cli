import click
from urllib.parse import urlparse
from ftf_cli.utils import fetch_user_details, store_credentials
import requests


@click.command()
@click.option(
    "-c",
    "--control-plane-url",
    prompt="Control Plane URL",
    help="The URL of the control plane",
)
@click.option("-u", "--username", prompt="Username", help="Your username")
@click.option(
    "-t", "--token", prompt="Token", hide_input=True, help="Your access token"
)
@click.option(
    "-p",
    "--profile",
    default="default",
    prompt="Profile",
    help="The profile name to use",
)
def login(profile, username, token, control_plane_url):
    """Login and store credentials under a named profile."""

    # Validate and clean URL
    if not control_plane_url.startswith(("http://", "https://")):
        raise click.UsageError(
            "❌ Invalid URL. Please ensure the URL starts with http:// or https://"
        )

    parsed_url = urlparse(control_plane_url)
    control_plane_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

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
    except requests.exceptions.HTTPError as e:
        raise click.UsageError(f"❌ Failed to login: {e}")
