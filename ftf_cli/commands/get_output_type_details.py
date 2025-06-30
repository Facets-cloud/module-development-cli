import json
import os
import re
import traceback
import click
import requests

from ftf_cli.utils import is_logged_in, get_profile_with_priority


def parse_namespace_and_name(output_type):
    """Parse output_type into namespace and name components.
    
    Args:
        output_type (str): Format should be @namespace/name
        
    Returns:
        tuple: (namespace, name)
        
    Raises:
        click.UsageError: If format is invalid
    """
    pattern = r"(@[^/]+)/(.*)"
    match = re.match(pattern, output_type)
    if not match:
        raise click.UsageError(
            f"❌ Invalid format '{output_type}'. Expected format: @namespace/name (e.g., @outputs/vpc, @anuj/sqs)"
        )
    return match.group(1), match.group(2)


@click.command()
@click.option(
    "-p",
    "--profile",
    default=get_profile_with_priority(),
    help="The profile name to use (defaults to the current default profile)",
)
@click.option(
    "-o",
    "--output-type",
    prompt="Output type to get details for",
    type=str,
    help="The output type to get details for. Format: @namespace/name (e.g., @outputs/vpc, @anuj/sqs)",
)
def get_output_type_details(profile, output_type):
    """Get the details of a registered output type from the control plane"""
    try:
        # Validate output_type format
        namespace, name = parse_namespace_and_name(output_type)

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
            # Create lookup by (namespace, name) tuple
            registered_outputs = {(output["namespace"], output["name"]): output for output in response.json()}
            
            required_output = registered_outputs.get((namespace, name))

            if not required_output:
                available_outputs = [f'{ns}/{nm}' for ns, nm in registered_outputs.keys()]
                raise click.UsageError(
                    f"❌ Output type {output_type} not found. Available outputs: {available_outputs}"
                )

            click.echo(f"=== Output Type Details: {output_type} ===\n")
            
            # Display basic information
            click.echo(f"Name: {required_output['name']}")
            click.echo(f"Namespace: {required_output['namespace']}")
            if 'source' in required_output:
                click.echo(f"Source: {required_output['source']}")
            if 'inferredFromModule' in required_output:
                click.echo(f"Inferred from Module: {required_output['inferredFromModule']}")
            
            # Display properties if present
            if "properties" in required_output and required_output["properties"]:
                click.echo(f"\n--- Properties ---")
                properties = required_output["properties"]
                click.echo(json.dumps(properties, indent=2, sort_keys=True))
            else:
                click.echo(f"\n--- Properties ---")
                click.echo("No properties defined.")

            # Display lookup tree if present
            if "lookupTree" in required_output and required_output["lookupTree"]:
                click.echo(f"\n--- Lookup Tree ---")
                try:
                    lookup_tree = json.loads(required_output["lookupTree"])
                    click.echo(json.dumps(lookup_tree, indent=2, sort_keys=True))
                except json.JSONDecodeError:
                    click.echo("Invalid JSON in lookup tree.")
            else:
                click.echo(f"\n--- Lookup Tree ---")
                lookup_tree = {"out": {"attributes": {}, "interfaces": {}}}
                click.echo(json.dumps(lookup_tree, indent=2, sort_keys=True))

        else:
            raise click.UsageError(
                f"❌ Failed to fetch output types. Status code: {response.status_code}"
            )
    except Exception as e:
        traceback.print_exc()
        raise click.UsageError(
            f"❌ An error occurred while getting output details: {e}"
        )
