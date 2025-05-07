OS := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(OS),Windows)
  PYTHON := $(shell where python3 2>NUL || echo "")
else
  PYTHON := $(shell which python3 2>/dev/null || echo "")
endif

ifeq ($(PYTHON),)
  $(error "Python is not installed. Please install Python 3.")
endif

.PHONY: setup install test all clean

setup:
ifeq ($(OS),Windows)
	"$(PYTHON)" -m venv env
	@if not exist env\Scripts\activate ( \
		echo "Virtual environment creation failed. Check Python installation." && exit 1 \
	)
	env\Scripts\python.exe -m pip install --upgrade pip && \
	curl -s -o rustup-init.exe https://win.rustup.rs && \
	rustup-init.exe -y && \
	del rustup-init.exe && \
	env\Scripts\pip install -r requirements.txt
else
	"$(PYTHON)" -m venv env
	@if [ ! -f "./env/bin/activate" ]; then \
		echo "Virtual environment creation failed. Check Python installation." && exit 1; \
	fi
	./env/bin/python3 -m pip install --upgrade pip && \
	source "./env/bin/activate" && \
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
	source "$(HOME)/.cargo/env" && \
	./env/bin/pip install -r requirements.txt
endif

install:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\pip.exe ( \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1 \
	)
	env\Scripts\pip install .
else
	@if [ ! -f "./env/bin/pip" ]; then \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1; \
	fi
	source "./env/bin/activate" && pip install .
endif

test:
ifeq ($(OS),Windows)
	@if not exist env\Scripts\pip ( \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1 \
	)
	env\Scripts\pip install pytest && \
	env\Scripts\pytest tests
else
	@if [ ! -f "./env/bin/pip" ]; then \
		echo "Virtual environment not found. Run 'make setup' first." && exit 1; \
	fi
	source "./env/bin/activate" && \
	pip install pytest && \
	pytest tests
endif

clean:
ifeq ($(OS),Windows)
	@if exist env (rmdir /S /Q env)
else
	rm -rf env
endif

all: setup test install
