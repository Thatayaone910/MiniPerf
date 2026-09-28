PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
REQUIREMENTS_STAMP := $(VENV)/.requirements-installed

.PHONY: setup demo test

setup: $(REQUIREMENTS_STAMP)

$(REQUIREMENTS_STAMP): requirements.txt
	@if [ ! -x "$(VENV_PYTHON)" ]; then $(PYTHON) -m venv $(VENV); fi
	@if "$(VENV_PYTHON)" -m pip --version >/dev/null 2>&1; then \
		"$(VENV_PYTHON)" -m pip install -r requirements.txt; \
	elif command -v pip3 >/dev/null 2>&1; then \
		pip3 --python "$(VENV_PYTHON)" install -r requirements.txt; \
	else \
		echo "pip is missing from $(VENV); install Python's venv/pip support and retry." >&2; \
		exit 1; \
	fi
	@touch $@

demo: setup
	$(VENV)/bin/uvicorn app.main:app --reload

test: setup
	$(VENV)/bin/pytest -q
