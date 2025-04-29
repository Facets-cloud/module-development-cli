import click
import yaml
import os
import questionary
import glob
import hcl2
import re
from ftf_cli.utils import validate_facets_yaml


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
def add_import(path, name=None, required=None):
    """Add an import declaration to the module.
    
    This command allows you to add import declarations to the facets.yaml file,
    specifying Terraform resources that should be imported when using the module.
    
    The command will scan the Terraform files in the module directory, identify
    resources, and allow you to select which resources to import. It handles
    resources with count and for_each meta-arguments.
    """
    try:
        # Check if facets.yaml exists
        facets_yaml_path = os.path.join(path, "facets.yaml")
        if not os.path.exists(facets_yaml_path):
            click.echo(f"❌ facets.yaml not found at {facets_yaml_path}")
            return
            
        # Validate facets.yaml format
        try:
            validate_facets_yaml(path)
        except click.UsageError as e:
            click.echo(f"❌ {e}")
            return

        # Discover resources in the module
        click.echo("Discovering resources in the module...")
        resources = discover_resources(path)
        
        if not resources:
            click.echo("❌ No resources found in the module.")
            return
        
        click.echo(f"Found {len(resources)} resources.")
        
        # Prompt user to select a resource
        resource = select_resource(resources)
        if not resource:
            return
        
        # Prompt for import name and required flag
        import_config = configure_import(resource, name, required)
        
        # Validate the import configuration
        if not validate_import_config(import_config):
            click.echo("❌ Invalid import configuration. Aborting.")
            return
        
        # Update the facets.yaml file
        update_facets_yaml(facets_yaml_path, import_config)

    except Exception as e:
        click.echo(f"❌ Error adding import: {e}")


def discover_resources(path):
    """Discover all Terraform resources in the module directory."""
    resources = []
    
    # Find all .tf files in the module directory
    tf_files = glob.glob(os.path.join(path, "*.tf"))
    
    # Track resource addresses to avoid duplicates
    seen_resources = set()
    
    for tf_file in tf_files:
        try:
            with open(tf_file, "r") as file:
                content = hcl2.load(file)
            
            # Extract resource blocks
            if "resource" in content:
                # The resource key contains a list of dictionaries
                for resource_block in content["resource"]:
                    # Each resource_block is a dictionary with a single key (resource type)
                    for resource_type, resources_of_type in resource_block.items():
                        # Skip metadata fields
                        if resource_type.startswith('__') and resource_type.endswith('__'):
                            continue
                            
                        # resources_of_type is a dictionary with resource names as keys
                        for resource_name, resource_config in resources_of_type.items():
                            # Skip metadata fields
                            if resource_name.startswith('__') and resource_name.endswith('__'):
                                continue
                                
                            resource_address = f"{resource_type}.{resource_name}"
                            
                            # Skip if we've already seen this resource
                            if resource_address in seen_resources:
                                continue
                                
                            seen_resources.add(resource_address)
                            
                            # Check for count or for_each
                            has_count = False
                            has_for_each = False
                            count_value = None
                            for_each_value = None
                            
                            # Handle different ways count/for_each might be represented
                            if isinstance(resource_config, dict):
                                if "count" in resource_config:
                                    has_count = True
                                    count_value = resource_config["count"]
                                if "for_each" in resource_config:
                                    has_for_each = True
                                    for_each_value = resource_config["for_each"]
                            elif isinstance(resource_config, list) and resource_config:
                                # If it's a list, check the first item (common HCL2 pattern)
                                first_item = resource_config[0]
                                if isinstance(first_item, dict):
                                    if "count" in first_item:
                                        has_count = True
                                        count_value = first_item["count"]
                                    if "for_each" in first_item:
                                        has_for_each = True
                                        for_each_value = first_item["for_each"]
                            
                            # Add the resource with appropriate metadata
                            if has_count:
                                resources.append({
                                    "address": f"{resource_address}",
                                    "display": f"{resource_address} (with count)",
                                    "indexed": True,
                                    "index_type": "count",
                                    "value": count_value,
                                    "source_file": os.path.basename(tf_file)
                                })
                            elif has_for_each:
                                resources.append({
                                    "address": f"{resource_address}",
                                    "display": f"{resource_address} (with for_each)",
                                    "indexed": True,
                                    "index_type": "for_each",
                                    "value": for_each_value,
                                    "source_file": os.path.basename(tf_file)
                                })
                            else:
                                resources.append({
                                    "address": resource_address,
                                    "display": resource_address,
                                    "indexed": False,
                                    "source_file": os.path.basename(tf_file)
                                })
        except Exception as e:
            click.echo(f"⚠️ Could not parse {tf_file}: {e}")
            click.echo(f"Error details: {str(e)}")
    
    # Sort resources by address for better display
    return sorted(resources, key=lambda r: r["address"])


def select_resource(resources):
    """Prompt the user to select a resource from the list."""
    choices = []
    for r in resources:
        source_info = f" (in {r['source_file']})"
        # choices.append(f"{r['display']}{source_info}")
        choices.append(f"{r['display']}")
    
    selected = questionary.select(
        "Select resource to import:",
        choices=choices
    ).ask()
    
    if not selected:
        click.echo("❌ No resource selected.")
        return None
    
    # Extract the display part from the selected choice by removing the source info
    display_part = selected.split(" (in ")[0]
    
    # Find the matching resource
    for r in resources:
        if r['display'] == display_part:
            return r
    
    # Fallback to index-based lookup if exact match fails
    selected_index = choices.index(selected)
    return resources[selected_index]


def configure_import(resource, name=None, required=None):
    """Configure import details based on user input."""
    # Get resource name from address (e.g., aws_s3_bucket.bucket -> bucket)
    default_name = resource["address"].split(".")[-1]
    
    # Prompt for import name if not provided via CLI
    if name is None:
        name = questionary.text(
            "Import Name:",
            default=default_name,
            validate=lambda text: len(text) > 0 or "Name cannot be empty"
        ).ask()
    
    # Validate name format
    if not re.match(r'^[a-zA-Z0-9_]+$', name):
        click.echo("⚠️ Warning: Import name should only contain alphanumeric characters and underscores.")
        if not questionary.confirm("Continue with this name?", default=False).ask():
            name = questionary.text(
                "Import Name:",
                default=default_name,
                validate=lambda text: len(text) > 0 and re.match(r'^[a-zA-Z0-9_]+$', text) or "Invalid name format"
            ).ask()
    
    # Prompt for required flag if not provided via CLI
    if required is None:
        required = questionary.confirm(
            "Is this import required?",
            default=True
        ).ask()
    
    # Handle indexed resources
    resource_address = resource["address"]
    if resource["indexed"]:
        if resource["index_type"] == "count":
            index_options = ["*", "0", "1", "2", "3", "4", "5", "Custom..."]
            index_choice = questionary.select(
                "Select resource index:",
                choices=index_options
            ).ask()
            
            if index_choice == "Custom...":
                index = questionary.text(
                    "Enter resource index (number or '*' for all):",
                    validate=lambda text: text == "*" or text.isdigit() or "Index must be a number or '*'"
                ).ask()
            else:
                index = index_choice
                
            resource_address = f"{resource_address}[{index}]"
            
        elif resource["index_type"] == "for_each":
            # For for_each, we can't easily predict the keys, so offer a text input
            key = questionary.text(
                "Enter resource key (string, number, or '*' for all):",
                validate=lambda text: len(text) > 0 or "Key cannot be empty"
            ).ask()
            
            if key == "*":
                resource_address = f"{resource_address}[*]"
            elif key.isdigit():
                # If it's a number, no quotes needed
                resource_address = f"{resource_address}[{key}]"
            else:
                # Add quotes for string keys
                resource_address = f"{resource_address}[\"{key}\"]"
    
    return {
        "name": name,
        "resource_address": resource_address,
        "required": required
    }


def validate_import_config(import_config):
    """Validate the import configuration before saving."""
    # Check for required fields
    if not import_config.get("name"):
        click.echo("❌ Import name is required.")
        return False
        
    if not import_config.get("resource_address"):
        click.echo("❌ Resource address is required.")
        return False
    
    # Validate resource address format
    address = import_config["resource_address"]
    if not re.match(r'^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+(\[[^\]]+\])?$', address):
        click.echo(f"❌ Invalid resource address format: {address}")
        return False
    
    return True


def update_facets_yaml(yaml_path, import_config):
    """Update the facets.yaml file with the import declaration."""
    try:
        # Load existing YAML
        with open(yaml_path, "r") as file:
            facets_data = yaml.safe_load(file) or {}
        
        # Add or update imports section
        if "imports" not in facets_data:
            facets_data["imports"] = []
        
        # Check if an import with the same name already exists
        for i, existing_import in enumerate(facets_data["imports"]):
            if existing_import.get("name") == import_config["name"]:
                if not questionary.confirm(
                    f"Import with name '{import_config['name']}' already exists. Update it?",
                    default=True
                ).ask():
                    # User chose not to update, ask if they want to use a different name or quit
                    action = questionary.select(
                        "What would you like to do?",
                        choices=["Enter a different name", "Quit without adding import"]
                    ).ask()
                    
                    if action == "Quit without adding import":
                        click.echo("❌ Import not added. Operation canceled.")
                        return False
                    
                    # User wants to enter a different name
                    new_name = questionary.text(
                        "Enter a new import name:",
                        validate=lambda text: len(text) > 0 or "Name cannot be empty"
                    ).ask()
                    
                    # Validate name format
                    if not re.match(r'^[a-zA-Z0-9_]+$', new_name):
                        click.echo("⚠️ Warning: Import name should only contain alphanumeric characters and underscores.")
                        if not questionary.confirm("Continue with this name?", default=False).ask():
                            new_name = questionary.text(
                                "Enter a new import name:",
                                validate=lambda text: len(text) > 0 and re.match(r'^[a-zA-Z0-9_]+$', text) or "Invalid name format"
                            ).ask()
                    
                    # Update the import configuration with the new name
                    import_config["name"] = new_name
                    
                    # Recursively call this function with the updated import_config
                    return update_facets_yaml(yaml_path, import_config)
                
                click.echo(f"⚠️ Updating existing import with name '{import_config['name']}'")
                facets_data["imports"][i] = import_config
                break
        else:
            # Add new import
            facets_data["imports"].append(import_config)
        
        # Write updated YAML back to file
        with open(yaml_path, "w") as file:
            yaml.dump(facets_data, file, default_flow_style=False, sort_keys=False)
        
        # Provide success message
        click.echo(f"✅ Import declaration added to facets.yaml:")
        click.echo(f"   name: \"{import_config['name']}\"")
        click.echo(f"   resource_address: \"{import_config['resource_address']}\"")
        click.echo(f"   required: {str(import_config['required']).lower()}")
        
        return True
        
    except Exception as e:
        click.echo(f"❌ Error updating facets.yaml: {e}")
        return False 