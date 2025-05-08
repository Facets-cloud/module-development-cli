# FTF CLI

FTF CLI is a command-line interface (CLI) tool that facilitates module generation, variable management, validation, and registration in Terraform.

## Installation

You can install FTF CLI using pip, pipx, or directly from source.

### Installing with pip / pipx

#### Using pipx (recommended)

```bash
pipx install git+https://github.com/Facets-cloud/module-development-cli.git
```

#### Using pip

```bash
pip install git+https://github.com/Facets-cloud/module-development-cli.git
```

### Installing from source

To install FTF CLI from source, follow these steps:

#### Prerequisites

- Python 3.8 or later
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
- Performs type