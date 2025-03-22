import click
import yaml
import os
import questionary
import hcl2
from ftf_cli.utils import generate_output_tree


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-n",
    "--name",
    prompt="Enter the name of the provider",
    help="The name of the provider.",
)
@click.option(
    "-s",
    "--source",
    prompt="Enter the source of the provider",
    help="The source of the provider.",
)
@click.option(
    "-v",
    "--version",
    prompt="Enter the version of the provider",
    help="The version of the provider.",
)
@click.option(
    "-a",
    "--attributes",
    prompt="Enter the comma seperated list of attributes (dot-separated for nested)",
    help='Comma seperated list of attributes. eg : "attribute1,attribute2" format. Supports nested attributes with "." character.',
)
def expose_provider(path, name, source, version, attributes):
    """Exposes the provider in facets yaml"""
    attributes_processed = list(attributes.split(","))
    providers = {}
    providers[name] = {
        "source": source,
        "version": version,
        "attributes": {value: None for value in attributes_processed},
    }

    try:
        facets_yaml_path = os.path.join(path, "facets.yaml")
        with open(facets_yaml_path, "r") as file:
            facets_yaml = yaml.safe_load(file)
            file.close()

        # Get outputs declared in facets yaml
        outputs = facets_yaml.get("outputs")
        output_list = []
        if outputs != None:
            output_list = outputs.keys()

        # Mention there are no outputs and generate the default output with intent name
        if len(output_list) < 1:

            click.echo(f"⚠️ No output found in {facets_yaml_path}.")
            intent = facets_yaml.get("intent", "")

            if intent == "":
                click.echo(
                    f"❌ Invalid facets yaml {facets_yaml_path}. Run validate directory command to validate."
                )
                return

            output_type = f"@outputs/{intent}"

            click.echo(f"🔧 Generating default output of type {output_type}.")

            new_output = generate_default_output(output_type)
            # add the default output generated to in memory yaml
            facets_yaml.update(new_output)

            output_list.append("default")

        selected_output = questionary.select(
            "Select output where you want to expose provider as a part of:",
            choices=output_list,
        ).ask()

        # generate output selection menu
        output_lookup = generate_output_lookup(path)

        provider_attributes = providers[name]["attributes"]

        # prompt for output selection for attributes
        for attribute in provider_attributes.keys():
            referred_output = prompt_user_for_output_selection(
                output_lookup, attribute, True
            )
            click.echo(f"Attribute {attribute} will be read from {referred_output}")
            provider_attributes[attribute] = referred_output

        # deflatten the attributes
        provider_attributes = deflatten_dict(provider_attributes)

        # update the deflatten attributes
        providers[name]["attributes"] = provider_attributes

        # add empty providers map if providers does not exist in selected output
        if not "providers" in facets_yaml["outputs"][selected_output]:
            facets_yaml["outputs"][selected_output]["providers"] = {}

        # add the generated provider config to selected output
        facets_yaml["outputs"][selected_output]["providers"].update(providers)

        # prompt for confirmation before writing to file
        click.echo(
            f"🪄 The updated facets yaml\n{yaml.dump(facets_yaml)}",
        )
        save = questionary.select(
            "Select if you want to save this to yaml:", choices=["Yes", "No"]
        ).ask()

        if save == "No":
            click.echo("❌ User cancelled the save.")
            return

        with open(facets_yaml_path, "w") as file:
            yaml.dump(facets_yaml, file, default_flow_style=False)
            file.close()

        click.echo(
            f"✅ Sucessfully exposed the provider {name} in output {selected_output}"
        )

    except Exception as e:
        click.echo(f"❌ Error encounter while adding provider {name}: {e}")


def generate_default_output(output_type):
    """Generate default output if none is present."""
    output = {"outputs": {"default": {"type": output_type}}}
    return output


def prompt_user_for_output_selection(obj, attribute, is_root=False):
    """Function to keep prompting the user to select fields from output lookup"""
    keys = list(obj.keys())
    if not is_root:
        keys.append("*")
    selected_output = questionary.select(
        f"Keep selecting the field to read attribute {attribute} from:",
        choices=keys,
    ).ask()

    # select whole object as output
    if selected_output == "*":
        return ""

    nested_obj = obj[selected_output]

    # if selected object is empty object
    if nested_obj == {}:
        raise Exception(
            f"❌ Selected object {selected_output} does not expose any fields."
        )

    # if selected object is terminating node
    if "type" in nested_obj:
        return selected_output

    # keep promting further
    result = prompt_user_for_output_selection(nested_obj, attribute)

    # generate the path
    if result == "" or result == "*":
        return selected_output
    else:
        return selected_output + "." + result


def generate_output_lookup(path):
    """Generate output lookup tree"""
    output_file = os.path.join(path, "output.tf")
    if not os.path.exists(output_file):
        click.echo(
            f"⚠️: {output_file} not found. Cannot expose providers if outputs are not defined."
        )
        return

    with open(output_file, "r") as file:
        parsed_outputs = hcl2.load(file)
        file.close()

    locals = parsed_outputs.get("locals", [{}])[0]
    output_interfaces = locals.get("output_interfaces", [{}])[0]
    output_attributes = locals.get("output_attributes", [{}])[0]
    output_blocks = parsed_outputs.get("output", [])

    output = {
        "output_attributes": output_attributes,
        "output_interfaces": output_interfaces,
    }

    output_tree = generate_output_tree(output)

    for output_block in output_blocks:
        for key, _ in output_block.items():
            output_tree[key] = {"type": "any"}

    return output_tree


def deflatten_dict(dict):
    """Deflatten the dictionary"""

    deflatten_dict = {}
    for key, value in dict.items():
        front = deflatten_dict
        back = front
        paths = list(key.split("."))
        for path in paths:
            if front.get(path) == None:
                front[path] = {}
            back = front
            front = front[path]
        back[path] = value
    return deflatten_dict
