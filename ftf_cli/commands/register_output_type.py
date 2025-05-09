import os
import click
import requests
import yaml
from requests import JSONDecodeError
from ftf_cli.utils import is_logged_in


@click.command()
@click.argument(
    "yaml_path", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.option(
    "-p",
    "--profile",
    default=lambda: os.getenv("FACETS_PROFILE", "default"),
    help="The profile name to use or defaults to environment variable FACETS_PROFILE if set.",
)
@click.option(
    "--inferred-from-module",
    is_flag=True,
    default=False,
    help="Flag to mark the output type as inferred from a module.",
)
def register_output_type(yaml_path, profile, inferred_from_module):
    """Register a new output type in the control plane using a YAML definition file."""
    try:
        # Check if profile is set
        click.echo(f"Profile selected: {profile}")
        credentials = is_logged_in(profile)
        if not credentials:
            raise click.UsageError(
                f"❌ Not logged in under profile {profile}. Please login first."
            )

        # Ensure file is a yaml file
        if not yaml_path.endswith((".yaml", ".yml")):
            raise click.UsageError(
                "❌ The provided file must be a YAML file (.yaml or .yml extension)."
            )

        # Parse the YAML file
        with open(yaml_path, "r") as file:
            try:
                output_type_def = yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise click.UsageError(f"❌ Error parsing YAML file: {e}")

        # Validate the YAML structure
        if not output_type_def.get("name"):
            raise click.UsageError("❌ 'name' field is required in the YAML file.")

        if not output_type_def.get("properties"):
            raise click.UsageError(
                "❌ 'properties' field is required in the YAML file."
            )

        # Parse the name to extract namespace and name
        name_parts = output_type_def["name"].split("/", 1)
        if len(name_parts) != 2:
            raise click.UsageError("❌ Name should be in the format '@namespace/name'.")

        namespace = name_parts[0]  # Keep the @ symbol
        name = name_parts[1]

        # Prepare providers list
        providers = []
        if "providers" in output_type_def:
            for provider_name, provider_data in output_type_def["providers"].items():
                providers.append(
                    {
                        "name": provider_name,
                        "source": provider_data.get("source", ""),
                        "version": provider_data.get("version", ""),
                    }
                )

        # Prepare the request payload
        request_payload = {
            "name": name,
            "namespace": namespace,
            "lookupTree": None,
            "inferredFromModule": inferred_from_module,
            "properties": output_type_def["properties"],
            "providers": providers,
        }

        # Extract credentials
        control_plane_url = credentials["control_plane_url"]
        username = credentials["username"]
        token = credentials["token"]

        # Make a request to register the output type
        response = requests.post(
            f"{control_plane_url}/cc-ui/v1/tf-outputs",
            json=request_payload,
            auth=(username, token),
        )

        if response.status_code in [200, 201]:
            click.echo(
                f"✅ Successfully registered output type: {output_type_def['name']}"
            )
        else:
            error_message = response.text
            try:
                error_json = response.json()
                if "message" in error_json:
                    error_message = error_json["message"]
            except JSONDecodeError:
                pass
            raise click.UsageError(
                f"❌ Failed to register output type. Status code: {response.status_code}, Error: {error_message}"
            )

    except Exception as e:
        raise click.UsageError(f"❌ An error occurred: {e}")
