# FTF CLI

FTF CLI is a command-line interface (CLI) tool that facilitates module generation, variable management, validation, and registration in Terraform.

## Key Features

- **Module Generation**: Scaffold Terraform modules with standardized structure
- **Variable Management**: Add and manage input variables with type validation
- **Output Integration**: Wire registered output types as module inputs
- **Validation**: Comprehensive validation for modules and configurations
- **Control Plane Integration**: Seamless authentication and interaction with Facets control plane

## Installation

You can install FTF CLI using pip, pipx, or directly from source.

### Installing with pip / pipx

#### Using pipx (recommended)

```bash
pipx install ftf-cli
```

#### Using pip

```bash
pip install ftf-cli
```

### Installing from source

To install FTF CLI from source, follow these steps:

#### Prerequisites

- Python 3.11 or later
- Virtual environment (recommended)

#### Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Facets-cloud/module-development-cli.git
   cd module-development-cli
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   uv sync
   source .venv/bin/activate   # On Windows use `.venv\Scripts\activate`
   ```

3. **Install the package**:

   ```bash
   pip install -e .[dev]  # Install with development dependencies
   ```

## Usage

After successful installation, you can use the `ftf` command to access CLI.

### Commands:

#### Validate Facets

Validate the facets YAML file in the specified directory for correctness and schema compliance.

```bash
ftf validate-facets [OPTIONS] PATH
```

**Arguments**:
- `PATH`: Filesystem path to directory containing the facets YAML file.

**Options**:
- `--filename TEXT`: Name of the facets YAML file to validate (default: facets.yaml).

**Notes**:
- Checks existence and YAML syntax of the specified facets YAML file.
- Validates adherence to Facets schema including spec fields.
- Prints success message if valid; raises error and message if invalid.

#### Generate Module

Generate a new Terraform module structured by specifying intent, flavor, cloud provider, title, and description.

```bash
ftf generate-module [OPTIONS] /path/to/module
```

**Options**:
- `-i, --intent`: (prompt) The intent or purpose of the module.
- `-f, --flavor`: (prompt) The flavor or variant of the module.
- `-c, --cloud`: (prompt) Target cloud provider (e.g. aws, gcp, azure).
- `-t, --title`: (prompt) Human-readable title of the module.
- `-d, --description`: (prompt) Description outlining module functionality.

**Notes**:
- Automatically scaffolds module files based on standard templates.
- Cloud provider selection influences configuration details.
- Module is generated inside the specified path or current directory by default.

#### Add Variable

Add a new input variable to the Terraform module, supporting nested names and types.

```bash
ftf add-variable [OPTIONS] /path/to/module
```

**Options**:
- `-n, --name`: (prompt) Name allowing nested dot-separated variants. Use * for dynamic keys where you want to use regex and pass the regex using --pattern flag For example: 'my_var.*.key'.
- `--title`: (prompt) Title for the variable in facets.yaml.
- `-t, --type`: (prompt) Variable type, supports basic JSON schema types like string, number, boolean, enum.
- `-d, --description`: (prompt) A descriptive text explaining the variable.
- `--options`: (prompt) Comma-separated options used if the variable type is enum.
- `--required`: Optional flag to mark variable as required.
- `--default`: Optional way to provide a default value for the variable.
- `-p, --pattern`: (prompt) Provide comma separated regex for pattern properties. Number of wildcard keys and patterns must match. Eg: '"^[a-z]+$","^[a-zA-Z0-9._-]+$"'

**Notes**:
- Preserves terraform formatting while adding variables.
- Performs type validation before addition.
- Nested variables create the necessary nested structure internally.
- Pattern properties support regex validation for dynamic keys.

#### Validate Directory

Perform validation on Terraform directories including formatting checks and security scans using Checkov.

```bash
ftf validate-directory /path/to/module [OPTIONS]
```

**Options**:
- `--check-only`: Only check formatting; does not make any changes.
- `--skip-terraform-validation`: Skip Terraform validation steps if set to true.

**Notes**:
- Runs `terraform fmt` for formatting verification.
- Runs `terraform init` to ensure initialization completeness (unless skipped).
- Uses Checkov to scan Terraform files for security misconfigurations.
- Designed for fast feedback on module quality and security.

#### Login

Authenticate to a control plane and store credentials under a named profile for reuse.

```bash
ftf login [OPTIONS]
```

**Options**:
- `-c, --control-plane-url`: (prompt) Base URL of the control plane API (must start with http:// or https://).
- `-u, --username`: (prompt) Your login username.
- `-t, --token`: (prompt) Access token or API token (input is hidden).
- `-p, --profile`: (prompt) Profile name to save credentials under (default: "default").

**Notes**:
- URL format is validated before saving.
- Credentials are verified via the control plane API before storage.
- The selected profile becomes the default profile for future commands in the current session.
- Profile selection persists across terminal sessions, so you don't need to specify a profile for each command.
- Allows switching between multiple profiles/environments.

#### Add Input

Add an existing registered output type as an input to your Terraform module.

```bash
ftf add-input [OPTIONS] /path/to/module
```

**Options**:
- `-p, --profile`: (prompt) Profile to use for control plane authentication (default: "default").
- `-n, --name`: (prompt) Name of the input variable to add in facets.yaml and variables.tf.
- `-dn, --display-name`: (prompt) Human-readable display name for the input variable.
- `-d, --description`: (prompt) Description for the input variable.
- `-o, --output-type`: (prompt) The type of registered output to wire as input. Format: @namespace/name (e.g., @outputs/database, @custom/sqs).

**Notes**:
- Updates facets.yaml required inputs and variables.tf accordingly.
- Facilitates parametrization of modules using control plane outputs.
- Supports both default (@outputs) and custom namespaces.

**Example**:
```bash
ftf add-input /path/to/module \
  --name queue_connection \
  --display-name "SQS Queue Connection" \
  --description "Configuration for SQS queue" \
  --output-type "@custom/sqs"
```

#### Preview (and Publish) Module

Preview or register a Terraform module with the control plane from a specified directory.

```bash
ftf preview-module /path/to/module [OPTIONS]
```

**Options**:
- `-p, --profile`: (prompt) Profile to authenticate with (default: "default").
- `-a, --auto-create-intent`: Automatically create intent in control plane if it doesn't exist.
- `-f, --publishable`: Marks the module as production-ready and publishable.
- `-g, --git-repo-url`: Git repository URL where the module source code resides.
- `-r, --git-ref`: Git ref, branch, or tag for the module version.
- `--publish`: Flag to publish the module immediately after preview.
- `--skip-terraform-validation`: Skip Terraform validation steps if set to true.
- `--skip-output-write`: Do not update the output type in facets. Set to true only if you have already registered the output type before calling this command.

**Notes**:
- Environment variables such as GIT_REPO_URL, GIT_REF, FACETS_PROFILE can be used for automation or CI pipelines.
- If Git info is absent, module versioning defaults to a local testing version format (e.g. 1.0-{username}).

#### Expose Provider

Expose a Terraform provider as part of the module outputs with configurable name, version, attributes, and output.

```bash
ftf expose-provider [OPTIONS] /path/to/module
```

**Options**:
- `-n, --name`: (prompt) Name to assign to the provider.
- `-s, --source`: (prompt) Provider source URL or address.
- `-v, --version`: (prompt) Version constraint for the provider.
- `-a, --attributes`: (prompt) Comma-separated attributes map with equal sign (e.g., "attribute1=val1,depth.attribute2=val2").
- `-o, --output`: (prompt) Output block to expose the provider under.

**Notes**:
- Supports nested attribute keys using dot notation.
- If no default output exists, one of type intent "default" under facets.yaml will be created.

#### Add Import

Add import declarations to the module to specify resources that should be imported.

```bash
ftf add-import [OPTIONS] /path/to/module
```

Automatically discovers resources in the module and prompts for selecting a resource, naming the import, and specifying if it's required.

**Options**:
- `-n, --name`: The name of the import to be added. If not provided, will prompt interactively.
- `-r, --required`: Flag to indicate if this import is required. Default is True.
- `--resource`: The Terraform resource address to import (e.g., 'aws_s3_bucket.bucket').
- `--index`: For resources with 'count', specify the index (e.g., '0', '1', or '*' for all).
- `--key`: For resources with 'for_each', specify the key (e.g., 'my-key' or '*' for all).
- `--resource-address`: The full resource address to import (e.g., 'azurerm_key_vault.for_each_key_vault[0]'). If provided, runs in non-interactive mode and skips resource discovery.

**Examples**:
```bash
# Interactive mode
ftf add-import /path/to/module

# Non-interactive mode for regular resource
ftf add-import /path/to/module --name key_vault --resource azurerm_key_vault.key_vault

# Non-interactive mode for count resource
ftf add-import /path/to/module --name count_vault --resource azurerm_key_vault.count_key_vault --index 1

# Non-interactive mode for for_each resource
ftf add-import /path/to/module --name for_each_vault --resource azurerm_key_vault.for_each_key_vault --key my-key

# Non-interactive mode with full resource state address
ftf add-import /path/to/module --name for_each_vault --resource-address 'azurerm_key_vault.for_each_key_vault[0]'
```

**Notes**:
- Discovers and lists all resources defined in the module's Terraform files
- Supports resources with count or for_each meta-arguments
- Validates import names and resource addresses
- Updates the facets.yaml file with the import declarations in the format:
  ```yaml
  imports:
    - name: s3_bucket
      resource_address: aws_s3_bucket.bucket
      required: true
  ```

#### Delete Module

Delete a registered Terraform module from the control plane.

```bash
ftf delete-module [OPTIONS]
```

**Options**:
- `-i, --intent`: (prompt) Intent of the module to delete.
- `-f, --flavor`: (prompt) Flavor of the module.
- `-v, --version`: (prompt) Version of the module.
- `-s, --stage`: (prompt) Deployment stage of the module (choices: "PUBLISHED", "PREVIEW").
- `-p, --profile`: (prompt) Authentication profile to use (default: "default").

#### Get Output Types

Retrieve the output types registered in the control plane for the authenticated profile. Shows both namespace and name for each output type.

```bash
ftf get-output-types [OPTIONS]
```

**Options**:
- `-p, --profile`: (prompt) Profile to authenticate as (default: "default").

**Example Output**:
```
Registered output types:
- @custom/sqs
- @outputs/cache
- @outputs/database
```

#### Get Output Type Details

Retrieve comprehensive details for a specific registered output type from the control plane, including properties and lookup tree.

```bash
ftf get-output-type-details [OPTIONS]
```

**Options**:
- `-o, --output-type`: (prompt) The output type to get details for. Format: @namespace/name (e.g., @outputs/vpc, @custom/sqs).
- `-p, --profile`: (prompt) Profile to use for authentication (default: "default").

**Example Output**:
```
=== Output Type Details: @custom/sqs ===

Name: sqs
Namespace: @custom
Source: CUSTOM
Inferred from Module: true

--- Properties ---
{
  "attributes": {
    "queue_arn": {"type": "string"},
    "queue_url": {"type": "string"}
  },
  "interfaces": {}
}

--- Lookup Tree ---
{
  "out": {
    "attributes": {"queue_arn": {}, "queue_url": {}},
    "interfaces": {}
  }
}
```

#### Register Output Type

Register a new output type in the control plane using a YAML definition file.

```bash
ftf register-output-type YAML_PATH [OPTIONS]
```

**Arguments**:
- `YAML_PATH`: Path to the YAML definition file for the output type.

**Options**:
- `-p, --profile`: Profile name to use, defaults to environment variable FACETS_PROFILE if set, otherwise `default`.
- `--inferred-from-module`: Flag to mark the output type as inferred from a module.

**Notes**:
- The YAML file must include `name` and `properties` fields.
- The name should be in the format `@namespace/name` (e.g., `@outputs/database`, `@custom/sqs`).
- You can include a `providers` section in the YAML to specify provider information.
- Ensures you're logged in before attempting to register the output type.

**Example YAML**:
```yaml
name: "@custom/sqs"
properties:
  attributes:
    queue_arn:
      type: string
    queue_url:
      type: string
  interfaces: {}
```

#### Get Resources

List all Terraform resources in the given module directory.

```bash
ftf get-resources /path/to/module
```

**Arguments**:
- `/path/to/module`: Filesystem path to the directory containing Terraform files.

**Description**:
- Discovers and lists all Terraform resources defined in the module's `.tf` files.
- Shows the resource address and whether it uses `count` or `for_each`.
- Useful for quickly auditing which resources are present in a module.

**Example Output**:
```
Found 3 resources:
- aws_s3_bucket.bucket
- aws_instance.web (with count)
- aws_security_group.sg (with for_each)
```

## Contribution

Feel free to fork the repository and submit pull requests for any feature enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for more details.