OS := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(OS),Windows)
  PYTHON := $(shell where python3 2>NUL || echo "")
  PYTHON_EXE := env\Scripts\python.exe
  PIP := env\Scripts\pip.exe
  PYTEST := env\Scripts\pytest.exe
else
  PYTHON := $(shell which python3 2>/dev/null || echo "")
  PYTHON_EXE := ./env/bin/python3
  PIP := ./env/bin/pip
  PYTEST := ./env/bin/pytest
endif

ifeq ($(PYTHON),)
  $(error "Python is not installed. Please install Python 3.")
endif

.PHONY: setup install dev test test-unit test-commands test-integration lint format clean all

setup:
ifeq ($(OS),Windows)
	"$(PYTHON)" -m venv env
	@if not exist env\Scripts\activate ( \
		echo "Virtual environment creation failed. Check Python installation." && exit 1 \
	)
	$(PYTHON_EXE) -m $(PIP) install --upgrade pip
else
	"$(PYTHON)" -m venv env
	@if [ ! -f "./env/bin/activate" ]; then \
		echo "Virtual environment creation failed. Check Python installation." && exit 1; \
	fi
	$(PYTHON_EXE) -m $(PIP) install --upgrade pip
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
else
	@if [ ! -f "./env/bin/pip" ]; then \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1; \
	fi
	$(PIP) install -e ".[dev]"
endif

test:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\pip ( \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1 \
	)
	$(PYTEST) tests
else
	@if [ ! -f "./env/bin/pip" ]; then \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1; \
	fi
	$(PYTEST) tests
endif

test-unit:
ifeq ($(OS),Windows)
	$(PYTEST) tests/test_*.py
else
	$(PYTEST) tests/test_*.py
endif

test-commands:
ifeq ($(OS),Windows)
	$(PYTEST) tests/commands/
else
	$(PYTEST) tests/commands/
endif

test-integration:
ifeq ($(OS),Windows)
	$(PYTEST) tests/integration/
else
	$(PYTEST) tests/integration/
endif

lint:
ifeq ($(OS),Windows)
	$(PIP) install flake8 && \
	env\Scripts\flake8 ftf_cli tests
else
	(PIP) install flake8 && flake8 ftf_cli tests
endif

format:
ifeq ($(OS),Windows)
	$(PIP) install black && \
	env\Scripts\black ftf_cli tests
else
	$(PIP) install black && black ftf_cli tests
endif

clean:
ifeq ($(OS),Windows)
	@if exist env (rmdir /S /Q env)
	@if exist ftf_cli.egg-info (rmdir /S /Q ftf_cli.egg-info)
	@if exist build (rmdir /S /Q build)
	@if exist dist (rmdir /S /Q dist)
	@if exist .pytest_cache (rmdir /S /Q .pytest_cache)
	@for /r %%i in (__pycache__) do @if exist "%%i" (rmdir /S /Q "%%i")
else
	rm -rf env ftf_cli.egg-info build dist .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
endif

all: setup dev test
