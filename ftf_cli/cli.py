import click
from ftf_cli.commands.generate_module import generate_module
from ftf_cli.commands.add_variable import add_variable
from ftf_cli.commands.login import login
from ftf_cli.commands.validate_directory import validate_directory
from ftf_cli.commands.preview_module import preview_module
from ftf_cli.commands.expose_provider import expose_provider
from ftf_cli.commands.add_input import add_input


@click.group()
def cli():
    """FTF CLI command entry point."""
    pass


cli.add_command(generate_module)
cli.add_command(add_variable)
cli.add_command(validate_directory)
cli.add_command(login)
cli.add_command(preview_module)
cli.add_command(expose_provider)
cli.add_command(add_input)
