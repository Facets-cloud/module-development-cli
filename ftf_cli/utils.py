import os
import configparser
from subprocess import run
from lark import Token, Tree
import yaml
import jsonschema
from jsonschema import validate
import click
import hcl2
import requests
import hcl
from ftf_cli.schema import yaml_schema, spec_schema, additional_properties_schema

ALLOWED_TYPES = ["string", "number", "boolean", "enum"]
REQUIRED_TF_FACETS_VARS = ["instance", "instance_name", "environment", "inputs"]


def validate_facets_yaml(path, filename="facets.yaml"):
    """Validate the existence and format of specified facets yaml file in the given path."""
    yaml_path = os.path.join(path, filename)
    if not os.path.isfile(yaml_path):
        raise click.UsageError(
            f"❌ {filename} file does not exist at {os.path.abspath(yaml_path)}"
        )

    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
            validate_yaml(data)

    except yaml.YAMLError as exc:
        raise click.UsageError(f"❌ {filename} is not a valid YAML file: {exc}")

    return yaml_path


def validate_facets_tf_vars(path, filename="variables.tf"):
    """Validate the existence and format of specified facets tf vars file in the given path."""
    variables_tf_path = os.path.join(path, filename)
    if not os.path.isfile(variables_tf_path):
        raise click.UsageError(
            f"❌ {filename} file does not exist at {os.path.abspath(variables_tf_path)}"
        )

    try:
        terraform_start_node: Tree = None
        with open(variables_tf_path, "r") as file:
            terraform_start_node = hcl.parse(file)

        body_node: Tree = terraform_start_node.children[0]
        child_nodes = body_node.children

        not_allowed_variables = []
        required_tf_facets_vars = REQUIRED_TF_FACETS_VARS.copy()

        for child in child_nodes:
            if (
                child.data == "block"
                and len(child.children) > 2
                and isinstance(child.children[0], Tree)
                and child.children[0].data == "identifier"
                and isinstance(child.children[0].children[0], Token)
                and child.children[0].children[0].type == "NAME"
                and child.children[0].children[0].value == "variable"
                and child.children[1].type == "STRING_LIT"
            ):
                var_name = child.children[1].value
                var_name = var_name.replace('"', "")
                if var_name in required_tf_facets_vars:
                    required_tf_facets_vars.remove(var_name)
                else:
                    not_allowed_variables.append(var_name)

        if len(required_tf_facets_vars) > 0:
            raise click.UsageError(
                f"❌ {filename} is missing required variables: {', '.join(required_tf_facets_vars)}"
            )
        elif len(not_allowed_variables) > 0:
            raise click.UsageError(
                f"❌ Following variables are not allowed in {filename}: {', '.join(not_allowed_variables)} ."
            )
        else:
            click.echo(f"✅ {filename} contains all required facets tf variables.")

    except Exception as e:
        raise click.UsageError(f"❌ {filename} is not a valid HCL file: {e}")

    return variables_tf_path


def generate_output_tree(obj):
    """Generate a JSON schema from a outputs.tf file."""
    if isinstance(obj, dict):
        transformed = {}
        for key, value in obj.items():
            transformed[key] = generate_output_tree(value)
        return transformed
    elif isinstance(obj, list):
        if len(obj) > 0:
            return {"type": "array", "items": generate_output_tree(obj[0])}
        else:
            return {"type": "array"}  # No "items" if unknown
    elif isinstance(obj, bool):
        return {"type": "boolean"}
    elif isinstance(obj, (int, float)):
        return {"type": "number"}
    elif isinstance(obj, str):
        return {"type": "string"}
    else:
        return {"type": "any"}  # Catch unexpected types


def generate_output_lookup_tree(obj):
    """Generate a lookup tree to support $ referencing in the control-plane. """
    if isinstance(obj, dict):
        transformed = {}
        for key, value in obj.items():
            transformed[key] = generate_output_lookup_tree(value)
        return transformed
    elif isinstance(obj, list):
        if len(obj) > 0:
            return {"type": "array", "items": generate_output_lookup_tree(obj[0])}
        else:
            return {"type": "array"}  # No "items" if unknown
    elif isinstance(obj, (int, float, bool, str)):
        return {}
    else:
        return {}  # Catch unexpected types


def transform_output_tree(tree, level=1):
    """Recursively transform the output tree into a Terraform-compatible schema with proper indentation."""
    INDENT = "  "  # Fixed indentation (2 spaces)
    current_indent = INDENT * level
    next_indent = INDENT * (level + 1)

    if isinstance(tree, dict):
        if "type" in tree:
            # If the node has a "type", return it directly
            if tree["type"] == "array":
                # Handle arrays with "items"
                if "items" in tree:
                    return f"list({transform_output_tree(tree['items'], level)})"
                else:
                    return "list(any)"
            elif tree["type"] == "object":
                # Handle objects
                return "object({})"
            elif tree["type"] == "boolean":
                # Fix boolean type to bool
                return "bool"
            else:
                return tree["type"]
        else:
            # Recursively process nested dictionaries
            transformed_items = []
            for key, value in tree.items():
                transformed_value = transform_output_tree(value, level + 1)
                transformed_items.append(f"{next_indent}{key} = {transformed_value}")

            # Step 1: Join the transformed items with a comma and newline
            joined_items = ",\n".join(transformed_items)

            # Step 2: Construct the object block with proper indentation
            object_block = f"object({{\n{joined_items}\n{current_indent}}})"

            # Step 3: Return the constructed object block
            return object_block
    elif isinstance(tree, list):
        # Handle arrays
        if len(tree) > 0:
            return f"list({transform_output_tree(tree[0], level)})"
        else:
            return "list(any)"  # Unknown items
    else:
        # Fallback for unexpected types
        return "any"


def load_facets_yaml(path):
    """Load and validate facets.yaml file, returning its content as an object."""
    # Validate the facets.yaml file
    yaml_path = validate_facets_yaml(path)

    # Load YAML content
    with open(yaml_path, "r") as file:
        content = yaml.safe_load(file)

    return content


def validate_variables_tf(path):
    """Ensure variables.tf exists and is valid HCL."""
    variables_tf_path = os.path.join(path, "variables.tf")
    if not os.path.isfile(variables_tf_path):
        raise click.UsageError(
            f"❌ variables.tf file does not exist at {os.path.abspath(variables_tf_path)}"
        )

    try:
        with open(variables_tf_path, "r") as f:
            hcl2.load(f)
    except Exception as e:
        raise click.UsageError(f"❌ variables.tf is not a valid HCL file: {e}")

    return variables_tf_path


def insert_nested_fields(structure, keys, value):
    """Recursively inserts nested fields into the given dictionary structure."""
    if len(keys) == 1:
        structure[keys[0]] = value
    else:
        if keys[0] not in structure:
            structure[keys[0]] = {}
        insert_nested_fields(structure[keys[0]], keys[1:], value)


def update_spec_variable(
    yaml_file: dict,
    terraform_file_path: str,
    instance_description: str,
):
    with open(terraform_file_path, "r") as file:
        terraform_code = file.read()

    spec = {"spec": yaml_file.get("spec", {})}
    type_tree = generate_type_tree(spec)

    instance_string = generate_instance_block(type_tree, instance_description)

    new_instance_start_node = hcl.parses(instance_string)

    start_node = hcl.parses(terraform_code)
    body_node: Tree = start_node.children[0]
    variable_nodes = body_node.children

    instance_node_found: bool = False
    instance_node_index: int = -1

    for index, variable_node in enumerate(variable_nodes):
        if (
            variable_node.data == "block"
            and len(variable_node.children) > 1
            and isinstance(variable_node.children[0], Tree)
            and len(variable_node.children[0].children) > 0
            and isinstance(variable_node.children[0].children[0], Token)
            and variable_node.children[0].children[0].value == "variable"
            and variable_node.children[1].type == "STRING_LIT"
            and variable_node.children[1].value == '"instance"'
        ):
            instance_node_found = True
            instance_node_index = index
            break

    # If the instance variable block is not found, append it to the file
    if instance_node_found is False:
        variable_nodes.append(new_instance_start_node.children[0].children[0])
    else:
        variable_nodes[instance_node_index] = new_instance_start_node.children[
            0
        ].children[0]

    with open(terraform_file_path, "w") as file:
        new_content = hcl.writes(start_node)
        file.write(new_content)
        ensure_formatting_for_object(terraform_file_path)
        return


def check_no_array_or_invalid_pattern_in_spec(spec_obj, path="spec"):
    """
    Recursively check that no field in spec is of type 'array'.
    Also check that any direct patternProperties have object type only, not primitive types like string.
    Nested properties inside patternProperties can be any allowed types.
    Raises a UsageError with instruction if found.
    Assumes input is always valid JSON schema (no direct list values at property keys).
    """
    if not isinstance(spec_obj, dict):
        return

    for key, value in spec_obj.items():
        if isinstance(value, dict):
            field_type = value.get("type")
            override_disable_flag = value.get("x-ui-override-disable", False)
            overrides_only_flag = value.get("x-ui-overrides-only", False)
            if field_type == "array" and not override_disable_flag and not overrides_only_flag:
                raise click.UsageError(
                    f"Invalid array type found at {path}.{key}. "
                    f"Arrays without x-ui-override-disable or x-ui-overrides-only field are not allowed in spec. Use patternProperties for array-like structures instead or set either x-ui-override-disable or x-ui-overrides-only field to true."
                )
            if "patternProperties" in value:
                pp = value["patternProperties"]
                for pattern_key, pp_val in pp.items():
                    pattern_type = pp_val.get("type")
                    if not isinstance(pattern_type, str) or (pattern_type != "object" and pattern_type != "string"):
                        raise click.UsageError(
                            f'patternProperties at {path}.{key} with pattern "{pattern_key}" must be of type object or string.'
                        )
                    if pattern_type == "string" and not pp_val.get("x-ui-yaml-editor", False):
                        raise click.UsageError(
                            f'patternProperties at {path}.{key} with pattern "{pattern_key}" and type "string" must have x-ui-yaml-editor field set to true.'
                        )
            check_no_array_or_invalid_pattern_in_spec(value, path=f"{path}.{key}")


def validate_yaml(data):
    spec_obj = data.get("spec")
    try:
        validate(instance=data, schema=yaml_schema)
        # Additional check for arrays and invalid patternProperties in spec
        if spec_obj:
            check_no_array_or_invalid_pattern_in_spec(spec_obj)
    except jsonschema.exceptions.ValidationError as e:
        raise click.UsageError(
            f"Validation error in `facets.yaml`: `facets.yaml` is not following Facets Schema: {e}"
        )

    try:
        validate(instance=spec_obj, schema=spec_schema)
    except jsonschema.exceptions.ValidationError as e:
        raise click.UsageError(
            f"Validation error in `facets.yaml`: `x-ui` tags are invalid. Details: {e}"
        )

    try:
        validate(instance=spec_obj, schema=additional_properties_schema)
    except jsonschema.exceptions.ValidationError as e:
        raise click.UsageError(
            f"Validation error in `facets.yaml`: Field additionalProperties is not allowed under any object."
        )

    click.echo("✅ Facets YAML validation successful!")
    return True


def fetch_user_details(cp_url, username, token):
    return requests.get(f"{cp_url}/api/me", auth=(username, token))


def store_credentials(profile, credentials):
    config = configparser.ConfigParser()
    cred_path = os.path.expanduser("~/.facets/credentials")
    os.makedirs(os.path.dirname(cred_path), exist_ok=True)

    if os.path.exists(cred_path):
        config.read(cred_path)

    config[profile] = credentials

    with open(cred_path, "w") as configfile:
        config.write(configfile)


def is_logged_in(profile):
    config = configparser.ConfigParser()
    cred_path = os.path.expanduser("~/.facets/credentials")

    if not os.path.exists(cred_path):
        click.echo("Credentials file not found. Please login first.")
        return False

    config.read(cred_path)
    if profile not in config:
        click.echo(f"Profile {profile} not found. Please login using this profile.")
        return False

    try:
        credentials = config[profile]
        response = fetch_user_details(
            credentials["control_plane_url"],
            credentials["username"],
            credentials["token"],
        )
        response.raise_for_status()
        click.echo("Successfully authenticated with the control plane.")
        return credentials  # Return credentials if login is successful
    except requests.exceptions.HTTPError as http_err:
        click.echo(f"HTTP error occurred: {http_err}")
        return False
    except KeyError as key_err:
        click.echo(f"Missing credential information: {key_err}")
        raise click.UsageError(
            "Incomplete credentials found in profile. Please re-login."
        )
    except Exception as err:
        click.echo(f"An error occurred: {err}")
        return False


def validate_boolean(ctx, param, value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("true", "yes", "1"):
        return True
    elif value.lower() in ("false", "no", "0"):
        return False
    else:
        raise click.BadParameter("Boolean flag must be true or false.")


def validate_number(value):
    """Validate that the given value is a number and return it as an integer or float."""
    try:
        # Check if the value is an integer
        if "." not in value:
            return int(value)
        # Otherwise, treat it as a float
        return float(value)
    except ValueError:
        raise click.UsageError(
            f"❌ Default value '{value}' must be a valid number (integer or float)."
        )


def ensure_formatting_for_object(file_path):
    """Ensure there is a newline after 'object({' in the Terraform file."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    updated_lines = []
    for line in lines:
        if "object({" in line or "})" in line:
            # Add a newline after 'object({'
            line = line.replace("object({", "object({\n", -1)
            line = line.replace("})", "})\n", -1)
            line = line.replace("})\n,", "}),\n", -1)
            # make sure only one newline is added in the end
            line = line.rstrip() + "\n"
            updated_lines.append(line)
        else:
            updated_lines.append(line)

    with open(file_path, "w") as file:
        file.writelines(updated_lines)

    with open(os.devnull, "w") as devnull:
        run(["terraform", "fmt", file_path], stdout=devnull, stderr=devnull)


def generate_instance_block(type_tree: dict, description: str) -> str:
    """
    Generate a terraform variable instance  block dynamically.

    Args:
        type_tree (str): The type tree to be used for generating the variable block.
        description (str): The description of the variable.

    Returns:
        str: The generated Terraform variable block.
    """

    transformed_type_tree = transform_type_tree(type_tree, level=2)

    # Generate the full variable block
    variable_block = f"""variable "instance" {{
  description = "{description}"
  type = object({{
    kind    = string
    flavor  = string
    version = string
{transformed_type_tree}
  }})
}}
"""
    return variable_block


def transform_type_tree(tree: any, level: int) -> str:
    """
    Recursively transform the type tree into a terraform-compatible schema with proper indentation.

    Args:
        tree (any): The type tree to be transformed.
        level (int): The current indentation level.

    Returns:
        str: The transformed Terraform-compatible schema.
    """
    INDENT = "  "
    current_indent = INDENT * level

    if isinstance(tree, dict):
        transformed_items = []
        for key, value in tree.items():
            transformed_value = transform_type_tree(value, level + 1)
            if isinstance(value, dict):
                object_block = f"object({{\n{transformed_value}\n{current_indent}}})"
                transformed_items.append(f"{current_indent}{key} = {object_block}")
            else:
                transformed_items.append(f"{current_indent}{key} = {transformed_value}")

        transformed_items_str = ",\n".join(transformed_items)
        return f"{transformed_items_str}"

    else:
        return f"{tree}"


def generate_type_tree(spec: dict) -> dict:
    """
    Generate a type tree from the given spec.

    Args:
        spec (dict): The spec dictionary to generate the type tree from.

    Returns:
        dict: The generated type tree.
    """
    result = {}
    for key, value in spec.items():
        if isinstance(value, dict) and "type" in value:
            if value["type"] == "string":
                result[key] = "string"
            elif value["type"] == "number":
                result[key] = "number"
            elif value["type"] == "boolean":
                result[key] = "boolean"
            elif value["type"] == "array":
                result[key] = "array"
            elif value["type"] == "object":
                if "properties" in value:
                    result[key] = generate_type_tree(value["properties"])
                else:
                    result[key] = "any"
    return result
