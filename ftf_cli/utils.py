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


def validate_facets_yaml(path):
    """Validate the existence and format of the facets.yaml file."""
    yaml_path = os.path.join(path, 'facets.yaml')
    if not os.path.isfile(yaml_path):
        raise click.UsageError(f'❌ facets.yaml file does not exist at {os.path.abspath(yaml_path)}')

    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            validate_yaml(data)

    except yaml.YAMLError as exc:
        raise click.UsageError(f'❌ facets.yaml is not a valid YAML file: {exc}')


    return yaml_path


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
        raise click.UsageError(f'❌ variables.tf file does not exist at {os.path.abspath(variables_tf_path)}')

    try:
        with open(variables_tf_path, 'r') as f:
            hcl2.load(f)
    except Exception as e:
        raise click.UsageError(f'❌ variables.tf is not a valid HCL file: {e}')

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
        raise click.UsageError(f"❌ Variable '{variable_name}' not found in the Terraform file.")

    if not spec_found:
        raise click.UsageError(f"❌ Spec block '{spec_identifier}' not found in the variable '{variable_name}'.")

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
        "spec": {},
        "outputs": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "pattern": "^@outputs/.+"},
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
                        "type": {"type": "string", "pattern": "^@outputs/.+"},
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
                        "attribute_path": {"type": "string"},
                        "artifact_type": {"type": "string", "enum": ["docker_image"]
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


def validate_yaml(data):
    try:
        validate(instance=data, schema=yaml_schema)
    except jsonschema.exceptions.ValidationError as e:
        print(e)
        raise click.UsageError(f'❌ facets.yaml is not following Facets Schema: {e.message}')
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
