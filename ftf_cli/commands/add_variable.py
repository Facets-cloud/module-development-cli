from subprocess import run
import click
import os
import yaml
from ftf_cli.utils import (
    ensure_formatting_for_object,
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
    help="Name allowing nested dot-separated variants. Use * for dynamic keys.",
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
        if run("terraform version", shell=True, capture_output=True).returncode != 0:
            click.echo(
                "❌ Terraform is not installed. Please install Terraform to continue."
            )
            return

        yaml_path = validate_facets_yaml(path)
        variables_tf_path = validate_variables_tf(path)

        if type not in ALLOWED_TYPES:
            raise click.UsageError(
                f"❌ Type '{type}' is not allowed. Must be one of: {', '.join(ALLOWED_TYPES)}."
            )

        # Validate default value based on type
        if default is not None:
            if type == "number":
                default = validate_number(
                    default
                )  # Ensure the default is a valid number
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

        if default is not None:
            variable_schema["default"] = default

        keys = name.split(".")

        if keys[-1] == "*":
            raise click.UsageError(
                "❌ Variable ending with pattern properties is not allowed."
            )

        keys_without_last = keys[:-1]

        # Load and update facets.yaml
        with open(yaml_path, "r") as yaml_file:
            data = yaml.safe_load(yaml_file) or {}

        instance_description = data["description"] if "description" in data else ""

        if keys[0] == "*":

            if "spec" not in data or not data["spec"]:
                data["spec"] = {"type": "object", "patternProperties": {}}

            check_and_raise_execption(
                data["spec"], "properties", "patternProperties", "spec"
            )

            if (
                "patternProperties" not in data["spec"]
                or data["spec"]["patternProperties"] is None
            ):
                data["spec"]["patternProperties"] = {}

            sub_data = data["spec"]["patternProperties"]
        else:

            if "spec" not in data or not data["spec"]:
                data["spec"] = {"type": "object", "properties": {}}

            check_and_raise_execption(
                data["spec"], "patternProperties", "properties", "spec"
            )

            if "properties" not in data["spec"] or data["spec"]["properties"] is None:
                data["spec"]["properties"] = {}
            sub_data = data["spec"]["properties"]

        tail = data["spec"]

        for index, key in enumerate(keys_without_last):
            if index + 1 < len(keys) and keys[index + 1] == "*":
                if key not in sub_data or sub_data[key] is None:
                    sub_data[key] = {"type": "object", "patternProperties": {}}

                check_and_raise_execption(
                    sub_data[key], "properties", "patternProperties", key
                )

                tail = sub_data
                sub_data = sub_data[key]["patternProperties"]
                continue

            if key == "*":
                if "type" not in sub_data:
                    sub_data["type"] = "object"
                if "keyPattern" not in sub_data:
                    sub_data["keyPattern"] = "^[a-zA-Z0-9_.-]+$"
                if "properties" not in sub_data:
                    sub_data["properties"] = {}
                tail = sub_data
                sub_data = sub_data["properties"]
            else:
                if key not in sub_data or sub_data[key] is None:
                    sub_data[key] = {"type": "object", "properties": {}}
                check_and_raise_execption(
                    sub_data[key], "patternProperties", "properties", key
                )
                tail = sub_data
                sub_data = sub_data[key]["properties"]

        if required:
            tail["required"] = tail.get("required", [])
            tail["required"].append(keys[-1])
            tail["required"] = list(set(tail["required"]))
        sub_data[keys[-1]] = variable_schema

        with open(yaml_path, "w") as yaml_file:
            yaml.dump(data, yaml_file)

        updated_key = ""
        updated_type = None
        for key in keys:
            if key == "*":
                updated_type = "any"
                break
            updated_key = f"{updated_key}.{key}" if updated_key != "" else key

        if updated_type is None:
            updated_type = "string" if type == "enum" else type

        update_spec_variable(data, variables_tf_path, instance_description)

        click.echo(
            f"✅ Variable '{name}' of type '{type}' added with description '{description}' in path '{path}'."
        )

    except click.UsageError as ue:
        click.echo(ue.message)


def check_and_raise_execption(
    data: dict, key_to_check: str, key_to_be_added: str, parent: str
):
    if key_to_check in data:
        raise click.UsageError(
            f"❌ facets.yaml already has {key_to_check} defined in {parent}. Cannot add {key_to_be_added} at the same level."
        )
