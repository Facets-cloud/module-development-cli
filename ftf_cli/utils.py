import os
import re
import configparser
import yaml
import jsonschema
from jsonschema import validate, Draft7Validator
import click
import hcl2
import requests

ALLOWED_TYPES = ['string', 'number', 'boolean', 'enum']


def validate_facets_yaml(path, filename="facets.yaml"):
    """Validate the existence and format of specified facets yaml file in the given path."""
    yaml_path = os.path.join(path, filename)
    if not os.path.isfile(yaml_path):
        raise click.UsageError(f' {filename} file does not exist at {os.path.abspath(yaml_path)}')

    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            validate_yaml(data)

    except yaml.YAMLError as exc:
        raise click.UsageError(f' {filename} is not a valid YAML file: {exc}')

    return yaml_path


def generate_output_tree(obj):
    """ Generate a JSON schema from a output.tf file. """
    if isinstance(obj, dict):
        transformed = {}
        for key, value in obj.items():
            transformed[key] = generate_output_tree(value)
        return transformed
    elif isinstance(obj, list):
        if len(obj) > 0:
            return {"type": "array", "items": generate_output_tree(obj[0])}
        else:
            return {"type": "array"}  # No "items" if unknown
    elif isinstance(obj, bool):
        return {"type": "boolean"}
    elif isinstance(obj, (int, float)):
        return {"type": "number"}
    elif isinstance(obj, str):
        return {"type": "string"}
    else:
        return {"type": "any"}  # Catch unexpected types


def transform_output_tree(tree, level=1):
    """ Recursively transform the output tree into a Terraform-compatible schema with proper indentation."""
    INDENT = "  "  # Fixed indentation (2 spaces)
    current_indent = INDENT * level
    next_indent = INDENT * (level + 1)

    if isinstance(tree, dict):
        if "type" in tree:
            # If the node has a "type", return it directly
            if tree["type"] == "array":
                # Handle arrays with "items"
                if "items" in tree:
                    return f"list({transform_output_tree(tree['items'], level)})"
                else:
                    return "list(any)"
            elif tree["type"] == "object":
                # Handle objects
                return "object({})"
            elif tree["type"] == "boolean":
                # Fix boolean type to bool
                return "bool"
            else:
                return tree["type"]
        else:
            # Recursively process nested dictionaries
            transformed_items = []
            for key, value in tree.items():
                transformed_value = transform_output_tree(value, level + 1)
                transformed_items.append(f"{next_indent}{key} = {transformed_value}")
            
            # Step 1: Join the transformed items with a comma and newline
            joined_items = ',\n'.join(transformed_items)

            # Step 2: Construct the object block with proper indentation
            object_block = f"object({{\n{joined_items}\n{current_indent}}})"

            # Step 3: Return the constructed object block
            return object_block
    elif isinstance(tree, list):
        # Handle arrays
        if len(tree) > 0:
            return f"list({transform_output_tree(tree[0], level)})"
        else:
            return "list(any)"  # Unknown items
    else:
        # Fallback for unexpected types
        return "any"


def load_facets_yaml(path):
    """Load and validate facets.yaml file, returning its content as an object."""
    # Validate the facets.yaml file
    yaml_path = validate_facets_yaml(path)

    # Load YAML content
    with open(yaml_path, 'r') as file:
        content = yaml.safe_load(file)

    return content


def validate_variables_tf(path):
    """Ensure variables.tf exists and is valid HCL."""
    variables_tf_path = os.path.join(path, 'variables.tf')
    if not os.path.isfile(variables_tf_path):
        raise click.UsageError(f' variables.tf file does not exist at {os.path.abspath(variables_tf_path)}')

    try:
        with open(variables_tf_path, 'r') as f:
            hcl2.load(f)
    except Exception as e:
        raise click.UsageError(f' variables.tf is not a valid HCL file: {e}')

    return variables_tf_path


def insert_nested_fields(structure, keys, value):
    """Recursively inserts nested fields into the given dictionary structure."""
    if len(keys) == 1:
        structure[keys[0]] = value
    else:
        if keys[0] not in structure:
            structure[keys[0]] = {}
        insert_nested_fields(structure[keys[0]], keys[1:], value)


def update_spec_variable(terraform_code, variable_name, spec_identifier, new_fields):
    lines = terraform_code.split("\n")
    updated_lines = []
    inside_spec = False
    inside_variable = False
    variable_found = False
    spec_found = False
    existing_structure = {}

    for line in lines:
        stripped = line.strip()

        if stripped.startswith(f'variable "{variable_name}" '):
            inside_variable = True
            variable_found = True

        if inside_variable and stripped.startswith(spec_identifier):
            inside_spec = True
            spec_found = True
            updated_lines.append(line)
            continue

        if inside_spec:
            if stripped == "})":
                inside_spec = False

                # Insert the new fields before closing the spec block
                for key, value in new_fields.items():
                    keys = key.split(".")
                    insert_nested_fields(existing_structure, keys, value)

                def format_structure(structure, indent=4):
                    formatted = []
                    for key, value in sorted(structure.items()):
                        if isinstance(value, dict):
                            formatted.append(" " * indent + f"{key} = object({{")
                            formatted.extend(format_structure(value, indent + 2))
                            formatted.append(" " * indent + "})")
                        else:
                            formatted.append(" " * indent + f"{key} = {value}")
                    return formatted

                updated_lines.extend(format_structure(existing_structure, indent=6))
                updated_lines.append(" " * 4 + "})")
                continue

        updated_lines.append(line)

    if not variable_found:
        raise click.UsageError(f" Variable '{variable_name}' not found in the Terraform file.")

    if not spec_found:
        raise click.UsageError(f" Spec block '{spec_identifier}' not found in the variable '{variable_name}'.")

    return "\n".join(updated_lines)


yaml_schema = {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "flavor": {"type": "string"},
        "version": {"type": "string"},
        "description": {"type": "string"},
        "clouds": {
            "type": "array",
            "items": {"type": "string"}
        },
        "spec": jsonschema.Draft7Validator.META_SCHEMA,
        "outputs": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "pattern": "^@outputs?/.+"},
                        "providers": {
                            "type": "object",
                            "patternProperties": {
                                ".*": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "version": {"type": "string"},
                                        "attributes": {
                                            "type": "object",
                                            "additionalProperties": True
                                        }
                                    },
                                    "required": ["source", "version", "attributes"]
                                }
                            }
                        }
                    },
                    "required": ["type"]
                }
            }
        },
        "inputs": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "pattern": "^@outputs?/.+"},
                        "providers": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["type"]
                }
            }
        },
        "sample": {"type": "object"},
        "artifact_inputs": {
            "type": "object",
            "properties": {
                "primary": {
                    "type": "object",
                    "properties": {
                        "attribute_path": {
                            "type": "string",
                            "pattern": "^spec\.[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]+)*$"
                        },
                        "artifact_type": {
                            "type": "string",
                            "enum": ["docker_image", "freestyle"]
                        }
                    },
                    "required": ["attribute_path", "artifact_type"]
                }
            },
            "required": ["primary"]
        },
        "metadata": jsonschema.Draft7Validator.META_SCHEMA
    },
    "required": ["intent", "flavor", "version", "description", "spec"]
}


def check_no_array_or_invalid_pattern_in_spec(spec_obj, path="spec"):
    """
    Recursively check that no field in spec is of type 'array'.
    Also check that any direct patternProperties have object type only, not primitive types like string.
    Nested properties inside patternProperties can be any allowed types.
    Raises a UsageError with instruction if found.
    Assumes input is always valid JSON schema (no direct list values at property keys).
    """
    if not isinstance(spec_obj, dict):
        return

    for key, value in spec_obj.items():
        if isinstance(value, dict):
            field_type = value.get("type")
            if field_type == "array":
                raise click.UsageError(
                    f'Invalid array type found at {path}.{key}. '
                    f'Arrays are not allowed in spec. Use patternProperties for array-like structures instead.'
                )
            if "patternProperties" in value:
                pp = value["patternProperties"]
                for pattern_key, pp_val in pp.items():
                    pattern_type = pp_val.get("type")
                    if not isinstance(pattern_type, str) or pattern_type != "object":
                        raise click.UsageError(
                            f'patternProperties at {path}.{key} with pattern "{pattern_key}" must be of type object.'
                        )
            check_no_array_or_invalid_pattern_in_spec(value, path=f"{path}.{key}")


def validate_yaml(data):
    try:
        validate(instance=data, schema=yaml_schema)
        # Additional check for arrays and invalid patternProperties in spec
        spec_obj = data.get("spec")
        if spec_obj:
            check_no_array_or_invalid_pattern_in_spec(spec_obj)
    except jsonschema.exceptions.ValidationError as e:
        print(e)
        raise click.UsageError(f' facets.yaml is not following Facets Schema: {e.message}')
    print("Facets YAML validation successful!")
    return True


def fetch_user_details(cp_url, username, token):
    return requests.get(f'{cp_url}/api/me', auth=(username, token))


def store_credentials(profile, credentials):
    config = configparser.ConfigParser()
    cred_path = os.path.expanduser('~/.facets/credentials')
    os.makedirs(os.path.dirname(cred_path), exist_ok=True)

    if os.path.exists(cred_path):
        config.read(cred_path)

    config[profile] = credentials

    with open(cred_path, 'w') as configfile:
        config.write(configfile)


def is_logged_in(profile):
    config = configparser.ConfigParser()
    cred_path = os.path.expanduser('~/.facets/credentials')

    if not os.path.exists(cred_path):
        click.echo('Credentials file not found. Please login first.')
        return False

    config.read(cred_path)
    if profile not in config:
        click.echo(f'Profile {profile} not found. Please login using this profile.')
        return False

    try:
        credentials = config[profile]
        response = fetch_user_details(credentials['control_plane_url'], credentials['username'], credentials['token'])
        response.raise_for_status()
        click.echo('Successfully authenticated with the control plane.')
        return credentials  # Return credentials if login is successful
    except requests.exceptions.HTTPError as http_err:
        click.echo(f'HTTP error occurred: {http_err}')
        return False
    except KeyError as key_err:
        click.echo(f'Missing credential information: {key_err}')
        raise click.UsageError('Incomplete credentials found in profile. Please re-login.')
    except Exception as err:
        click.echo(f'An error occurred: {err}')
        return False

def validate_boolean(ctx, param, value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', 'yes', '1'):
        return True
    elif value.lower() in ('false', 'no', '0'):
        return False
    else:
        raise click.BadParameter("Boolean flag must be true or false.")

if __name__ == "__main__":
    sample_terraform_code = """
variable "example_variable" {
  type = object({
    spec = object({
      cpu    = number
      memory = number
    })
  })
}
    """

    test_cases = [
        {"gpu": "number"},
        {"disk.size": "number", "disk.type": "string"},
        {"network.vpc": "string", "network.subnet": "string"},
    ]

    for i, new_fields in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        updated_code = update_spec_variable(sample_terraform_code, "example_variable", "spec =", new_fields)
        print(updated_code)
        print("\n" + "-" * 50 + "\n")
