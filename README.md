# FTF CLI

FTF CLI is a command-line interface (CLI) tool that facilitates module generation, variable management, validation, and registration in Terraform.

## Installation

You can install FTF CLI from pip, pipx or directly from source.

### Installing with `pip` / `pipx`

To install FTF CLI using pip (or or pipx if you have that available)

#### Steps

- With pipx
  ```
  pipx install git+https://github.com/Facets-cloud/module-development-cli.git
  ```
- With pip
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

- **Generate Module**

  Generates a new module with specified parameters.

  ```bash
  ftf generate-module
  ```
  Prompts for details such as Intent, Flavor, Cloud, Title, and Description.

  **Options**:
  - `-i, --intent`: (prompt) The intent of the module.
  - `-f, --flavor`: (prompt) The flavor of the module.
  - `-c, --cloud`: (prompt) The cloud provider for the module.
  - `-t, --title`: (prompt) The title of the module.
  - `-d, --description`: (prompt) The description of the module.


- **Add Variable**
  Add a new variable to the module by specifying necessary details.

  ```bash
  ftf add-variable
  ```
  Prompts for Variable Name, Type, and Description, with the option to specify via CLI.

  **Options**:
  - `-n, --name`: (prompt/type) Variable Name, allows nested dot-separated variants.
  - `-t, --type`: (prompt/type) Variable Type, given base JSON schema type.
  - `-d, --description`: Provides a description for the variable.
  - `--options`: For enums, offer aggregate option hierarchy.
  - `-p, --path`: Path to the module directory containing facets.yaml


- **Validate Directory**
  Validate the Terraform configuration for formatting, initialization, and security violations using Checkov.

  ```bash
  ftf validate-directory --path /your/path/to/module [--check-only]
  ```

  **Options**:
  - `--check-only`: Verifies formatting without applying changes.
  - The command operates directly on the provided path without additional prompts.


- **Preview Module**

  Register or preview a module at the specified path.

  ```bash
   ftf preview-module /path/to/module [OPTIONS]
  ```

  **Options**:
  - `-p, --profile`: Profile to use, defaults from environment.
  - `-a, --auto-create-intent`: Automatically create intent if not exists.
  - `-f, --publishable`: Indicates whether the module is publishable for production.
  - `-g, --git-repo-url`: Git repository URL from where the code is taken.
  - `-r, --git-ref`: Git reference or branch name.


## Contribution

Feel free to fork the repository and submit pull requests for any feature enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for more details.
