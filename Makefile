PYTHON := $(shell command -v python || command -v python3 || echo "")

ifeq ($(PYTHON),)
  $(error "Python is not installed. Please install Python 3.")
endif

.PHONY: setup install test

setup:
	$(PYTHON) -m venv env
	source "./env/bin/activate"
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	source "$(HOME)/.cargo/env"
	$(PYTHON) -m pip install -r requirements.txt

install: setup
	pip install .

test: setup
	pip install pytest
	pytest tests

all: setup test install