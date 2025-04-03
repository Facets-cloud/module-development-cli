# FTF CLI

FTF CLI is a command-line interface (CLI) tool that facilitates module generation, variable management, validation, and registration in Terraform.

## Installation

You can install FTF CLI from pip, pipx or directly from source.

### Installing with `pip` / `pipx`

To install FTF CLI using pip (or pipx)

#### Steps

1. With pipx
   ```
   pipx install git+https://github.com/Facets-cloud/module-development-cli.git
   ```
2. With pip
   ```
   pip install git+https://github.com/Facets-cloud/module-development-cli.git
   ```

### Installing from source

To install FTF CLI locally, follow these steps:

#### Prerequisites

- Python 3.6 or later
- Virtual Environment (recommended)

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

3. **Install dependencies**:
   Ensure `pip` is upgraded and install the required packages:

   ```bash
   pip install .
   ```

## Usage

After successful installation, you can use the `ftf` command to access CLI.

### Commands:

#### Generate Module

Generate a new module with specified parameters.

```bash
ftf generate-module [OPTIONS] /path/to/module
```

Prompts for details such as Intent, Flavor, Cloud, Title, and Description.

**Options**:
- `-i, --intent`: (prompt) The intent of the module.
- `-f, --flavor`: (prompt) The flavor of the module.
- `-c, --cloud`: (prompt) The cloud provider for the module.
- `-t, --title`: (prompt) The title of the module.
- `-d, --description`: (prompt) The description of the module.

**Notes**:
- User inputs define basic module structure, auto-created based on templates.
- Ensure correct cloud provider information for accurate configurations.
- Default path where module is generated is current directory where the cli is run.

#### Add Variable

Add a new variable to the module by specifying necessary details.

```bash
ftf add-variable [OPTIONS] /path/to/module
```

Prompts for Variable Name, Type, and Description, with the option to specify via CLI.

**Options**:
- `-n, --name`: (prompt) Variable Name, allows nested dot-separated variants.
- `-t, --type`: (prompt) Variable Type, given base JSON schema type.
- `-d, --description`: (prompt) Provides a description for the variable.
- `--options`: (prompt) For enums, input comma separated Options.

**Notes**:
- Supports nested variables using dot notation in variable names.
- Validates variable type before addition to ensure compliance.

#### Validate Directory

Validate the Terraform configuration for formatting, initialization, and security violations using Checkov.

```bash
ftf validate-directory /path/to/module [OPTIONS]
```

**Options**:
- `--check-only`: Verifies formatting without applying changes.
- The command operates directly on the provided path without additional prompts.

**Notes**:
- Ensures Terraform files are valid and formatted, preventing deployment errors.
- Automatically runs Checkov for security checks, enhancing module safety.
#### Login

Authenticate and store credentials for a control plane using a named profile.

```bash
ftf login [OPTIONS]
```

Prompts for Control Plane URL, Username, Token, and Profile. This information is stored under a specified profile for future interactions.

**Options**:
- `-c, --control-plane-url`: (prompt) The URL of the control plane. Must start with `http://` or `https://`.
- `-u, --username`: (prompt) Your username.
- `-t, --token`: (prompt) Your access token, input is hidden.
- `-p, --profile`: (prompt) The profile name to use for storing credentials, defaults to `default`.

**Notes**:
- Validates the Control Plane URL format.
- Checks credentials against the control plane before storing.
- Useful for managing multiple environments with different profiles.
  

#### Add Input

Add an predefined output as input for terraform module by specifying necessary details.

```bash
ftf add-input [OPTIONS] /path/to/module
```

Prompts for Profile Name, Input Name Display Name, Description and Output Type.

**Options**:
- `-p, --profile`: (prompt) Profile name to use, defaults to `default`.
- `-n, --name`: (prompt) Name of the input to be added as part of required inputs in facets.yaml and variables.tf.
- `-dn, --display-name`: (prompt) Display name of the input to be added as part of input variable in facets.yaml.
- `-d, --description`: (prompt) Description of the input variable to be added as part of input variable in facets.yaml.
- `-o, --output-type`: (prompt) The type of registered output type to be added as input for terraform module.


#### Preview (and Publish) Module

Register or preview a module at the specified path.

```bash
ftf preview-module /path/to/module [OPTIONS]
```

**Options**:
- `-p, --profile`: (prompt) Profile to use, defaults to `default`.
- `-a, --auto-create-intent`: Automatically create intent if not exists.
- `-f, --publishable`: Indicates whether the module is publishable for production.
- `-g, --git-repo-url`: Git repository URL from where the code is taken.
- `-r, --git-ref`: Git reference or branch name.
- `--publish`: Publish the module after preview if set.

You can even set env vars GIT_REPO_URL, GIT_REF, FACETS_PROFILE. Particularly useful in CI integration

**Notes**:
- If GIT_REPO_URL, GIT_REF are not set or provided it will preview the module as a non-publishable module with a changed version
- The version will be changed to a local testing version such as 1.0-username


#### Expose Provider

Expose a new provider in the module output by specifying necessary details.

```bash
ftf expose-provider [OPTIONS] /path/to/module
```

Prompts for Provider Name, Source, Version, Attributes and Output.

**Options**:
- `-n, --name`: (prompt) Provider Name.
- `-s, --source`: (prompt) Provider Source.
- `-v, --version`: (prompt) Provider Version.
- `-a, --attributes`: (prompt) Provider Attributes comma-separated list of  of map items; attributes mapped to their values with equal(=) symbol. eg : "attribute1=val1,depth.attribute2=val2" format.
- `-o, --output`: (prompt) Output to expose provider as a part of. 

**Notes**:
- Supports nested attributes using dot notation in attribute name.
- By default, a default output will be created if none is present of type intent provided in facets.yaml with name "default".


#### Delete Module

Delete a registered terraform module from control plane.

```bash
ftf delete-module [OPTIONS]
```

Prompts for Module Intent, Flavor, Version and Profile.

**Options**:
- `-i, --intent`: (prompt) Intent of the terraform module to delete.
- `-f, --flavor`: (prompt) Flavor of the terraform module to delete.
- `-v, --version`: (prompt) Version of the terraform module to delete.
- `-s, --stage`: (prompt) Stage of the terraform module to delete.
- `-p, --profile`: (prompt) Profile name to use, defaults to `default`.

## Contribution

Feel free to fork the repository and submit pull requests for any feature enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for more details.

