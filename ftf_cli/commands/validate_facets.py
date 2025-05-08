import click
from ftf_cli.utils import validate_facets_yaml


@click.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "--filename",
    default="facets.yaml",
    help="Name of the facets YAML file to validate.",
)
def validate_facets(path, filename):
    """Validate the facets YAML file within the specified directory."""

    try:
        # Validate the specified facets yaml file in given path
        validate_facets_yaml(path, filename)
        click.echo(f"✅ {filename} validated successfully.[0m")

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}[0m")
        raise e


if __name__ == "__main__":
    validate_facets()
