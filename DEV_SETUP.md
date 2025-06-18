# Development Environment Setup

This guide helps you set up a development environment that matches your CI exactly.

## Quick Setup (Recommended)

Run the automated setup script:

```bash
./scripts/setup-dev-env.sh
```

This will:
- Install pyenv for Python version management
- Install Python 3.11, 3.12, and 3.13
- Set up your development environment
- Install all dependencies
- Set up pre-commit hooks
- Run initial tests

## Manual Setup

If you prefer manual setup or the script doesn't work:

### 1. Install pyenv (for Python version management)

```bash
# On macOS with Homebrew
brew install pyenv

# Add to your shell profile (.zshrc, .bashrc, etc.)
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

### 2. Install Python versions

```bash
# Install the same Python versions as CI
pyenv install 3.11.9  # or latest 3.11.x
pyenv install 3.12.4  # or latest 3.12.x  
pyenv install 3.13.0  # or latest 3.13.x

# Set local versions for this project
pyenv local 3.11.9 3.12.4 3.13.0
```

### 3. Set up development environment

```bash
make setup
make dev
```

## Available Commands

After setup, you can use these commands:

### Basic Development
- `make help` - Show all available commands
- `make setup` - Create virtual environment
- `make dev` - Install in development mode
- `make test` - Run tests with default Python version
- `make lint` - Run linting
- `make format` - Format code with black
- `make clean` - Clean build artifacts

### Multi-Version Testing (Matches CI)
- `make test-all-versions` - Test against Python 3.11, 3.12, 3.13
- `make ci-test` - Run exact CI test workflow locally
- `make ci-lint` - Run exact CI lint workflow locally

### Python Version Management
- `make install-python-versions` - Install all required Python versions
- `make check-python-versions` - Check which Python versions are available

## Testing Like CI

To run tests exactly like your CI:

```bash
# Run all tests across all Python versions (like CI matrix)
make ci-test

# Run linting exactly like CI
make ci-lint

# Or use tox for multi-version testing
make test-all-versions
```

## Troubleshooting

### Python Version Issues

If you get Python version errors:

1. Check your current Python version: `python3 --version`
2. Install required versions: `make install-python-versions`
3. Verify installation: `make check-python-versions`

### pyenv Not Working

1. Restart your terminal after installation
2. Check your shell profile has pyenv configuration
3. Run: `source ~/.zshrc` (or ~/.bashrc)

### CI Test Failures

If local tests pass but CI fails:

1. Run `make ci-test` to replicate CI exactly
2. Check Python version requirements in `setup.py`
3. Compare local and CI dependency versions

## Integration with IDEs

### VS Code

Add this to your `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./env/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black"
}
```

### PyCharm

1. Set Project Interpreter to `./env/bin/python`
2. Set Test Runner to pytest
3. Configure Code Style to use Black

## Notes

- Your CI uses Python 3.11, 3.12, 3.13
- Your `setup.py` requires Python >=3.11
- Local testing with Python 3.9 will not match CI behavior
- Use `make ci-test` for the most accurate local testing
