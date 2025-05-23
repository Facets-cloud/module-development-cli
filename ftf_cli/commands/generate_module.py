import os
import click
from jinja2 import Environment, FileSystemLoader
import importlib.resources as pkg_resources


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("-i", "--intent", prompt="Intent", help="The intent of the module.")
@click.option("-f", "--flavor", prompt="Flavor", help="The flavor of the module.")
@click.option(
    "-c", "--cloud", prompt="Cloud", help="The cloud provider for the module."
)
@click.option("-t", "--title", prompt="Title", help="The title of the module.")
@click.option(
    "-d", "--description", prompt="Description", help="The description of the module."
)
@click.option(
    "-v",
    "--version",
    default="1.0",
    help="The version of the module. If not provided, the default version will be 1.0. and the module will increment the version number.",
)
def generate_module(path, intent, flavor, cloud, title, description, version):
    """Generate a new module."""
    if str(version).isdigit():
        raise click.UsageError(
            f"❌ Version {version} is not a valid version. Use a valid version like 1.0"
        )

    base_module_path = os.path.join(path, f"{intent}/{flavor}")
    module_path = os.path.join(base_module_path, version)

    # If the version already exists, increment until we find an available one
    if os.path.exists(module_path):
        try:
            base_version = float(version)
            next_version = base_version
            while os.path.exists(os.path.join(base_module_path, str(next_version))):
                next_version = round(
                    next_version + 0.1, 1
                )  # Round to avoid floating point issues
            version = str(next_version)
            module_path = os.path.join(base_module_path, version)
            raise click.UsageError(
                f"❌ Version {base_version} already exists. Use this version {version} instead."
            )
        except ValueError:
            raise click.UsageError(
                f"❌ Version {version.split('_')[0]} already exists. Use this version {version} instead."
            )

    # Create the directory
    os.makedirs(module_path, exist_ok=True)

    # Setup Jinja2 environment using package resources
    templates_path = pkg_resources.files("ftf_cli.commands.templates")
    env = Environment(loader=FileSystemLoader(str(templates_path)))

    # Render and write templates
    for template_name in [
        "main.tf.j2",
        "variables.tf.j2",
        "outputs.tf.j2",
        "facets.yaml.j2",
    ]:
        template = env.get_template(template_name)
        rendered_content = template.render(
            intent=intent,
            flavor=flavor,
            cloud=cloud,
            title=title,
            description=description,
        )
        file_name = template_name.replace(
            ".j2", ""
        )  # Remove .j2 to get the real file name
        with open(os.path.join(module_path, file_name), "w", encoding='utf-8') as f:
            f.write(rendered_content)
    click.echo(f"✅ Module generated at: {module_path}")
