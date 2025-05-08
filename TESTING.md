# Testing Guide for FTF CLI

This document explains the testing structure and best practices for contributing to the FTF CLI project.

## Overview

The project uses `pytest` for testing and has a structured approach to organizing tests:

- `tests/`: Main test directory
  - `commands/`: Tests for CLI commands
  - `integration/`: Integration tests with real CLI execution
  - Unit tests for utility functions and other components

## Running Tests

You can run tests using the following commands:

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run only command tests
make test-commands

# Run only integration tests
make test-integration
```

Or directly with pytest:

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/commands/test_add_variable.py
pytest tests/test_utils.py::test_dict_input
```

## Test Structure and Best Practices

### 1. Unit Tests

Place these directly in the `tests/` directory. They should test individual utility functions and other components.

```python
# Example: tests/test_utils.py
import pytest
from ftf_cli.utils import some_function

def test_some_function():
    result = some_function(input_value)
    assert result == expected_value
```

### 2. Command Tests

Place these in the `tests/commands/` directory. They should test the CLI commands using mocking.

```python
# Example: tests/commands/test_add_variable.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch, mock_open
from ftf_cli.commands.add_variable import add_variable

def test_add_variable(runner):  # runner fixture from conftest.py
    with patch('builtins.open', mock_open(read_data="mock_data")):
        result = runner.invoke(add_variable, ['--arg', 'value'])
        assert result.exit_code == 0
        assert "Success message" in result.output
```

### 3. Integration Tests

Place these in the `tests/integration/` directory. They should test the CLI from end to end, calling actual CLI commands.

```python
# Example: tests/integration/test_cli_commands.py
import subprocess
import os
import pytest

def test_generate_module(temp_module_dir):  # temp_module_dir fixture from conftest.py
    result = subprocess.run(
        ['ftf', 'generate-module', '--arg', 'value'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert os.path.exists(os.path.join(temp_module_dir, 'expected_file'))
```

## Fixtures

Common test fixtures are provided in `tests/conftest.py`:

- `runner`: A Click test runner for command tests
- `temp_module_dir`: A temporary directory with a basic module structure
- `mock_yaml_validator`: Mocks the YAML validator

Use these fixtures in your tests where appropriate.

## Mocking

When testing commands that interact with files or external services, use mocking:

```python
# Mock file operations
with patch('builtins.open', mock_open(read_data='file_content')):
    # Test code that reads files

# Mock file existence checks
with patch('os.path.exists', return_value=True):
    # Test code that checks if files exist

# Mock YAML operations
with patch('yaml.safe_load', return_value={'key': 'value'}):
    # Test code that loads YAML files
```

## Adding New Tests

When adding new tests:

1. Follow the existing pattern and structure
2. Use descriptive test names that indicate what's being tested
3. Isolate tests from the file system and external services using mocks
4. Group related tests in the same file
5. Add appropriate docstrings to test functions

## Dependencies

The project uses these testing dependencies:

- `pytest`: Main testing framework
- `pytest-mock`: For easy mocking
- `flake8`: For linting (run with `make lint`)
- `black`: For code formatting (run with `make format`)

These are installed when you run `make dev` or `pip install -e ".[dev]"`.
