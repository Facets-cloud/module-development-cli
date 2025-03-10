import click
import os
import yaml
from ftf_cli.utils import validate_facets_yaml, validate_variables_tf, ALLOWED_TYPES, update_spec_variable


@click.command()
@click.option('-n', '--name', prompt='Variable Name (dot-separated for nested)', type=str,
              help='Name allowing nested dot-separated variants.')
@click.option('-t', '--type', prompt='Variable Type', type=str, help='Given base JSON schema type.')
@click.option('-d', '--description', prompt='Variable Description', type=str, help='Provides a description for the variable.')
@click.option('--options', prompt='If type is enum add comma separated values', default='', help='For enums, offer aggregate option hierarchy.')
@click.argument('path', type=click.Path(exists=True))
def add_variable(name, type, description, options, path):
    """Add a new variable to the module."""
    # Validate the facets.yaml file in the given path
    try:
        yaml_path = validate_facets_yaml(path)

        # Validate the variables.tf file
        variables_tf_path = validate_variables_tf(path)

        # Check against allowed types
        if type not in ALLOWED_TYPES:
            raise click.UsageError(f"❌ Type '{type}' is not allowed. Must be one of: {', '.join(ALLOWED_TYPES)}.")

        # Prepare variable schema entry for facets.yaml
        variable_schema = {
            'type': 'string' if type == 'enum' else type,
            'description': description
        }

        if type == 'enum':
            if not options:
                raise click.UsageError("❌ Options must be specified for enum type.")
            variable_schema['enum'] = options.split(',')

        # Load existing YAML data
        with open(yaml_path, 'r') as yaml_file:
            data = yaml.safe_load(yaml_file) or {}

        # Ensure 'spec' and 'properties' sections
        if 'spec' not in data or not data['spec']:
            data['spec'] = {'type': 'object', 'properties': {}}
        if 'properties' not in data['spec'] or data['spec']['properties'] is None:
            data['spec']['properties'] = {}

        # Add the variable schema to the spec
        keys = name.split('.')
        sub_data = data['spec']['properties']
        for key in keys[:-1]:
            if key not in sub_data or sub_data[key] is None:
                sub_data[key] = {'type': 'object', 'properties': {}}
            sub_data = sub_data[key]['properties']
        sub_data[keys[-1]] = variable_schema

        # Save changes back to the facets.yaml file
        with open(yaml_path, 'w') as yaml_file:
            yaml.dump(data, yaml_file)

        with open(variables_tf_path, "r") as file:
            terraform_code = file.read()

        updated_code = update_spec_variable(terraform_code, "instance", "spec", {
            name: 'string' if type == 'enum' else type,
        })

        with open(variables_tf_path, "w") as file:
            file.write(updated_code)

        click.echo(f"✅ Variable '{name}' of type '{type}' added with description '{description}' in path '{path}'.")

    except click.UsageError as ue:
        click.echo(ue.message)
