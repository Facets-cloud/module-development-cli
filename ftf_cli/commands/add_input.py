import json
import re
from subprocess import run
import traceback
import click
import os

import hcl
import requests
import yaml
from ftf_cli.utils import (
    is_logged_in,
    transform_output_tree,
    ensure_formatting_for_object,
)
from lark import Token, Tree


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-p",
    "--profile",
    default=lambda: os.getenv("FACETS_PROFILE", "default"),
    help="The profile name to use or defaults to environment variable FACETS_PROFILE if set.",
)
@click.option(
    "-n",
    "--name",
    prompt="Input Name",
    type=str,
    help="The name of the input variable to be added as part of input variable in facets.yaml and variables.tf.",
)
@click.option(
    "-dn",
    "--display-name",
    prompt="Input Display Name",
    type=str,
    help="The display name of the input variable to be added as part of input variable in facets.yaml.",
)
@click.option(
    "-d",
    "--description",
    prompt="Input Description",
    type=str,
    help="The description of the input variable to be added as part of input variable in facets.yaml.",
)
@click.option(
    "-o",
    "--output-type",
    prompt="Output Type",
    type=str,
    help="The type of registered output to be added as input for terraform module.",
)
def add_input(path, profile, name, display_name, description, output_type):
    """Add an existing registered output as a input in facets.yaml and populate the attributes in variables.tf exposed by selected output."""

    if run("terraform version", shell=True, capture_output=True).returncode != 0:
        raise click.UsageError(
            "❌ Terraform is not installed. Please install Terraform to continue."
        )

    # validate if facets.yaml and variables.tf exists
    facets_yaml = os.path.join(path, "facets.yaml")
    variable_file = os.path.join(path, "variables.tf")
    if not (os.path.exists(variable_file) and os.path.exists(facets_yaml)):
        raise click.UsageError(
            f"❌ {variable_file} or {facets_yaml} not found. Run validate directory command to validate directory."
        )
    try:

        with open(facets_yaml, "r") as file:
            facets_data = yaml.safe_load(file)

        required_inputs = facets_data.get("inputs", {})
        required_inputs_map = {}

        pattern = r"@outputs/(.*)"
        for key, value in required_inputs.items():
            required_input = value.get("type", "")
            if required_input and required_input != "":
                match = re.search(pattern, required_input)
                if match:
                    required_inputs_map[key] = match.group(1)

        if name in required_inputs_map:
            click.echo(
                f"⚠️ Input {name} already exists in the inputs variable in {facets_yaml}. Will be overwritten."
            )

        required_inputs_map[name] = output_type

        # update facets yaml
        required_inputs.update(
            {
                name: {
                    "type": f"@outputs/{output_type}",
                    "displayName": display_name,
                    "description": description,
                }
            }
        )

        # update the facets yaml with the new input
        facets_data.update({"inputs": required_inputs})

        # check if profile is set
        click.echo(f"Profile selected: {profile}")
        credentials = is_logged_in(profile)
        if not credentials:
            raise click.UsageError(
                f"❌ Not logged in under profile {profile}. Please login first."
            )

        # Extract credentials
        control_plane_url = credentials["control_plane_url"]
        username = credentials["username"]
        token = credentials["token"]

        response = requests.get(
            f"{control_plane_url}/cc-ui/v1/tf-outputs", auth=(username, token)
        )

        registered_outputs = {output["name"]: output for output in response.json()}
        registered_output_names = list(registered_outputs.keys())

        # make sure all outputs are registered

        for output in required_inputs_map.values():
            if output not in registered_output_names:
                raise click.UsageError(
                    f"❌ {output} not found in registered outputs. Please select a valid output type from {registered_output_names}."
                )

        # get output tree for each output
        output_trees = {}
        for output_name, output in required_inputs_map.items():
            output_tree_string = registered_outputs[output].get("lookupTree")
            output_tree = json.loads(output_tree_string) if output_tree_string else None
            if output_tree and output_tree["out"] != {}:
                output_trees[output_name] = output_tree["out"]
            else:
                output_trees[output_name] = {"attributes": {}, "interfaces": {}}

        inputs_var = generate_inputs_variable(output_trees)

        replace_inputs_variable(variable_file, inputs_var)
        ensure_formatting_for_object(variable_file)

        click.echo(f"✅ Input added to the {variable_file}.")

        # write facets yaml data to file
        with open(facets_yaml, "w") as file:
            yaml.dump(facets_data, file, sort_keys=False)

        click.echo(f"✅ Input added to the {facets_yaml}.")

    except Exception:
        traceback.print_exc()
        raise click.UsageError(f"❌ Error encountered while adding input {name}")


def generate_inputs_variable(output_trees):
    """Generate the Terraform 'inputs' variable schema from the given output tree and name."""

    generated_inputs = {}

    for tree_name, output_tree in output_trees.items():

        # Initialize the tree_name entry in generated_inputs
        if tree_name not in generated_inputs:
            generated_inputs[tree_name] = {}

        # Transform the output tree into the Terraform schema
        generated_inputs[tree_name]["attributes"] = transform_output_tree(
            output_tree["attributes"], level=3
        )
        generated_inputs[tree_name]["interfaces"] = transform_output_tree(
            output_tree["interfaces"], level=3
        )

    # Generate the Terraform variable by iterating over generated inputs
    terraform_variable = f"""
variable "inputs" {{
  description = "A map of inputs requested by the module developer."
  type        = object({{
    {', '.join([
        f'{tree_name} = object({{ {", ".join([f"{key} = {value}" for key, value in attributes.items()])} }})'
        for tree_name, attributes in generated_inputs.items()
    ])}
  }})
}}
"""
    return terraform_variable


def replace_inputs_variable(file_path, new_inputs_block):
    """
    Replace the entire 'inputs' variable block in the Terraform file with a new block.
    If the 'inputs' variable block is not found, append the new block to the file.

    Args:
        file_path (str): Path to the Terraform file.
        new_inputs_block (str): The new 'inputs' variable block to replace or append.
    """
    with open(file_path, "r+") as file:
        content = file.read()
        if not content.endswith("\n"):
            file.write("\n")

    with open(file_path, "r") as file:
        start_node = hcl.parse(file)

    new_start_node = hcl.parses(new_inputs_block)

    body_node = start_node.children[0]

    inputs_tree_index = -1

    # remove input variable if present in the file
    for index, child in enumerate(body_node.children):
        if (
            isinstance(child, Tree)
            and child.data == "block"
            and len(child.children) >= 3
            and child.children[0].data == "identifier"
            and isinstance(child.children[0].children[0], Token)
            and child.children[0].children[0].type == "NAME"
            and child.children[0].children[0].value == "variable"
            and isinstance(child.children[1], Token)
            and child.children[1].type == "STRING_LIT"
            and child.children[1].value == '"inputs"'
        ):
            inputs_tree_index = index

    new_body_node = new_start_node.children[0]
    new_line_node = new_body_node.children[0]
    new_inputs_node = new_body_node.children[1]

    if inputs_tree_index == -1:
        body_node.children.append(new_inputs_node)
        body_node.children.append(new_line_node)
    else:
        body_node.children[inputs_tree_index] = new_inputs_node

    with open(file_path, "w") as file:
        new_content = hcl.writes(body_node)
        file.write(new_content)
