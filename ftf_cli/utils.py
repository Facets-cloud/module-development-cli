import os
import yaml
import click

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


def is_valid_facets_yaml(directory):
    """
    Check if a valid facets.yaml exists in the specified directory.
    Returns:
        bool: True if facets.yaml exists and is valid, False otherwise.
    """
    filepath = os.path.join(directory, 'facets.yaml')
    if not os.path.exists(filepath):
        return False

    try:
        with open(filepath, 'r') as file:
            data = yaml.safe_load(file)
            # Basic validation logic based on expected keys
            return 'intent' in data and 'flavor' in data and 'spec' in data
    except Exception:
        return False
    return True
