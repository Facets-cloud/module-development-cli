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
   pip install --upgrade pip
   pip install -r requirements.txt

   # Or install directly via setup
   pip install .
   ```

## Usage

After successful installation, you can use the `ftf` command to access CLI.

### Commands:

#### Generate Module

Generate a new module with specified parameters.

```bash
ftf generate-module [OPTIONS]
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

#### Preview Module

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

#### Login

Authenticate and store credentials for a control plane using a named profile.


## Contribution

Feel free to fork the repository and submit pull requests for any feature enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for more details.
