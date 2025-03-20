PYTHON := $(shell command -v python || command -v python3 || echo "")

ifeq ($(PYTHON),)
  $(error "Python is not installed. Please install Python 3.")
endif

.PHONY: init install test

init:
	$(PYTHON) -m venv env
	source "./env/bin/activate"
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	source "$(HOME)/.cargo/env"

install: init
	pip install .

test: init
	pip install pytest
	pytest tests