import json
import os
import traceback
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
@click.option(
    "-o",
    "--output",
    prompt="Name of the output to get details for",
    type=str,
    help="The profile name to use or defaults to environment variable FACETS_PROFILE if set.",
)
def get_output_lookup_tree(profile, output):
    """Get the lookup tree of a registered output from the control plane"""
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
            registered_outputs = {}
            for registered_output in response.json():
                registered_outputs[registered_output["name"]] = registered_output

            required_output = registered_outputs.get(output)

            if not required_output:
                click.echo(f"❌ Output {output} not found.")
                return

            if "lookupTree" not in required_output:
                lookup_tree = {"out": {"attributes": {}, "interfaces": {}}}
            else:
                lookup_tree = json.loads(required_output["lookupTree"])
            click.echo(
                f"Output lookup tree for {output}:\n{json.dumps(lookup_tree, indent=2)}"
            )

        else:
            click.echo(
                f"❌ Failed to fetch outputs. Status code: {response.status_code}"
            )
    except Exception as e:
        click.echo(f"❌ An error occurred: {e}")
        traceback.print_exc()
