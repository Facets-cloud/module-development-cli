import os
import click
import configparser
from ftf_cli.utils import is_logged_in, fetch_user_details, store_credentials
import requests

@click.command()
@click.option('-c', '--control-plane-url', prompt='Control Plane URL', help='The URL of the control plane')
@click.option('-u', '--username', prompt='Username', help='Your username')
@click.option('-t', '--token', prompt='Token', hide_input=True, help='Your access token')
@click.option('-p', '--profile', default='default', prompt='Profile', help='The profile name to use')

def login(profile, username, token, control_plane_url):
    """Login and store credentials under a named profile."""
    if is_logged_in(profile):
        click.echo(f'Already logged in under profile {profile}.')
        return

    try:
        response = fetch_user_details(control_plane_url, username, token)
        response.raise_for_status()

        click.echo('✔ Successfully logged in.')

        # Store credentials
        credentials = {'control_plane_url': control_plane_url, 'username': username, 'token': token}
        store_credentials(profile, credentials)
    except requests.exceptions.HTTPError as e:
        click.echo(f'❌ Failed to login: {e}')
