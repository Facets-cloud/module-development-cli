import os
import traceback
import click
import requests
import yaml
import json

from ftf_cli.utils import is_logged_in, get_profile_with_priority


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-p",
    "--profile",
    default=get_profile_with_priority,
    help="The profile name to use (defaults to the current default profile)",
)
@click.option(
    "-c",
    "--cascade",
    default=False,
    help="Delete all versions of the module. Default is false.",
)
def delete_module(path, profile, cascade):
    """Delete a module from the control plane."""
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

        # Load facets.yaml
        yaml_file = os.path.join(path, "facets.yaml")
        if not os.path.exists(yaml_file):
            raise click.UsageError(f"❌ facets.yaml not found at {path}")

        # Check if facets.yaml exists
        with open(yaml_file, "r") as file:
            facets_data = yaml.safe_load(file)

        # Extract intent and flavor
        intent = facets_data.get("intent")
        flavor = facets_data.get("flavor")
        version = facets_data.get("version")

        if not intent or not flavor or not version:
            raise click.UsageError(
                "❌ facets.yaml is missing one or more required fields: intent, flavor, version"
            )

        click.echo(
            f"Deleting module: intent={intent}, flavor={flavor}, version={version}, cascade={cascade}"
        )

        # Prompt for confirmation
        if not click.confirm(
            f"Are you sure you want to delete {intent}/{flavor}/{version}?"
        ):
            click.echo("Module deletion cancelled.")
            return

        # Construct URL with query parameters
        api_url = f"{control_plane_url}/cc-ui/v1/registry/module/{intent}/{flavor}/{version}"
        if cascade:
            api_url += "?cascade=true"

        response = requests.get(
            api_url, auth=(username, token)
        )

        module_id = -1

        filtered_modules = []
        for module in response.json():
            if (
                module["intentDetails"]["name"] == intent
                and module["flavor"] == flavor
                and module["version"] == version
            ):
                filtered_modules.append(module)

        for module in filtered_modules:
            if module["stage"] == "PUBLISHED":
                module_id = module["id"]
                break
            elif (
                module["stage"] == "PREVIEW"
                and module["previewModuleId"] is not None
            ):
                module_id = module["previewModuleId"]
                break

        if module_id == -1:
            raise click.UsageError(
                f"❌ Module with intent {intent} flavor {flavor} version {version} not found."
            )

        delete_response = requests.delete(
            f"{control_plane_url}/cc-ui/v1/modules/{module_id}",
            auth=(username, token),
        )
        if delete_response.status_code == 200:
            click.echo(
                f"✅ Module with intent {intent} flavor {flavor} version {version} deleted successfully."
            )
        else:
            click.echo(
                f"❌ Failed to delete module with intent {intent} flavor {flavor} version {version}.{delete_response.json().get('message', 'Unknown error')}"
            )
        return

    except Exception as e:
        traceback.print_exc()
        raise click.UsageError(
            f"❌ Error encountered while deleting module with intent {intent} flavor {flavor} version {version}: {e}"
        )
