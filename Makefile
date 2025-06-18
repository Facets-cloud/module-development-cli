# Detect OS for cross-platform compatibility
OS := $(shell uname -s 2>/dev/null || echo Windows)

# Python versions to test (matching CI)
PYTHON_VERSIONS := 3.11 3.12 3.13
DEFAULT_PYTHON_VERSION := 3.11

# Directory for virtual environments
VENV_DIR := .venvs

ifeq ($(OS),Windows)
  PYTHON := $(shell where python3 2>NUL || echo "")
  PYTHON_EXE := env\Scripts\python.exe
  PIP := env\Scripts\pip.exe
  PYTEST := env\Scripts\pytest.exe
  FLAKE8 := env\Scripts\flake8.exe
  BLACK := env\Scripts\black.exe
  TOX := env\Scripts\tox.exe
else
  PYTHON := $(shell which python3 2>/dev/null || echo "")
  PYTHON_EXE := ./env/bin/python3
  PIP := ./env/bin/pip
  PYTEST := ./env/bin/pytest
  FLAKE8 := ./env/bin/flake8
  BLACK := ./env/bin/black
  TOX := ./env/bin/tox
endif

ifeq ($(PYTHON),)
  $(error "Python is not installed. Please install Python 3.11+")
endif

.PHONY: help setup install dev test test-unit test-commands test-integration lint format clean all
.PHONY: test-all-versions setup-pyenv install-python-versions check-python-versions
.PHONY: ci-test ci-lint test-matrix clean-all

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup              - Create virtual environment with default Python"
	@echo "  make install            - Install package in virtual environment"
	@echo "  make dev                - Install package in development mode"
	@echo "  make test               - Run tests with single Python version"
	@echo "  make test-unit          - Run unit tests only"
	@echo "  make test-commands      - Run command tests only"
	@echo "  make test-integration   - Run integration tests only"
	@echo "  make lint               - Run linting (flake8)"
	@echo "  make format             - Format code with black"
	@echo "  make clean              - Clean build artifacts and venv"
	@echo ""
	@echo "Multi-version testing (matches CI):"
	@echo "  make setup-pyenv           - Install pyenv (macOS/Linux)"
	@echo "  make install-python-versions - Install Python 3.11, 3.12, 3.13"
	@echo "  make test-all-versions     - Test against all Python versions (like CI)"
	@echo "  make ci-test               - Run exact CI test workflow locally"
	@echo "  make ci-lint               - Run exact CI lint workflow locally"
	@echo ""
	@echo "  make all                - Setup + dev + test"
	@echo "  make clean-all          - Clean everything including multi-version setups"

# Check if required Python version is available
check-python-version:
	@python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" || \
		(echo "Error: Python 3.11+ required. You have: $$(python3 --version)" && \
		 echo "Please install Python 3.11+ or run 'make install-python-versions'" && exit 1)

setup: check-python-version
ifeq ($(OS),Windows)
	"$(PYTHON)" -m venv env
	@if not exist env\Scripts\activate ( \
		echo "Virtual environment creation failed. Check Python installation." && exit 1 \
	)
	$(PYTHON_EXE) -m pip install --upgrade pip
else
	"$(PYTHON)" -m venv env
	@if [ ! -f "./env/bin/activate" ]; then \
		echo "Virtual environment creation failed. Check Python installation." && exit 1; \
	fi
	$(PYTHON_EXE) -m pip install --upgrade pip
endif

install:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\pip.exe ( \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1 \
	)
	$(PIP) install .
else
	@if [ ! -f "./env/bin/pip" ]; then \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1; \
	fi
	$(PIP) install .
endif

dev:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\pip.exe ( \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1 \
	)
	$(PIP) install -e ".[dev]"
	$(PIP) install tox flake8 black
else
	@if [ ! -f "./env/bin/pip" ]; then \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1; \
	fi
	$(PIP) install -e ".[dev]"
	$(PIP) install tox flake8 black
endif

test:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\pytest.exe ( \
		echo "Virtual environment not found. Run 'make dev' first." && exit 1 \
	)
	$(PYTEST) tests
else
	@if [ ! -f "./env/bin/pytest" ]; then \
		echo "Virtual environment not found. Run 'make dev' first." && exit 1; \
	fi
	$(PYTEST) tests
endif

test-unit:
	$(PYTEST) tests/test_*.py

test-commands:
	$(PYTEST) tests/commands/

test-integration:
	$(PYTEST) tests/integration/

lint:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\flake8.exe ( \
		echo "Virtual environment not found. Run 'make dev' first." && exit 1 \
	)
	$(FLAKE8) ftf_cli tests --count --select=E9,F63,F7,F82 --show-source --statistics
	$(FLAKE8) ftf_cli tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
else
	@if [ ! -f "./env/bin/flake8" ]; then \
		echo "Virtual environment not found. Run 'make dev' first." && exit 1; \
	fi
	$(FLAKE8) ftf_cli tests --count --select=E9,F63,F7,F82 --show-source --statistics
	$(FLAKE8) ftf_cli tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
endif

format:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\black.exe ( \
		echo "Virtual environment not found. Run 'make dev' first." && exit 1 \
	)
	$(BLACK) ftf_cli tests
else
	@if [ ! -f "./env/bin/black" ]; then \
		echo "Virtual environment not found. Run 'make dev' first." && exit 1; \
	fi
	$(BLACK) ftf_cli tests
endif

# Multi-version testing setup (macOS/Linux)
setup-pyenv:
ifneq ($(OS),Windows)
	@echo "Setting up pyenv for multi-version Python testing..."
	@if ! command -v pyenv >/dev/null 2>&1; then \
		echo "Installing pyenv..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install pyenv; \
		else \
			curl https://pyenv.run | bash; \
		fi; \
		echo ""; \
		echo "⚠️  Please add the following to your shell profile (~/.bashrc, ~/.zshrc, etc.):"; \
		echo "   export PATH=\"\$$HOME/.pyenv/bin:\$$PATH\""; \
		echo "   eval \"\$$(pyenv init --path)\""; \
		echo "   eval \"\$$(pyenv init -)\""; \
		echo ""; \
		echo "Then restart your shell or run: source ~/.bashrc"; \
		echo "After that, run 'make install-python-versions'"; \
	else \
		echo "pyenv is already installed"; \
	fi
else
	@echo "Multi-version testing on Windows requires manual Python installation"
	@echo "Please install Python 3.11, 3.12, and 3.13 from python.org"
endif

install-python-versions:
ifneq ($(OS),Windows)
	@echo "Installing Python versions for testing..."
	@for version in $(PYTHON_VERSIONS); do \
		echo "Installing Python $$version..."; \
		pyenv install -s $$version; \
	done
	@echo "Setting local Python versions..."
	pyenv local $(PYTHON_VERSIONS)
	@echo "Available Python versions:"
	pyenv versions
else
	@echo "Please manually install Python 3.11, 3.12, and 3.13 on Windows"
endif

check-python-versions:
	@echo "Checking available Python versions..."
	@for version in $(PYTHON_VERSIONS); do \
		if command -v python$$version >/dev/null 2>&1; then \
			echo "✓ Python $$version: $$(python$$version --version)"; \
		else \
			echo "✗ Python $$version: Not found"; \
		fi; \
	done

# Create tox.ini for multi-version testing
create-tox-config:
	@echo "Creating tox configuration..."
	@echo "[tox]" > tox.ini
	@echo "envlist = py311,py312,py313" >> tox.ini
	@echo "isolated_build = true" >> tox.ini
	@echo "" >> tox.ini
	@echo "[testenv]" >> tox.ini
	@echo "deps =" >> tox.ini
	@echo "    pytest>=8.3.5" >> tox.ini
	@echo "    pytest-mock" >> tox.ini
	@echo "    pyhcl>=0.4.5" >> tox.ini
	@echo "commands = python -m pytest tests" >> tox.ini
	@echo "install_command = pip install {opts} {packages}" >> tox.ini
	@echo "" >> tox.ini
	@echo "[testenv:lint]" >> tox.ini
	@echo "deps = flake8" >> tox.ini
	@echo "commands =" >> tox.ini
	@echo "    flake8 ftf_cli tests --count --select=E9,F63,F7,F82 --show-source --statistics" >> tox.ini
	@echo "    flake8 ftf_cli tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics" >> tox.ini
	@echo "" >> tox.ini
	@echo "[testenv:format]" >> tox.ini
	@echo "deps = black" >> tox.ini
	@echo "commands = black --check ftf_cli tests" >> tox.ini

# Test against all Python versions (like CI)
test-all-versions: create-tox-config
ifneq ($(OS),Windows)
	@if [ ! -f "./env/bin/tox" ]; then \
		echo "Installing tox in virtual environment..."; \
		$(PIP) install tox; \
	fi
	@echo "Running tests against all Python versions (matching CI)..."
	$(TOX)
else
	@echo "Multi-version testing on Windows requires tox to be set up manually"
endif

# Run exact CI lint workflow locally
ci-lint:
	@echo "Running CI lint workflow locally..."
	@echo "Setting up Python 3.13 environment..."
	@if command -v python3.13 >/dev/null 2>&1; then \
		python3.13 -m venv .ci-lint-env; \
		.ci-lint-env/bin/pip install --upgrade pip; \
		.ci-lint-env/bin/pip install flake8; \
		.ci-lint-env/bin/pip install -e ".[dev]"; \
		echo "Running flake8 (strict)..."; \
		.ci-lint-env/bin/flake8 ftf_cli tests --count --select=E9,F63,F7,F82 --show-source --statistics; \
		echo "Running flake8 (warnings)..."; \
		.ci-lint-env/bin/flake8 ftf_cli tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics; \
		rm -rf .ci-lint-env; \
		echo "✓ CI lint workflow completed successfully"; \
	else \
		echo "Python 3.13 not found. Install it first with 'make install-python-versions'"; \
		exit 1; \
	fi

# Run exact CI test workflow locally
ci-test: create-tox-config
	@echo "Running CI test workflow locally..."
	@for version in $(PYTHON_VERSIONS); do \
		echo ""; \
		echo "=== Testing with Python $$version ==="; \
		if command -v python$$version >/dev/null 2>&1; then \
			python$$version -m venv .ci-test-env-$$version; \
			.ci-test-env-$$version/bin/pip install --upgrade pip; \
			.ci-test-env-$$version/bin/pip install pytest pytest-mock; \
			.ci-test-env-$$version/bin/pip install -e ".[dev]"; \
			.ci-test-env-$$version/bin/python -m pytest; \
			rm -rf .ci-test-env-$$version; \
			echo "✓ Python $$version tests passed"; \
		else \
			echo "✗ Python $$version not found"; \
		fi; \
	done
	@echo ""
	@echo "✓ All CI test workflows completed"

clean:
ifeq ($(OS),Windows)
	@if exist env (rmdir /S /Q env)
	@if exist ftf_cli.egg-info (rmdir /S /Q ftf_cli.egg-info)
	@if exist build (rmdir /S /Q build)
	@if exist dist (rmdir /S /Q dist)
	@if exist .pytest_cache (rmdir /S /Q .pytest_cache)
	@if exist .tox (rmdir /S /Q .tox)
	@for /r %%i in (__pycache__) do @if exist "%%i" (rmdir /S /Q "%%i")
else
	rm -rf env ftf_cli.egg-info build dist .pytest_cache .tox
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
endif

clean-all: clean
	rm -rf $(VENV_DIR) .ci-*-env-* tox.ini .python-version
	@echo "Cleaned all environments and configurations"

all: setup dev test
