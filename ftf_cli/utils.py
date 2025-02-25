import os
import re

import click
import yaml
import hcl2

ALLOWED_TYPES = ['string', 'number', 'integer', 'boolean', 'array', 'object', 'enum']


def validate_facets_yaml(path):
    """Validate the existence and format of the facets.yaml file."""
    yaml_path = os.path.join(path, 'facets.yaml')
    if not os.path.isfile(yaml_path):
        raise click.UsageError(f'facets.yaml file does not exist at {os.path.abspath(yaml_path)}')

    try:
        with open(yaml_path, 'r') as f:
            yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise click.UsageError(f'facets.yaml is not a valid YAML file: {exc}')

    return yaml_path


def validate_variables_tf(path):
    """Ensure variables.tf exists and is valid HCL."""
    variables_tf_path = os.path.join(path, 'variables.tf')
    if not os.path.isfile(variables_tf_path):
        raise click.UsageError(f'variables.tf file does not exist at {os.path.abspath(variables_tf_path)}')

    try:
        with open(variables_tf_path, 'r') as f:
            hcl2.load(f)
    except Exception as e:
        raise click.UsageError(f'variables.tf is not a valid HCL file: {e}')

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
        raise ValueError(f"Variable '{variable_name}' not found in the Terraform file.")

    if not spec_found:
        raise ValueError(f"Spec block '{spec_identifier}' not found in the variable '{variable_name}'.")

    return "\n".join(updated_lines)
