# ===== Cross-platform Makefile (pip + venv) =====

SHELL := /bin/sh

# Detect Windows vs *nix
ifeq ($(OS),Windows_NT)
	PY := .venv\Scripts\python.exe
	PIP := .venv\Scripts\pip.exe
	UVICORN := .venv\Scripts\uvicorn.exe
	VENV_EXISTS := $(wildcard .venv\Scripts\python.exe)
	PY_BOOT := py -3.11d
else
	PY := .venv/bin/python
	PIP := .venv/bin/pip
	UVICORN := .venv/bin/uvicorn
	VENV_EXISTS := $(wildcard .venv/bin/python)
	PY_BOOT := python3
endif

API_DEPS = "fastapi>=0.111" "uvicorn[standard]>=0.30" "pydantic>=2.7"
DEV_DEPS = "black>=24.8.0" "ruff>=0.6.9" "mypy>=1.11" "pytest>=8.3"

.PHONY: help setup venv api js-setup js-dev fmt lint type test clean clean-py lock sync install-all precommit check

help:
	@echo "Targets:"
	@echo "  make setup     - Create venv and install deps (API + dev) + JS deps"
	@echo "  make api       - Run FastAPI dev server (http://localhost:8080/health)"
	@echo "  make js-setup  - Install JS deps for apps/demo"
	@echo "  make js-dev    - Run Vite dev server for demo"
	@echo "  make fmt       - Format Python code with black"
	@echo "  make lint      - Lint Python with ruff"
	@echo "  make type      - Type-check with mypy"
	@echo "  make test      - Run pytest (packages/evals if present)"
	@echo "  make clean     - Remove venv and node_modules"
	@echo "  make clean-py  - Remove Python caches"
	@echo "  make lock      - Compile requirements.txt from *.in using pip-tools"
	@echo "  make sync      - Install pinned versions from requirements.txt"
	@echo "  make precommit - Run pre-commit hooks on all files"
	@echo "  make check     - Run fmt, lint, type"

setup: venv
	@echo "==> Installing Python deps"
	$(PIP) install $(API_DEPS) $(DEV_DEPS)
	@$(MAKE) js-setup

venv:
ifndef VENV_EXISTS
	@echo "==> Creating virtualenv"
	$(PY_BOOT) -m venv .venv
else
	@echo "==> Virtualenv already exists"
endif

api: venv
	@echo "==> Running FastAPI (Ctrl+C to stop)"
	$(UVICORN) apps.api.app.main:app --host 0.0.0.0 --port 8080 --reload

js-setup:
	@echo "==> Installing JS deps (apps/demo)"
	cd apps/demo && corepack enable && corepack prepare pnpm@9.6.0 --activate && pnpm install

js-dev:
	@echo "==> Starting Vite dev server (Ctrl+C to stop)"
	cd apps/demo && pnpm dev

fmt:
	@echo "==> black"
	-$(PY) -m black apps packages || true

lint:
	@echo "==> ruff"
	-$(PY) -m ruff check apps packages || true

type:
	@echo "==> mypy"
	-$(PY) -m mypy apps packages || true

test:
	@echo "==> pytest"
	-$(PY) -m pytest -q packages/evals || true

clean:
	@echo "==> Removing venv and node_modules"
	@rm -rf .venv || rmdir /S /Q .venv 2>nul || true
	@rm -rf apps/**/node_modules || true

clean-py:
	@echo "==> Removing Python caches"
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true

# === Dependency management (pip-tools + pre-commit) ===

PIP_COMPILE := $(PY) -m piptools compile
PRECOMMIT := $(PY) -m pre_commit

lock:
	@echo "==> Compiling lockfiles with pip-tools"
	$(PIP_COMPILE) --strip-extras apps/api/requirements.in        -o apps/api/requirements.txt
	$(PIP_COMPILE) --strip-extras packages/agents/requirements.in -o packages/agents/requirements.txt
	$(PIP_COMPILE) --strip-extras packages/tools/requirements.in  -o packages/tools/requirements.txt
	$(PIP_COMPILE) --strip-extras packages/memory/requirements.in -o packages/memory/requirements.txt
	$(PIP_COMPILE) --strip-extras packages/evals/requirements.in  -o packages/evals/requirements.txt
	$(PIP_COMPILE) --strip-extras requirements-dev.in             -o requirements-dev.txt

sync:
	@echo "==> Installing pinned versions"
	$(PIP) install -r apps/api/requirements.txt
	$(PIP) install -r packages/agents/requirements.txt
	$(PIP) install -r packages/tools/requirements.txt
	$(PIP) install -r packages/memory/requirements.txt
	$(PIP) install -r packages/evals/requirements.txt
	$(PIP) install -r requirements-dev.txt

install-all: venv lock sync

precommit:
	@echo "==> Running pre-commit hooks"
	$(PRECOMMIT) run --all-files

check: fmt lint type

# === Dataset utilities ===
DATASETS = packages/evals/datasets

.PHONY: datasets-validate datasets-build

# Validate all role datasets against schema
datasets-validate:
	python $(DATASETS)/tools/validate.py \
		$(DATASETS)/researcher.jsonl \
		$(DATASETS)/writer.jsonl \
		$(DATASETS)/editor.jsonl

# Convert all role datasets into TRL-style chat JSONL
datasets-build:
	@mkdir -p $(DATASETS)/out
	python $(DATASETS)/tools/to_trl.py $(DATASETS)/out/researcher.chat.jsonl $(DATASETS)/researcher.jsonl
	python $(DATASETS)/tools/to_trl.py $(DATASETS)/out/writer.chat.jsonl     $(DATASETS)/writer.jsonl
	python $(DATASETS)/tools/to_trl.py $(DATASETS)/out/editor.chat.jsonl     $(DATASETS)/editor.jsonl
