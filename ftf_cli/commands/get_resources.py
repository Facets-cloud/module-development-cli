import click
from ftf_cli.utils import discover_resources


@click.command()
@click.argument("path", type=click.Path(exists=True))
def get_resources(path):
    """List all Terraform resources in the given module directory."""
    resources = discover_resources(path)
    if not resources:
        click.echo("No resources found in the module.")
        return
    click.echo(f"Found {len(resources)} resources:")
    for r in resources:
        # Show address and display info (e.g., with count/for_each)
        click.echo(f"- {r['display']}")
