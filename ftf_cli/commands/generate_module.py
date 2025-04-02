import os
import click
from jinja2 import Environment, FileSystemLoader
import importlib.resources as pkg_resources

@click.command()
@click.argument('path', default=".", type=click.Path(exists=True))
@click.option('-i', '--intent', prompt='Intent', help='The intent of the module.')
@click.option('-f', '--flavor', prompt='Flavor', help='The flavor of the module.')
@click.option('-c', '--cloud', prompt='Cloud', help='The cloud provider for the module.')
@click.option('-t', '--title', prompt='Title', help='The title of the module.')
@click.option('-d', '--description', prompt='Description', help='The description of the module.')
def generate_module(path, intent, flavor, cloud, title, description):
    """Generate a new module."""
    
    module_path = os.path.join(path, f"{intent}/{flavor}/1.0")
    os.makedirs(module_path, exist_ok=True)

    # Setup Jinja2 environment using package resources
    templates_path = pkg_resources.files('ftf_cli.commands.templates')
    env = Environment(loader=FileSystemLoader(str(templates_path)))

    # Render and write templates
    for template_name in ['main.tf.j2', 'variables.tf.j2', 'output.tf.j2', 'facets.yaml.j2']:
        template = env.get_template(template_name)
        rendered_content = template.render(intent=intent, flavor=flavor, cloud=cloud, title=title,
                                           description=description)
        file_name = template_name.replace('.j2', '')  # Remove .j2 to get the real file name
        with open(os.path.join(module_path, file_name), 'w') as f:
            f.write(rendered_content)
    click.echo(f'✅ Module generated at: {module_path}')