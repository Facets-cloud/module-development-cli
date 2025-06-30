import click
from ftf_cli.commands.generate_module import generate_module
from ftf_cli.commands.add_variable import add_variable
from ftf_cli.commands.login import login
from ftf_cli.commands.validate_directory import validate_directory
from ftf_cli.commands.preview_module import preview_module
from ftf_cli.commands.expose_provider import expose_provider
from ftf_cli.commands.add_input import add_input
from ftf_cli.commands.delete_module import delete_module
from ftf_cli.commands.get_output_types import get_output_types
from ftf_cli.commands.get_output_type_details import get_output_type_details
from ftf_cli.commands.validate_facets import validate_facets
from ftf_cli.commands.register_output_type import register_output_type
from ftf_cli.commands.add_import import add_import
from ftf_cli.commands.get_resources import get_resources


@click.group()
def cli():
    """FTF CLI command entry point."""
    pass


cli.add_command(add_import)
cli.add_command(add_input)
cli.add_command(add_variable)
cli.add_command(delete_module)
cli.add_command(expose_provider)
cli.add_command(generate_module)
cli.add_command(get_output_types)
cli.add_command(get_output_type_details)
cli.add_command(login)
cli.add_command(preview_module)
cli.add_command(register_output_type)
cli.add_command(validate_directory)
cli.add_command(validate_facets)
cli.add_command(get_resources)
