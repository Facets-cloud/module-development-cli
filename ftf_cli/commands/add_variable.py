import click
import os
import yaml
from ftf_cli.utils import (
    validate_facets_yaml,
    validate_variables_tf,
    ALLOWED_TYPES,
    update_spec_variable,
    validate_number,
)


@click.command()
@click.option(
    "-n",
    "--name",
    prompt="Variable Name (dot-separated for nested)",
    type=str,
    help="Name allowing nested dot-separated variants. Use {{KEY}} for dynamic keys.",
)
@click.option(
    "-t",
    "--type",
    prompt="Variable Type",
    type=str,
    help="Given base JSON schema type.",
)
@click.option(
    "-d",
    "--description",
    prompt="Variable Description",
    type=str,
    help="Provides a description for the variable.",
)
@click.option(
    "--options",
    prompt="If type is enum add comma separated values",
    default="",
    help="For enums, offer aggregate option hierarchy.",
)
@click.option("--required", is_flag=True, help="Mark the variable as required.")
@click.option("--default", type=str, help="Provide a default value for the variable.")
@click.argument("path", type=click.Path(exists=True))
def add_variable(name, type, description, options, required, default, path):
    """Add a new variable to the module."""
    try:
        yaml_path = validate_facets_yaml(path)
        variables_tf_path = validate_variables_tf(path)

        if type not in ALLOWED_TYPES:
            raise click.UsageError(
                f"❌ Type '{type}' is not allowed. Must be one of: {', '.join(ALLOWED_TYPES)}."
            )

        # Validate default value based on type
        if default is not None:
            if type == "number":
                default = validate_number(default)  # Ensure the default is a valid number
            elif type == "boolean" and default.lower() not in ["true", "false"]:
                raise click.UsageError(
                    "❌ Default value for type 'boolean' must be 'true' or 'false'."
                )
            elif type == "enum" and default not in options.split(","):
                raise click.UsageError(
                    f"❌ Default value for type 'enum' must be one of the options: {options}."
                )

        variable_schema = {
            "type": "string" if type == "enum" else type,
            "description": description,
        }

        if type == "enum":
            if not options:
                raise click.UsageError("❌ Options must be specified for enum type.")
            variable_schema["enum"] = options.split(",")

        if required:
            variable_schema["required"] = True

        if default is not None:
            variable_schema["default"] = default

        # Load and update facets.yaml
        with open(yaml_path, "r") as yaml_file:
            data = yaml.safe_load(yaml_file) or {}

        if "spec" not in data or not data["spec"]:
            data["spec"] = {"type": "object", "properties": {}}
        if "properties" not in data["spec"] or data["spec"]["properties"] is None:
            data["spec"]["properties"] = {}

        keys = name.split(".")
        sub_data = data["spec"]["properties"]
        for key in keys[:-1]:
            if key not in sub_data or sub_data[key] is None:
                sub_data[key] = {"type": "object", "properties": {}}
            sub_data = sub_data[key]["properties"]
        sub_data[keys[-1]] = variable_schema

        with open(yaml_path, "w") as yaml_file:
            yaml.dump(data, yaml_file)

        with open(variables_tf_path, "r") as file:
            terraform_code = file.read()

        updated_code = update_spec_variable(terraform_code, "instance", "spec", {
            name: 'string' if type == 'enum' else type,
        })

        with open(variables_tf_path, "w") as file:
            file.write(updated_code)

        click.echo(
            f"✅ Variable '{name}' of type '{type}' added with description '{description}' in path '{path}'."
        )

    except click.UsageError as ue:
        click.echo(ue.message)
