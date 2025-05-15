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
    prompt="Enter the comma seperated list of map items; attributes mapped to their values with equal(=) symbol (dot-separated keys for nested)",
    help='Comma seperated list of  of map items; attributes mapped to their values with equal(=) symbol. eg : "attribute1=val1,depth.attribute2=val2" format. Supports nested attributes with "." character.',
)
@click.option(
    "-o",
    "--output",
    default=None,
    help='Output to expose provider as a part of. By default, a default output will be created if none is present of type intent provided in facets.yaml with name "default".',
)
def expose_provider(path, name, source, version, attributes, output):
    """Exposes the provider in facets yaml"""
    pairs = attributes.split(",")
    prosssed_attributes = {}
    for pair in pairs:
        if "=" not in pair:
            # Assign None if no value is provided
            prosssed_attributes[pair.strip()] = None
        else:
            key, value = pair.split("=", 1)
            prosssed_attributes[key.strip()] = value.strip()
    providers = {}
    providers[name] = {
        "source": source,
        "version": version,
        "attributes": prosssed_attributes,
    }

    try:
        facets_yaml_path = os.path.join(path, "facets.yaml")
        output_file = os.path.join(path, "outputs.tf")

        if not (os.path.exists(output_file) and os.path.exists(facets_yaml_path)):
            raise click.UsageError(
                f"❌ {output_file} or {facets_yaml_path} not found. Run validate directory command to validate directory"
            )

        with open(facets_yaml_path, "r") as file:
            facets_yaml = yaml.safe_load(file)

        # Get outputs declared in facets yaml
        outputs = facets_yaml.get("outputs")
        output_list = []
        if outputs is not None:
            output_list = outputs.keys()

        # Mention there are no outputs and generate the default output with intent name
        if len(output_list) < 1:

            click.echo(f"⚠️ No output found in {facets_yaml_path}.")
            intent = facets_yaml.get("intent", "")

            if intent == "":
                raise click.UsageError(
                    f"❌ Invalid facets yaml {facets_yaml_path}. Run validate directory command to validate."
                )

            output_type = f"@outputs/{intent}"

            click.echo(f"🔧 Generating default output of type {output_type}.")

            new_output = generate_default_output(output_type)
            # add the default output generated to in memory yaml
            facets_yaml.update(new_output)

            output_list.append("default")

        if not output:
            output = questionary.select(
                "Select output where you want to expose provider as a part of:",
                choices=output_list,
            ).ask()
        elif output not in output_list:
            raise click.UsageError(
                f"❌ Invalid output {output}. Please select from {output_list}"
            )

        # generate output selection menu
        output_lookup = generate_output_lookup(path)

        provider_attributes = providers[name]["attributes"]

        # prompt for output selection for attributes
        for attribute in provider_attributes.keys():
            if provider_attributes[attribute] is None:
                referred_output = prompt_user_for_output_selection(
                    output_lookup, attribute, True
                )
                provider_attributes[attribute] = referred_output
                click.echo(f"Attribute {attribute} will be read from {referred_output}")
            else:
                click.echo(
                    f"Attribute {attribute} will be read from {provider_attributes[attribute]}"
                )

        # convert output_attributes to attributes and output_interfaces to interfaces
        for key, value in provider_attributes.items():
            if isinstance(value, str) and value.startswith("output_attributes"):
                provider_attributes[key] = value.replace(
                    "output_attributes", "attributes"
                )
            elif isinstance(value, str) and value.startswith("output_interfaces"):
                provider_attributes[key] = value.replace(
                    "output_interfaces", "interfaces"
                )

        # deflatten the attributes
        provider_attributes = deflatten_dict(provider_attributes)

        # update the deflatten attributes
        providers[name]["attributes"] = provider_attributes

        # add empty providers map if providers does not exist in selected output
        if "providers" not in facets_yaml["outputs"][output]:
            facets_yaml["outputs"][output]["providers"] = {}

        # add the generated provider config to selected output
        facets_yaml["outputs"][output]["providers"].update(providers)

        with open(facets_yaml_path, "w") as file:
            yaml.dump(facets_yaml, file, default_flow_style=False, sort_keys=False)

        click.echo(f"✅ Sucessfully exposed the provider {name} in output {output}")

    except Exception as e:
        raise click.UsageError(
            f"❌ Error encountered while adding provider {name}: {e}"
        )


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
        raise click.UsageError(
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
    output_file = os.path.join(path, "outputs.tf")
    if not os.path.exists(output_file):
        click.echo(
            f"⚠️: {output_file} not found. Cannot expose providers if outputs are not defined."
        )
        return

    with open(output_file, "r") as file:
        parsed_outputs = hcl2.load(file)

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
            if front.get(path) is None:
                front[path] = {}
            back = front
            front = front[path]
        back[path] = value
    return deflatten_dict
