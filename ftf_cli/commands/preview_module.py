import os
import click
from ftf_cli.utils import is_logged_in
from ftf_cli.commands.validate_directory import validate_directory
import subprocess
import getpass

@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-p', '--profile', default=lambda: os.getenv('FACETS_PROFILE', 'default'), help='The profile name to use or defaults to environment variable FACETS_PROFILE if set')
@click.option('-a', '--auto-create-intent', is_flag=True, default=False, help='Automatically create intent if not exists')
@click.option('-f', '--publishable', is_flag=True, default=False, help='Mark the module as publishable for production. Default is for development and testing (use false).')
@click.option('-g', '--git-repo-url', default=lambda: os.getenv('GIT_REPO_URL'), help='The Git repository URL, defaults to environment variable GIT_REPO_URL if set')
@click.option('-r', '--git-ref', default=lambda: os.getenv('GIT_REF', f'local-{getpass.getuser()}'), help='The Git reference, defaults to environment variable GIT_REF if set, or local user name')
def preview_module(path, profile, auto_create_intent, publishable, git_repo_url, git_ref):
    """Register a module at the specified path using the given or default profile."""

    click.echo(f'Profile selected: {profile}')

    credentials = is_logged_in(profile)
    if not credentials:
        click.echo(f'❌ Not logged in under profile {profile}. Please login first.')
        return

    click.echo(f'Validating directory at {path}...')

    # Validate the directory before proceeding
    ctx = click.Context(validate_directory)
    ctx.params['path'] = path
    ctx.params['check_only'] = False  # Set default for check_only
    validate_directory.invoke(ctx)

    # Extract credentials
    control_plane_url = credentials['control_plane_url']
    username = credentials['username']
    token = credentials['token']

    # Preparing the command for registration
    click.echo('Preparing registration command...')

    command = [
        "curl", "-s", "https://facets-cloud.github.io/facets-schemas/scripts/module_register.sh", "|", "bash", "-s", "--",
        "-c", control_plane_url,
        "-u", username,
        "-t", token
    ]

    # Add the auto-create-intent flag if set
    if auto_create_intent:
        command.append("-a")
    
    click.echo(f'Auto-create intent: {auto_create_intent}')

    # Add the publishable flag if set
    if publishable:
        command.append("-f")

    click.echo(f'Module marked as publishable: {publishable}')

    # Add GIT_REPO_URL if set
    if git_repo_url:
        command.extend(["-g", git_repo_url])
        click.echo(f'Git repository URL: {git_repo_url}')
    
    # Add GIT_REF
    command.extend(["-r", git_ref])
    click.echo(f'Git reference: {git_ref}')

    try:
        subprocess.run(' '.join(command), shell=True, check=True)
        click.echo('✔ Module preview successfully registered.')
    except subprocess.CalledProcessError as e:
        click.echo(f'❌ Failed to register module for preview: {e}')

    click.echo(f'Previewing module at {path} with profile {profile}.')


if __name__ == "__main__":
    preview_module()
