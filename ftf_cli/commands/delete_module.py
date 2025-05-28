import os
import traceback
import click
import requests

from ftf_cli.utils import is_logged_in


@click.command()
@click.option(
    "-i",
    "--intent",
    prompt="Intent of the module to delete.",
    help="Intent of the module to delete.",
)
@click.option(
    "-f",
    "--flavor",
    prompt="Flavor of the module to delete.",
    help="Flavor of the module to delete.",
)
@click.option(
    "-v",
    "--version",
    prompt="Version of the module to delete.",
    help="Version of the module to delete.",
)
@click.option(
    "-s",
    "--stage",
    prompt="Stage of the module to delete.",
    type=click.Choice(["PUBLISHED", "PREVIEW"], case_sensitive=False),
    help="Stage of the module to delete.",
)
@click.option(
    "-p",
    "--profile",
    default=lambda: os.getenv("FACETS_PROFILE", "default"),
    help="The profile name to use or defaults to environment variable FACETS_PROFILE if set.",
)
def delete_module(intent, flavor, version, profile, stage):
    """Delete a module from the control plane"""
    try:
        stage = stage.upper()
        # check if profile is set
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

        response = requests.get(
            f"{control_plane_url}/cc-ui/v1/modules", auth=(username, token)
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
            if module["stage"] == stage:
                module_id = module["id"]
                break
            elif (
                stage == "PREVIEW"
                and module["stage"] == "PUBLISHED"
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