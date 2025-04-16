import json
import os
import click
import requests

from ftf_cli.utils import is_logged_in


@click.command()  # Add this decorator to register the function as a Click command
@click.option(
    "-p",
    "--profile",
    default=lambda: os.getenv("FACETS_PROFILE", "default"),
    help="The profile name to use or defaults to environment variable FACETS_PROFILE if set.",
)
def get_outputs(profile):
    """Get the list of registered outputs in the control plane"""
    try:
        # Check if profile is set
        click.echo(f"Profile selected: {profile}")
        credentials = is_logged_in(profile)
        if not credentials:
            click.echo(f"❌ Not logged in under profile {profile}. Please login first.")
            return

        # Extract credentials
        control_plane_url = credentials["control_plane_url"]
        username = credentials["username"]
        token = credentials["token"]

        # Make a request to fetch outputs
        response = requests.get(
            f"{control_plane_url}/cc-ui/v1/tf-outputs", auth=(username, token)
        )

        if response.status_code == 200:
            registered_outputs = []
            for output in response.json():
                registered_outputs.append(output["name"])
            registered_outputs.sort()
            if len(registered_outputs) == 0:
                click.echo("No outputs registered.")
                return
            click.echo("Registered outputs:")
            for output in registered_outputs:
                click.echo(f"- {output}")
        else:
            click.echo(
                f"❌ Failed to fetch outputs. Status code: {response.status_code}"
            )
    except Exception as e:
        click.echo(f"❌ An error occurred: {e}")
