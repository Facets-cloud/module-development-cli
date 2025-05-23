import os
import re
from typing import Dict, List, Optional, Union, Any, Tuple
import click
import questionary
import yaml
import sys
from ftf_cli.utils import (
    validate_facets_yaml,
    update_facets_yaml_imports,
    discover_resources,
)


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-n",
    "--name",
    help="The name of the import to be added. If not provided, will prompt interactively.",
)
@click.option(
    "-r",
    "--required",
    is_flag=True,
    default=True,
    help="Whether the import is required. Default is True.",
)
@click.option(
    "--resource",
    help="The Terraform resource address to import (e.g., 'aws_s3_bucket.bucket'). If not provided, will prompt interactively.",
)
@click.option(
    "--index",
    help="The index for resources with 'count' meta-argument (e.g., '0', '1', or '*' for all). Only used when the selected resource has 'count'.",
)
@click.option(
    "--key",
    help="The key for resources with 'for_each' meta-argument (e.g., 'my-key' or '*' for all). Only used when the selected resource has 'for_each'.",
)
@click.option(
    "--resource-address",
    help="The full resource address to import (e.g., 'azurerm_key_vault.for_each_key_vault[0]'). If provided, runs in non-interactive mode and skips resource discovery.",
)
def add_import(
    path: str,
    name: Optional[str] = None,
    required: Optional[bool] = None,
    resource: Optional[str] = None,
    index: Optional[str] = None,
    key: Optional[str] = None,
    resource_address: Optional[str] = None,
) -> None:
    """Add an import declaration to the module.

    This command allows you to add import declarations to the facets.yaml file,
    specifying Terraform resources that should be imported when using the module.

    The command will scan the Terraform files in the module directory, identify
    resources, and allow you to select which resources to import. It handles
    resources with count and for_each meta-arguments.

    Can be run in interactive or non-interactive mode. In non-interactive mode,
    you must provide --resource and --name options, or --resource-address and --name.
    """
    try:
        # Check if facets.yaml exists
        facets_yaml_path = os.path.join(path, "facets.yaml")
        if not os.path.exists(facets_yaml_path):
            click.echo(f"❌ facets.yaml not found at {facets_yaml_path}")
            sys.exit(1)

        # Enforce that name is required in all scenarios
        if name is None:
            click.echo("❌ Import name is required. Use --name option.")
            sys.exit(1)

        # Validate facets.yaml format
        try:
            validate_facets_yaml(path)
        except click.UsageError as e:
            click.echo(f"❌ {e}")
            sys.exit(1)

        # If resource_address is provided, skip resource discovery and run in non-interactive mode
        if resource_address is not None:
            if name is None:
                click.echo(
                    "❌ Import name is required when using --resource-address. Use --name option."
                )
                sys.exit(1)
            import_config = {
                "name": name,
                "resource_address": resource_address,
                "required": required if required is not None else True,
            }
            if not validate_import_config(import_config):
                click.echo("❌ Invalid import configuration. Aborting.")
                sys.exit(1)
            result = update_facets_yaml_non_interactive(facets_yaml_path, import_config)
            if result:
                click.echo(
                    f"✅ Import declaration {'added to' if result == True else 'updated in'} facets.yaml:"
                )
                click.echo(f"   name: {import_config['name']}")
                click.echo(f"   resource_address: {import_config['resource_address']}")
                click.echo(f"   required: {str(import_config['required']).lower()}")
            return

        # Discover resources in the module
        click.echo("Discovering resources in the module...")
        resources = discover_resources(path)

        if not resources:
            click.echo("❌ No resources found in the module.")
            sys.exit(1)

        click.echo(f"Found {len(resources)} resources.")

        # Determine if all required arguments are provided for non-interactive mode
        non_interactive = False
        if name is not None and resource is not None:
            # Find the selected resource to check if index/key is needed
            selected_resource = None
            for r in resources:
                if r["address"] == resource:
                    selected_resource = r
                    break
            if selected_resource:
                if selected_resource.get("indexed"):
                    if (
                        selected_resource.get("index_type") == "count"
                        and index is not None
                    ):
                        non_interactive = True
                    elif (
                        selected_resource.get("index_type") == "for_each"
                        and key is not None
                    ):
                        non_interactive = True
                    elif selected_resource.get("index_type") not in (
                        "count",
                        "for_each",
                    ):
                        non_interactive = True
                else:
                    non_interactive = True
            else:
                # If resource not found, fallback to interactive
                non_interactive = False
        # If not all required args, non_interactive remains False

        # Handle resource selection
        selected_resource = select_resource_by_options(
            resources, resource, non_interactive
        )
        if not selected_resource:
            sys.exit(1)

        # Configure import with CLI options or prompts
        import_config = configure_import(
            selected_resource, name, required, index, key, non_interactive
        )

        if not import_config:
            sys.exit(1)

        # Validate the import configuration
        if not validate_import_config(import_config):
            click.echo("❌ Invalid import configuration. Aborting.")
            sys.exit(1)

        # Update the facets.yaml file
        if non_interactive:
            # In non-interactive mode, always add new or overwrite existing
            result = update_facets_yaml_non_interactive(facets_yaml_path, import_config)
        else:
            result = update_facets_yaml(facets_yaml_path, import_config)

        if result:
            click.echo(
                f"✅ Import declaration {'added to' if result == True else 'updated in'} facets.yaml:"
            )
            click.echo(f"   name: {import_config['name']}")
            click.echo(f"   resource_address: {import_config['resource_address']}")
            click.echo(f"   required: {str(import_config['required']).lower()}")

    except yaml.YAMLError as e:
        click.echo(f"❌ Error parsing YAML: {e}")
        sys.exit(1)
    except Exception as e:
        if "hcl" in str(e).lower():
            click.echo(f"❌ Error parsing Terraform files: {e}")
            sys.exit(1)
        else:
            click.echo(f"❌ Unexpected error: {e}")
            sys.exit(1)


def select_resource_by_options(
    resources: List[Dict[str, Any]],
    resource_address: Optional[str] = None,
    non_interactive: bool = False,
) -> Optional[Dict[str, Any]]:
    """Select a resource based on the provided options or via interactive selection.

    Args:
        resources: List of discovered resources
        resource_address: The resource address to find, if provided
        non_interactive: Whether to run in non-interactive mode

    Returns:
        The selected resource or None if no resource was selected
    """
    if resource_address and non_interactive:
        # In non-interactive mode with provided resource address
        # Find the resource in the discovered resources
        for r in resources:
            if r["address"] == resource_address:
                return r

        click.echo(f"❌ Resource '{resource_address}' not found in the module.")
        return None
    elif resource_address:
        # In interactive mode with resource suggestion
        matches = [r for r in resources if r["address"] == resource_address]
        if matches:
            selected_resource = matches[0]
            click.echo(f"Using provided resource: {selected_resource['address']}")
            return selected_resource
        else:
            click.echo(
                f"⚠️ Resource '{resource_address}' not found. Please select from available resources."
            )
            return select_resource(resources)
    else:
        # Fully interactive resource selection
        if non_interactive:
            click.echo(
                "❌ Resource address is required in non-interactive mode. Use --resource option."
            )
            return None
        return select_resource(resources)


def select_resource(resources: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Prompt the user to select a resource from the list.

    Args:
        resources: List of discovered resources

    Returns:
        The selected resource or None if no resource was selected
    """
    choices = []
    for r in resources:
        choices.append(f"{r['display']}")

    selected = questionary.select("Select resource to import:", choices=choices).ask()

    if not selected:
        click.echo("❌ No resource selected.")
        return None

    # Extract the display part from the selected choice by removing the source info
    display_part = selected.split(" (in ")[0]

    # Find the matching resource
    for r in resources:
        if r["display"] == display_part:
            return r

    # Fallback to index-based lookup if exact match fails
    selected_index = choices.index(selected)
    return resources[selected_index]


def configure_import(
    resource: Dict[str, Any],
    name: Optional[str] = None,
    required: Optional[bool] = None,
    index: Optional[str] = None,
    key: Optional[str] = None,
    non_interactive: bool = False,
) -> Optional[Dict[str, Any]]:
    """Configure import details based on user input.

    Args:
        resource: The resource to import
        name: The name of the import
        required: Whether the import is required
        index: The index for resources with count
        key: The key for resources with for_each
        non_interactive: Whether to run in non-interactive mode

    Returns:
        Import configuration dictionary or None if configuration failed
    """
    # Get resource name from address (e.g., aws_s3_bucket.bucket -> bucket)
    default_name = resource["address"].split(".")[-1]

    # Handle name
    if name is None and non_interactive:
        click.echo(
            "❌ Import name is required in non-interactive mode. Use --name option."
        )
        return None
    elif name is None:
        name = questionary.text(
            "Import Name:",
            default=default_name,
            validate=lambda text: len(text) > 0 or "Name cannot be empty",
        ).ask()

    # Validate name format
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        message = "⚠️ Warning: Import name should only contain alphanumeric characters and underscores."
        if non_interactive:
            click.echo(f"{message} Continuing with provided name.")
        else:
            click.echo(message)
            if not questionary.confirm("Continue with this name?", default=False).ask():
                name = questionary.text(
                    "Import Name:",
                    default=default_name,
                    validate=lambda text: len(text) > 0
                    and re.match(r"^[a-zA-Z0-9_]+$", text)
                    or "Invalid name format",
                ).ask()

    # Handle required flag
    if required is None and non_interactive:
        # Default to True if not specified in non-interactive mode
        required = True
    elif required is None:
        required = questionary.confirm("Is this import required?", default=True).ask()

    # Handle indexed resources
    resource_address = resource["address"]
    if resource["indexed"]:
        if resource["index_type"] == "count":
            if index is not None:
                # Use provided index
                if index == "*" or index.isdigit():
                    resource_address = f"{resource_address}[{index}]"
                else:
                    click.echo(
                        f"❌ Invalid index format: {index}. Must be a number or '*'."
                    )
                    if non_interactive:
                        return None
                    # Fall back to interactive mode
                    index = None

            if index is None:
                if non_interactive:
                    click.echo(
                        "❌ Index is required for count resources in non-interactive mode. Use --index option."
                    )
                    return None

                index_options = ["*", "0", "1", "2", "3", "4", "5", "Custom..."]
                index_choice = questionary.select(
                    "Select resource index:", choices=index_options
                ).ask()

                if index_choice == "Custom...":
                    index = questionary.text(
                        "Enter resource index (number or '*' for all):",
                        validate=lambda text: text == "*"
                        or text.isdigit()
                        or "Index must be a number or '*'",
                    ).ask()
                else:
                    index = index_choice

                resource_address = f"{resource_address}[{index}]"

        elif resource["index_type"] == "for_each":
            if key is not None:
                # Use provided key
                if key == "*":
                    resource_address = f"{resource_address}[*]"
                elif key.isdigit():
                    # If it's a number, no quotes needed
                    resource_address = f"{resource_address}[{key}]"
                else:
                    # Add quotes for string keys
                    resource_address = f'{resource_address}["{key}"]'
            else:
                if non_interactive:
                    click.echo(
                        "❌ Key is required for for_each resources in non-interactive mode. Use --key option."
                    )
                    return None

                # For for_each, we can't easily predict the keys, so offer a text input
                key = questionary.text(
                    "Enter resource key (string, number, or '*' for all):",
                    validate=lambda text: len(text) > 0 or "Key cannot be empty",
                ).ask()

                if key == "*":
                    resource_address = f"{resource_address}[*]"
                elif key.isdigit():
                    # If it's a number, no quotes needed
                    resource_address = f"{resource_address}[{key}]"
                else:
                    # Add quotes for string keys
                    resource_address = f'{resource_address}["{key}"]'

    return {"name": name, "resource_address": resource_address, "required": required}


def validate_import_config(import_config: Dict[str, Any]) -> bool:
    """Validate the import configuration before saving.

    Args:
        import_config: The import configuration to validate

    Returns:
        True if the configuration is valid, False otherwise
    """
    # Check for required fields
    if not import_config.get("name"):
        click.echo("❌ Import name is required.")
        return False

    if not import_config.get("resource_address"):
        click.echo("❌ Resource address is required.")
        return False

    # Validate resource address format
    address = import_config["resource_address"]
    if not re.match(r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+(\[[^\]]+\])?$", address):
        click.echo(f"❌ Invalid resource address format: {address}")
        return False

    return True


def update_facets_yaml(
    yaml_path: str, import_config: Dict[str, Any]
) -> Union[bool, str]:
    """Update the facets.yaml file with the import declaration.

    Args:
        yaml_path: Path to the facets.yaml file
        import_config: The import configuration to add

    Returns:
        True if a new import was added, "updated" if an existing import was updated,
        False if the operation was canceled or failed
    """
    result = update_facets_yaml_imports(yaml_path, import_config, mode="interactive")

    # If an import with the same name exists, handle interactive prompts
    if isinstance(result, dict) and result["action"] == "exists":
        facets_data = result["facets_data"]
        i = result["index"]

        if not questionary.confirm(
            f"Import with name '{import_config['name']}' already exists. Update it?",
            default=True,
        ).ask():
            # User chose not to update, ask if they want to use a different name or quit
            action = questionary.select(
                "What would you like to do?",
                choices=["Enter a different name", "Quit without adding import"],
            ).ask()

            if action == "Quit without adding import":
                click.echo("❌ Import not added. Operation canceled.")
                sys.exit(1)

            # User wants to enter a different name
            new_name = questionary.text(
                "Enter a new import name:",
                validate=lambda text: len(text) > 0 or "Name cannot be empty",
            ).ask()

            # Validate name format
            if not re.match(r"^[a-zA-Z0-9_]+$", new_name):
                click.echo(
                    "⚠️ Warning: Import name should only contain alphanumeric characters and underscores."
                )
                if not questionary.confirm(
                    "Continue with this name?", default=False
                ).ask():
                    new_name = questionary.text(
                        "Enter a new import name:",
                        validate=lambda text: len(text) > 0
                        and re.match(r"^[a-zA-Z0-9_]+$", text)
                        or "Invalid name format",
                    ).ask()

            # Update the import configuration with the new name
            import_config["name"] = new_name

            # Recursively call this function with the updated import_config
            return update_facets_yaml(yaml_path, import_config)

        click.echo(f"⚠️ Updating existing import with name '{import_config['name']}'")
        facets_data["imports"][i] = import_config

        # Write updated YAML back using the utility function
        return update_facets_yaml_imports(
            yaml_path, import_config, mode="non-interactive"
        )

    # For success cases, return the original result
    return result


def update_facets_yaml_non_interactive(
    yaml_path: str, import_config: Dict[str, Any]
) -> Union[bool, str]:
    """Update the facets.yaml file with the import declaration in non-interactive mode.

    Args:
        yaml_path: Path to the facets.yaml file
        import_config: The import configuration to add

    Returns:
        True if a new import was added, "updated" if an existing import was updated,
        False if the operation failed
    """
    return update_facets_yaml_imports(yaml_path, import_config, mode="non-interactive")
