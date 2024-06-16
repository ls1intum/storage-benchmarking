POETRY = $$(command -v poetry 2> /dev/null)
POETRY_INSTALL_STAMP = .poetry.install.stamp
POETRYDEV_INSTALL_STAMP = .poetrydev.install.stamp
PROJECT_DIR = src

.DEAFULT_GOAL := help

.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "  all               to perform all of the following"
	@echo "  lint              to lint python code"
	@echo "  static-analysis   to perform static type analysis"
	@echo "  format            to automatically format the python code"
	@echo ""
	@echo "Check the Makefile to know exactly what each target is doing."

.PHONY: all
all: lint static-analysis format

.PHONY: install
install: $(POETRY_INSTALL_STAMP)
$(POETRY_INSTALL_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install
	@touch $(POETRY_INSTALL_STAMP)

.PHONY: install-dev
install-dev: $(POETRYDEV_INSTALL_STAMP)
$(POETRYDEV_INSTALL_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install --with dev
	@touch $(POETRYDEV_INSTALL_STAMP)

.PHONY: lint
lint: install-dev $(PROJECT_DIR)
	$(POETRY) run pylint $(PROJECT_DIR)

.PHONY: static-analysis
static-analysis: install install-dev $(PROJECT_DIR)
	$(POETRY) run mypy $(PROJECT_DIR)

.PHONY: format
format: install-dev $(PROJECT_DIR)
	$(POETRY) run isort $(PROJECT_DIR)
	$(POETRY) run black $(PROJECT_DIR)

.PHONY: clean
clean:
	@find . -type d -name "__pycache__" -prune -print -exec rm -rf {} \;
	@find . -type d -name ".mypy_cache" -prune -print -exec rm -rf {} \;
	@rm -rf $(POETRY_INSTALL_STAMP) $(POETRYDEV_INSTALL_STAMP)
