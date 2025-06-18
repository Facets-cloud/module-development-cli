#!/bin/bash

# Development Environment Setup Script
# This script sets up a complete development environment matching CI

set -e

echo "🚀 Setting up development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS. For other platforms, follow manual setup."
    exit 1
fi

# Check if Homebrew is installed
print_step "Checking Homebrew installation..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    print_success "Homebrew is installed"
fi

# Install pyenv if not present
print_step "Setting up pyenv for Python version management..."
if ! command -v pyenv &> /dev/null; then
    print_warning "pyenv not found. Installing pyenv..."
    brew install pyenv
    
    # Add pyenv to shell profile
    SHELL_PROFILE=""
    if [[ -f ~/.zshrc ]]; then
        SHELL_PROFILE=~/.zshrc
    elif [[ -f ~/.bashrc ]]; then
        SHELL_PROFILE=~/.bashrc
    elif [[ -f ~/.bash_profile ]]; then
        SHELL_PROFILE=~/.bash_profile
    fi
    
    if [[ -n "$SHELL_PROFILE" ]]; then
        echo "" >> "$SHELL_PROFILE"
        echo "# pyenv configuration" >> "$SHELL_PROFILE"
        echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> "$SHELL_PROFILE"
        echo 'eval "$(pyenv init --path)"' >> "$SHELL_PROFILE"
        echo 'eval "$(pyenv init -)"' >> "$SHELL_PROFILE"
        print_success "Added pyenv to $SHELL_PROFILE"
    fi
    
    # Load pyenv for current session
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
else
    print_success "pyenv is already installed"
fi

# Install required Python versions
print_step "Installing Python versions (3.11, 3.12, 3.13)..."
PYTHON_VERSIONS=("3.11" "3.12" "3.13")
for version in "${PYTHON_VERSIONS[@]}"; do
    # Get latest patch version
    latest_version=$(pyenv install --list | grep -E "^\s*${version}\.[0-9]+$" | tail -1 | tr -d ' ')
    if [[ -n "$latest_version" ]]; then
        print_step "Installing Python $latest_version..."
        pyenv install -s "$latest_version"
        print_success "Python $latest_version installed"
    else
        print_warning "Could not find Python $version in pyenv"
    fi
done

# Set local Python versions for the project
print_step "Setting up local Python versions for project..."
cd "$(dirname "$0")/.."
pyenv local 3.11 3.12 3.13
print_success "Local Python versions set"

# Verify installations
print_step "Verifying Python installations..."
for version in "${PYTHON_VERSIONS[@]}"; do
    if command -v "python$version" &> /dev/null; then
        py_version=$(python$version --version)
        print_success "Python $version: $py_version"
    else
        print_error "Python $version not found in PATH"
    fi
done

# Setup development environment
print_step "Setting up development environment..."
make setup
make dev

print_step "Installing additional development tools..."
./env/bin/pip install tox pre-commit

# Setup pre-commit hooks
print_step "Setting up pre-commit hooks..."
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=127, --max-complexity=10]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: ./env/bin/pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
EOF

./env/bin/pre-commit install
print_success "Pre-commit hooks installed"

# Run initial tests
print_step "Running initial test suite..."
make test

echo ""
print_success "Development environment setup complete!"
echo ""
echo -e "${BLUE}Available commands:${NC}"
echo "  make help                 - Show all available commands"
echo "  make test                 - Run tests with single Python version"
echo "  make test-all-versions    - Test against all Python versions (like CI)"
echo "  make ci-test              - Run exact CI workflow locally"
echo "  make ci-lint              - Run exact CI lint workflow locally"
echo "  make lint                 - Run linting"
echo "  make format               - Format code"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Restart your terminal or run: source ~/.zshrc (or ~/.bashrc)"
echo "2. Run 'make test-all-versions' to test against all Python versions"
echo "3. Run 'make ci-test' to run the exact same tests as CI"
echo ""
print_success "Happy coding! 🎉"
