import configparser
import os
import re
import jsonschema
from jsonschema import validate, Draft7Validator
import click
import requests


ALLOWED_TYPES = ['string', 'number', 'integer', 'boolean', 'array', 'object', 'enum']


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


def insert_nested_fields(existing_structure, keys, value):
    """Recursively inserts nested fields within an object structure"""
    if len(keys) == 1:
        existing_structure[keys[0]] = value
    else:
        if keys[0] not in existing_structure or not isinstance(existing_structure[keys[0]], dict):
            existing_structure[keys[0]] = {}
        insert_nested_fields(existing_structure[keys[0]], keys[1:], value)


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

        if stripped.startswith(f"variable \"{variable_name}\" "):
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

                def format_structure(structure, indent=6):
                    formatted = []
                    for key, value in structure.items():
                        if isinstance(value, dict):
                            formatted.append(" " * indent + f"{key} = object({{")
                            formatted.extend(format_structure(value, indent + 2))
                            formatted.append(" " * indent + "})")
                        else:
                            formatted.append(" " * indent + f"{key} = {value}")
                    return formatted

                updated_lines.extend(format_structure(existing_structure))

            else:
                parts = stripped.split("=")
                if len(parts) > 1:
                    key = parts[0].strip()
                    existing_structure[key] = {}

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
        "spec": jsonschema.Draft7Validator.META_SCHEMA,
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
                                            "patternProperties": {
                                                ".*": {"type": "string"}
                                            }
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
        raise click.UsageError(f'❌ facets.yaml is not a following Facets Schema: {e.message}')
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
        return True
    except requests.exceptions.HTTPError as http_err:
        click.echo(f'HTTP error occurred: {http_err}')
        return False
    except KeyError as key_err:
        click.echo(f'Missing credential information: {key_err}')
        raise click.UsageError('Incomplete credentials found in profile. Please re-login.')
    except Exception as err:
        click.echo(f'An error occurred: {err}')
        return False
