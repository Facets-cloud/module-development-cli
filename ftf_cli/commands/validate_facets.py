import os
import click
from ftf_cli.utils import validate_facets_yaml

@click.command()
@click.argument('path', type=click.Path(exists=True))
def validate_facets(path):
    """Validate the facets.yaml file within the specified directory."""

    try:
        # Validate the facets.yaml file in the given path
        validate_facets_yaml(path)
        click.echo("✅ facets.yaml validated successfully.")

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        raise e


if __name__ == "__main__":
    validate_facets()
