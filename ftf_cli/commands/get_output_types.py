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
def get_output_types(profile):
    """Get the list of registered output types in the control plane"""
    try:
        # Check if profile is set
        click.echo(f"Profile selected: {profile}")
        credentials = is_logged_in(profile)
        if not credentials:
            raise click.UsageError(
                f"❌ Not logged in under profile {profile}. Please login first."
            )

        # Extract credentials
        control_plane_url = credentials["control_plane_url"]
        username = credentials["username"]
        token = credentials["token"]

        # Make a request to fetch output types
        response = requests.get(
            f"{control_plane_url}/cc-ui/v1/tf-outputs", auth=(username, token)
        )

        if response.status_code == 200:
            registered_output_types = []
            for output_type in response.json():
                registered_output_types.append(output_type["name"])
            registered_output_types.sort()
            if len(registered_output_types) == 0:
                click.echo("No output types registered.")
                return
            click.echo("Registered output types:")
            for output_type in registered_output_types:
                click.echo(f"- {output_type}")
        else:
            raise click.UsageError(
                f"❌ Failed to fetch output types. Status code: {response.status_code}"
            )
    except Exception as e:
        raise click.UsageError(f"❌ An error occurred: {e}")
