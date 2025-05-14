from subprocess import run
import click
from ftf_cli.utils import (
    validate_facets_yaml,
    validate_variables_tf,
    ALLOWED_TYPES,
    update_spec_variable,
    validate_number,
)
from ruamel.yaml.scalarstring import DoubleQuotedScalarString
from ruamel.yaml import YAML


@click.command()
@click.option(
    "-n",
    "--name",
    prompt="Variable Name (dot-separated for nested and * for dynamic keys).",
    type=str,
    help="Name allowing nested dot-separated variants. Use '*' for dynamic keys where you want to use regex and pass the regex using --pattern flag For example: 'my_var.*.key'.",
)
@click.option(
    "--title",
    prompt="Title for the variable in facets.yaml.",
    type=str,
    help="Title for the variable in facets.yaml.",
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
    default="",
    help="For enums, offer aggregate option hierarchy.",
)
@click.option("--required", is_flag=True, help="Mark the variable as required.")
@click.option("--default", type=str, help="Provide a default value for the variable.")
@click.option(
    "-p",
    "--pattern",
    type=str,
    default=None,
    help='Provide comma separated regex for pattern properties. Number of wildcard keys and patterns must match. Eg: \'"^[a-z]+$","^[a-zA-Z0-9._-]+$"\'',
)
@click.argument("path", type=click.Path(exists=True))
def add_variable(
    name, title, type, description, options, required, default, path, pattern
):
    """Add a new variable to the module."""

    yaml = YAML()
    yaml.preserve_quotes = True
    if run("terraform version", shell=True, capture_output=True).returncode != 0:
        raise click.UsageError(
            "❌ Terraform is not installed. Please install Terraform to continue."
        )

    yaml_path = validate_facets_yaml(path)
    variables_tf_path = validate_variables_tf(path)

    if type not in ALLOWED_TYPES:
        raise click.UsageError(
            f"❌ Type '{type}' is not allowed. Must be one of: {', '.join(ALLOWED_TYPES)}."
        )

    if type == "enum" and not options:
        options = click.prompt(
            "Type is set to 'enum'. Please provide comma-separated values for options",
            type=str,
        )

    if type == "enum":
        if not options:
            raise click.UsageError("❌ Options must be specified for enum type.")

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
        "title": title,
        "description": description,
        "type": "string" if type == "enum" else type,
    }

    if type == "enum":
        variable_schema["enum"] = options.split(",")

    if default is not None:
        variable_schema["default"] = default

    keys = name.split(".")

    if keys[-1] == "*" or keys[0] == "*":
        raise click.UsageError(
            "❌ Variable starting or ending with pattern properties is not allowed."
        )

    for index in range(len(keys)):
        if keys[index] == "*" and index + 1 < len(keys) and keys[index + 1] == "*":
            raise click.UsageError(
                "❌ Variable with consecutive pattern properties is not allowed."
            )

    wildcard_keys = [i for i in keys if i == "*"]
    if pattern is None and len(wildcard_keys) > 0:
        pattern = click.prompt(
            'Pattern for dynamic keys (comma-separated regex). Number of wildcard keys and patterns must match. Eg: "^[a-z]+$","^[a-zA-Z0-9._-]+$"',
            type=str,
        )
    patterns = pattern.split(",") if pattern else []

    if len(wildcard_keys) != len(patterns):
        raise click.UsageError("❌ Number of wildcard keys and patterns must match.")

    # Load and update facets.yaml
    with open(yaml_path, "r") as yaml_file:
        data = yaml.load(yaml_file) or {}

    instance_description = data["description"] if "description" in data else ""

    if "spec" not in data or not data["spec"]:
        data["spec"] = {"type": "object", "properties": {}}

    if "properties" not in data["spec"] or data["spec"]["properties"] is None:
        data["spec"]["properties"] = {}
    sub_data = data["spec"]["properties"]

    tail = data["spec"]

    for index, key in enumerate(keys):
        if index + 1 < len(keys) and keys[index + 1] == "*":
            if key not in sub_data or sub_data[key] is None:
                sub_data[key] = {"type": "object", "patternProperties": {}}

            check_and_raise_execption(
                sub_data[key], "properties", "patternProperties", key
            )

            prompt_for_title_and_description(key, sub_data[key])

            tail = sub_data
            sub_data = sub_data[key]["patternProperties"]
            continue

        if key == "*":
            old_keys = list(sub_data.keys())
            old_value = None
            if len(old_keys) > 0:
                old_value = sub_data[old_keys[0]]
                del sub_data[old_keys[0]]

            pattern_key = patterns.pop(0)
            pattern_key = DoubleQuotedScalarString(pattern_key.replace('"', ""))
            sub_data[pattern_key] = (
                old_value if old_value else {"type": "object", "properties": {}}
            )
            sub_data = sub_data[pattern_key]
            prompt_for_title_and_description(pattern_key, sub_data)
            tail = sub_data
            sub_data = sub_data["properties"]

        elif index + 1 < len(keys):
            if key not in sub_data or sub_data[key] is None:
                sub_data[key] = {"type": "object", "properties": {}}
            else:
                check_and_raise_execption(
                    sub_data[key], "patternProperties", "properties", key
                )
            prompt_for_title_and_description(key, sub_data[key])
            tail = sub_data[key]
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


def check_and_raise_execption(
    data: dict, key_to_check: str, key_to_be_added: str, parent: str
):
    if key_to_check in data:
        raise click.UsageError(
            f"❌ facets.yaml already has {key_to_check} defined in {parent}. Cannot add {key_to_be_added} at the same level."
        )


def prompt_for_title_and_description(key: str, object: dict):
    if "title" not in object:
        title = click.prompt(
            f"Title for key {key} not found. Please provide a title",
            type=str,
        )
        if title == "" or title is None:
            raise click.UsageError(
                f"❌ Title for key {key} cannot be empty. Please provide a valid title."
            )

        object["title"] = title
    if "description" not in object:
        description = click.prompt(
            f"Description for key {key} not found. Please provide a description",
            type=str,
        )
        if description == "" or description is None:
            raise click.UsageError(
                f"❌ Description for key {key} cannot be empty. Please provide a valid description."
            )

        object["description"] = description
