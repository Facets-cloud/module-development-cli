# FTF CLI

FTF CLI is a command-line interface (CLI) tool that facilitates module generation, variable management, and validation in Terraform.

## Installation

To install FTF CLI locally, follow these steps:

### Prerequisites

- Python 3.6 or later
- Virtual Environment (recommended)

### Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
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
  Follow on-screen prompts to input module details like Intent, Flavor, Cloud, Title, and Description.

- **Add Variable**

  Adds a new variable to the module.
  
  ```bash
  ftf add-variable
  ```
  Provide the necessary variable details as prompted, such as Variable Name, Type, and Description.

- **Validate Directory**

  Validates the Terraform configuration and checks for formatting, initialization, and security violations using Checkov.
  
  ```bash
  ftf validate-directory --path /your/path/to/module [--check-only]
  ```
  Use `--check-only` to verify formatting without applying changes.

## Contribution

Feel free to fork the repository and submit pull requests for any feature enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE.md file for more details.
