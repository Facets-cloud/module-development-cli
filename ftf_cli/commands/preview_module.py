import os
import click
from ftf_cli.utils import is_logged_in, validate_boolean, generate_output_lookup_tree
from ftf_cli.commands.validate_directory import validate_directory

import subprocess
import getpass
import yaml
import hcl2
import json

@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-p",
    "--profile",
    default=lambda: os.getenv("FACETS_PROFILE", "default"),
    help="The profile name to use or defaults to environment variable FACETS_PROFILE if set",
)
@click.option(
    "-a",
    "--auto-create-intent",
    default=False,
    callback=validate_boolean,
    help="Automatically create intent if not exists",
)
@click.option(
    "-f",
    "--publishable",
    default=False,
    callback=validate_boolean,
    help="Mark the module as publishable for production. Default is for development and testing (use false).",
)
@click.option(
    "-g",
    "--git-repo-url",
    default=lambda: os.getenv("GIT_REPO_URL"),
    help="The Git repository URL, defaults to environment variable GIT_REPO_URL if set",
)
@click.option(
    "-r",
    "--git-ref",
    default=lambda: os.getenv("GIT_REF", f"local-{getpass.getuser()}"),
    help="The Git reference, defaults to environment variable GIT_REF if set, or local user name",
)
@click.option(
    "--publish",
    default=False,
    callback=validate_boolean,
    help="Publish the module after preview if set.",
)
@click.option(
    "--skip-terraform-validation",
    default=False,
    callback=validate_boolean,
    help="Skip Terraform validation steps if set to true.",
)
def preview_module(
    path,
    profile,
    auto_create_intent,
    publishable,
    git_repo_url,
    git_ref,
    publish,
    skip_terraform_validation,
):
    """Register a module at the specified path using the given or default profile."""

    def generate_and_write_output_tree(path):
        output_file = os.path.join(path, "outputs.tf")
        output_json_path = os.path.join(path, "output-lookup-tree.json")

        # Check if outputs.tf exists
        if not os.path.exists(output_file):
            click.echo(
                f"Warning: {output_file} not found. Skipping output tree generation."
            )
            return None

        try:
            with open(output_file, "r") as file:
                dict = hcl2.load(file)

            locals = dict.get("locals", [{}])[0]
            output_interfaces = locals.get("output_interfaces", [{}])[0]
            output_attributes = locals.get("output_attributes", [{}])[0]

            output = {
                "out": {
                    "attributes": output_attributes,
                    "interfaces": output_interfaces,
                }
            }

            transformed_output = generate_output_lookup_tree(output)

            # Save the transformed output to output-lookup-tree.json
            with open(output_json_path, "w") as file:
                json.dump(transformed_output, file, indent=4)

            click.echo(f"Output lookup tree saved to {output_json_path}")
            return output_json_path

        except Exception as e:
            click.echo(f"Error processing {output_file}: {e}")
            return None

    click.echo(f"Profile selected: {profile}")

    credentials = is_logged_in(profile)
    if not credentials:
        raise click.UsageError(
            f"❌ Not logged in under profile {profile}. Please login first."
        )

    click.echo(f"Validating directory at {path}...")

    # Validate the directory before proceeding
    ctx = click.Context(validate_directory)
    ctx.params["path"] = path
    ctx.params["check_only"] = False  # Set default for check_only
    ctx.params["skip_terraform_validation"] = skip_terraform_validation
    try:
        validate_directory.invoke(ctx)
    except click.ClickException as e:
        raise click.UsageError(f"❌ Validation failed: {e}")

    # Warn if GIT_REPO_URL and GIT_REF are considered local
    if not git_repo_url:
        click.echo(
            "\n\n\n⚠️  CI related env vars: GIT_REPO_URL and GIT_REF not set. Assuming local testing.\n\n"
        )

    # Load facets.yaml and modify if necessary
    yaml_file = os.path.join(path, "facets.yaml")
    with open(yaml_file, "r") as file:
        facets_data = yaml.safe_load(file)

    original_version = facets_data.get("version", "1.0")
    original_sample_version = facets_data.get("sample", {}).get("version", "1.0")
    is_local_develop = git_ref.startswith("local-")
    # Modify version if git_ref indicates local environment
    if is_local_develop:
        new_version = f"{original_version}-{git_ref}"
        facets_data["version"] = new_version

        new_sample_version = f"{original_sample_version}-{git_ref}"
        facets_data["sample"]["version"] = new_sample_version

        click.echo(f"Version modified to: {new_version}")
        click.echo(f"Sample version modified to: {new_sample_version}")

        # Write modified version back to facets.yaml
        with open(yaml_file, "w") as file:
            yaml.dump(facets_data, file, sort_keys=False)

    # Write the updated facets.yaml with validated files
    with open(yaml_file, "w") as file:
        yaml.dump(facets_data, file, sort_keys=False)

    control_plane_url = credentials["control_plane_url"]
    username = credentials["username"]
    token = credentials["token"]

    intent = facets_data.get("intent", "unknown")
    flavor = facets_data.get("flavor", "unknown")

    # Preparing the command for registration
    click.echo("Preparing registration command...")

    command = [
        "curl",
        "-s",
        "https://facets-cloud.github.io/facets-schemas/scripts/module_register.sh",
        "|",
        "bash",
        "-s",
        "--",
        "-c",
        control_plane_url,
        "-u",
        username,
        "-t",
        token,
        "-p",
        path,
    ]

    # Add the auto-create-intent flag if set
    if auto_create_intent:
        command.append("-a")

    click.echo(f"Auto-create intent: {auto_create_intent}")

    # Add the publishable flag if set
    if not publishable and not publish:
        command.append("-f")

    click.echo(f"Module marked as publishable: {publishable}")

    # Add GIT_REPO_URL if set
    if git_repo_url:
        command.extend(["-g", git_repo_url])
        click.echo(f"Git repository URL: {git_repo_url}")

    # Add GIT_REF
    command.extend(["-r", git_ref])
    click.echo(f"Git reference: {git_ref}")

    success_message = f'[PREVIEW] Module with Intent "{intent}", Flavor "{flavor}", and Version "{facets_data["version"]}" successfully previewed to {control_plane_url}'

    output_json_path = None
    try:
        # Generate the output tree and get the path to the generated file
        output_json_path = generate_and_write_output_tree(path)

        # Execute the command
        process = subprocess.run(
            " ".join(command), shell=True, capture_output=True, text=True, check=True
        )
        # Echo each line of the output using click.echo
        for line in process.stdout.splitlines():
            click.echo(line)
        click.echo("✔ Module preview successfully registered.")
        click.echo(f"\n\n✔✔✔ {success_message}\n")
    except subprocess.CalledProcessError as e:
        # Echo any error output
        if e.stdout:
            for line in e.stdout.splitlines():
                click.echo(line)
        if e.stderr:
            for line in e.stderr.splitlines():
                click.echo(line)
        raise click.UsageError(f"❌ Failed to register module for preview: {e}")
    finally:
        # Revert version back to original after attempting registration
        if is_local_develop:
            facets_data["version"] = original_version
            facets_data["sample"]["version"] = original_sample_version
            with open(yaml_file, "w") as file:
                yaml.dump(facets_data, file, sort_keys=False)
            click.echo(f"Version reverted to: {original_version}")
            click.echo(f"Sample version reverted to: {original_sample_version}")

        # Remove the output-lookup-tree.json file if it exists
        if output_json_path and os.path.exists(output_json_path):
            try:
                os.remove(output_json_path)
                click.echo(f"Removed temporary file: {output_json_path}")
            except Exception as e:
                click.echo(
                    f"Warning: Failed to remove temporary file {output_json_path}: {e}"
                )

    success_message_published = f'[PUBLISH] Module with Intent "{intent}", Flavor "{flavor}", and Version "{facets_data["version"]}" successfully published to {control_plane_url}'
    publish_command = [
        "curl",
        "-s",
        "https://facets-cloud.github.io/facets-schemas/scripts/module_publish.sh",
        "|",
        "bash",
        "-s",
        "--",
        "-c",
        control_plane_url,
        "-u",
        username,
        "-t",
        token,
        "-i",
        intent,
        "-f",
        flavor,
        "-v",
        original_version,
    ]
    try:
        if publish:
            if is_local_develop:
                raise click.UsageError(
                    "❌ Cannot publish a local development module, please provide GIT_REF and GIT_REPO_URL"
                )
            process = subprocess.run(
                " ".join(publish_command),
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )

            # Echo each line of the output
            for line in process.stdout.splitlines():
                click.echo(line)

            click.echo(f"\n\n✔✔✔ {success_message_published}\n")
    except subprocess.CalledProcessError as e:
        # Echo any error output
        if e.stdout:
            for line in e.stdout.splitlines():
                click.echo(line)
        if e.stderr:
            for line in e.stderr.splitlines():
                click.echo(line)
        raise click.UsageError(f"❌ Failed to Publish module: {e}")


if __name__ == "__main__":
    preview_module()
