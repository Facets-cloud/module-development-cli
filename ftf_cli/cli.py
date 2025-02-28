import click
from ftf_cli.commands.generate_module import generate_module
from ftf_cli.commands.add_variable import add_variable
from ftf_cli.commands.validate_directory import validate_directory


@click.group()
def cli():
    """FTF CLI command entry point."""
    pass


cli.add_command(generate_module)
cli.add_command(add_variable)
cli.add_command(validate_directory)
