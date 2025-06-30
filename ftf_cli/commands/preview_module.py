import os
import click
import getpass
import yaml
import hcl2
import json
from ftf_cli.utils import (
    is_logged_in,
    validate_boolean,
    generate_output_lookup_tree,
    get_profile_with_priority,
    generate_output_tree,
)
from ftf_cli.commands.validate_directory import validate_directory
from ftf_cli.operations import register_module, publish_module, ModuleOperationError


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-p",
    "--profile",
    default=get_profile_with_priority(),
    help="The profile name to use (defaults to the current default profile)",
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
@click.option(
    "--skip-output-write",
    default=False,
    callback=validate_boolean,
    is_flag=False,
    help="Do not update the output type in facets. Set to true only if you have already registered the output type before calling this command.",
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
    skip_output_write,
):
    """Register a module at the specified path using the given or default profile."""

    def parse_outputs_tf(path):
        output_file = os.path.join(path, "outputs.tf")
        if not os.path.exists(output_file):
            return None
        with open(output_file, "r", encoding="utf-8") as file:
            parsed = hcl2.load(file)
        return parsed

    def extract_output_structures(parsed_outputs):
        locals_list = parsed_outputs.get("locals")
        if isinstance(locals_list, list) and locals_list:
            locals_ = locals_list[0]
        elif isinstance(locals_list, dict):
            locals_ = locals_list
        else:
            locals_ = {}

        output_interfaces = locals_.get("output_interfaces", {})
        if isinstance(output_interfaces, list) and output_interfaces:
            output_interfaces = output_interfaces[0]
        elif not isinstance(output_interfaces, dict):
            output_interfaces = {}

        output_attributes = locals_.get("output_attributes", {})
        if isinstance(output_attributes, list) and output_attributes:
            output_attributes = output_attributes[0]
        elif not isinstance(output_attributes, dict):
            output_attributes = {}

        return output_interfaces, output_attributes

    def write_output_lookup_tree(path, output_interfaces, output_attributes):
        output_json_path = os.path.join(path, "output-lookup-tree.json")
        output = {
            "out": {
                "attributes": output_attributes,
                "interfaces": output_interfaces,
            }
        }
        transformed_output = generate_output_lookup_tree(output)
        with open(output_json_path, "w", encoding="utf-8") as file:
            json.dump(transformed_output, file, indent=4)
        return output_json_path

    def write_output_facets_yaml(path, output_interfaces, output_attributes):
        output_facets_file = os.path.join(path, "output.facets.yaml")
        interfaces_schema = generate_output_tree(output_interfaces)
        attributes_schema = generate_output_tree(output_attributes)
        out_schema = {
            "interfaces": interfaces_schema,
            "attributes": attributes_schema,
        }
        with open(output_facets_file, "w", encoding="utf-8") as f:
            yaml.dump({"out": out_schema}, f, sort_keys=False)
        return output_facets_file

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
    with open(yaml_file, "r", encoding="utf-8") as file:
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
        with open(yaml_file, "w", encoding="utf-8") as file:
            yaml.dump(facets_data, file, sort_keys=False)

    # Write the updated facets.yaml with validated files
    with open(yaml_file, "w", encoding="utf-8") as file:
        yaml.dump(facets_data, file, sort_keys=False)

    control_plane_url = credentials["control_plane_url"]
    username = credentials["username"]
    token = credentials["token"]

    intent = facets_data.get("intent", "unknown")
    flavor = facets_data.get("flavor", "unknown")

    click.echo(f"Auto-create intent: {auto_create_intent}")
    click.echo(f"Module marked as publishable: {publishable}")
    if git_repo_url:
        click.echo(f"Git repository URL: {git_repo_url}")
    click.echo(f"Git reference: {git_ref}")

    success_message = f'[PREVIEW] Module with Intent "{intent}", Flavor "{flavor}", and Version "{facets_data["version"]}" successfully previewed to {control_plane_url}'

    output_json_path = None
    output_facets_path = None
    parsed_outputs = parse_outputs_tf(path)
    output_interfaces = None
    output_attributes = None
    if parsed_outputs:
        output_interfaces, output_attributes = extract_output_structures(parsed_outputs)
    try:
        # Generate the output lookup tree if outputs.tf exists
        if output_interfaces is not None and output_attributes is not None:
            try:
                output_json_path = write_output_lookup_tree(path, output_interfaces, output_attributes)
                click.echo(f"Output lookup tree saved to {output_json_path}")
            except Exception as e:
                click.echo(f"Error generating output lookup tree: {e}")
        else:
            output_json_path = None
            if parse_outputs_tf(path) is None:
                click.echo(f"Warning: {os.path.join(path, 'outputs.tf')} not found. Skipping output tree generation.")

        # Generate output.facets.yaml if needed
        output_facets_file = os.path.join(path, "output.facets.yaml")
        if not skip_output_write and output_interfaces is not None and output_attributes is not None:
            if not os.path.exists(output_facets_file):
                try:
                    output_facets_path = write_output_facets_yaml(path, output_interfaces, output_attributes)
                    click.echo(f"output.facets.yaml saved to {output_facets_path}")
                except Exception as e:
                    click.echo(f"Error generating output.facets.yaml: {e}")
            else:
                click.echo("output.facets.yaml already exists, skipping generation.")

        # Register the module
        register_module(
            control_plane_url=control_plane_url,
            username=username,
            token=token,
            path=path,
            git_url=git_repo_url,
            git_ref=git_ref,
            is_feature_branch=(not publishable and not publish),
            auto_create=auto_create_intent,
            skip_output_write=skip_output_write,
        )

        click.echo("✔ Module preview successfully registered.")
        click.echo(f"\n\n✔✔✔ {success_message}\n")

    except ModuleOperationError as e:
        raise click.UsageError(f"❌ Failed to register module for preview: {e}")
    finally:
        # Revert version back to original after attempting registration
        if is_local_develop:
            facets_data["version"] = original_version
            facets_data["sample"]["version"] = original_sample_version
            with open(yaml_file, "w", encoding="utf-8") as file:
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
        # Remove output.facets.yaml if it was generated
        if output_facets_path and os.path.exists(output_facets_path):
            try:
                os.remove(output_facets_path)
                click.echo(f"Removed temporary file: {output_facets_path}")
            except Exception as e:
                click.echo(f"Warning: Failed to remove temporary file {output_facets_path}: {e}")

    success_message_published = f'[PUBLISH] Module with Intent "{intent}", Flavor "{flavor}", and Version "{facets_data["version"]}" successfully published to {control_plane_url}'

    try:
        if publish:
            if is_local_develop:
                raise click.UsageError(
                    "❌ Cannot publish a local development module, please provide GIT_REF and GIT_REPO_URL"
                )

            # Publish the module
            publish_module(
                control_plane_url=control_plane_url,
                username=username,
                token=token,
                intent=intent,
                flavor=flavor,
                version=original_version,
            )

            click.echo(f"\n\n✔✔✔ {success_message_published}\n")

    except ModuleOperationError as e:
        raise click.UsageError(f"❌ Failed to Publish module: {e}")


if __name__ == "__main__":
    preview_module()
