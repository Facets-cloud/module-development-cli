# FTF CLI

FTF CLI is a command-line interface (CLI) tool that facilitates module generation, variable management, validation, and registration in Terraform.

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

- Python 3.9 or later
- Virtual environment (recommended)

#### Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Facets-cloud/module-development-cli.git
   cd module-development-cli
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv env
   source env/bin/activate   # On Windows use `env\Scripts\activate`
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

#### Validate Directory

Perform validation on Terraform directories including formatting checks and security scans using Checkov.

```bash
ftf validate-directory /path/to/module [OPTIONS]
```

**Options**:
- `--check-only`: Only check formatting; does not make any changes.

**Notes**:
- Runs `terraform fmt` for formatting verification.
- Runs `terraform init` to ensure initialization completeness.
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
- `-o, --output-type`: (prompt) The type of registered output to wire as input.

**Notes**:
- Updates facets.yaml required inputs and variables.tf accordingly.
- Facilitates parametrization of modules using control plane outputs.

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

#### Delete Module

Delete a registered Terraform module from the control plane.

```bash
ftf delete-module [OPTIONS]
```

**Options**:
- `-i, --intent`: (prompt) Intent of the module to delete.
- `-f, --flavor`: (prompt) Flavor of the module.
- `-v, --version`: (prompt) Version of the module.
- `-s, --stage`: (prompt) Deployment stage of the module.
- `-p, --profile`: (prompt) Authentication profile to use (default: "default").

#### Get Output Types

Retrieve the output types registered in the control plane for the authenticated profile.

```bash
ftf get-output-types [OPTIONS]
```

**Options**:
- `-p, --profile`: (prompt) Profile to authenticate as (default: "default").

#### Get Output Lookup Tree

Retrieve the detailed lookup tree for a registered output type from the control plane.

```bash
ftf get-output-lookup-tree [OPTIONS]
```

**Options**:
- `-o, --output`: (prompt) Name of the output type to query.
- `-p, --profile`: (prompt) Profile to use for authentication (default: "default").

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
- The name should be in the format `@namespace/name`.
- You can include a `providers` section in the YAML to specify provider information.
- Ensures you're logged in before attempting to register the output type.

## Contribution

Feel free to fork the repository and submit pull requests for any feature enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for more details.