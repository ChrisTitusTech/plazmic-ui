SHELL := /bin/sh

PYTHON_FILES := \
	tests/test_plazmic_ui_tools.py \
	tools/check_repository.py \
	ui-tools/apply-improvements.py \
	ui-tools/format_xml.py \
	ui-tools/lint-ui.py \
	ui-tools/ui_studio.py
SHELL_FILES := \
	plazmic-ui \
	ui-tools/format-ui.sh \
	ui-tools/install-ui.sh \
	ui-tools/plazmic-ui \
	ui-tools/sync-ui.sh
MARKDOWN_FILES := \
	.github/pull_request_template.md \
	AGENTS.md \
	CODE_OF_CONDUCT.md \
	CONTRIBUTING.md \
	README.md \
	ROADMAP.md \
	SECURITY.md \
	SPEC.md \
	TASKS.md \
	docs/*.md

.PHONY: help sync refresh capture studio format lint install-dry-run install publish test shellcheck shfmt ruff pycompile markdownlint hygiene check

help:
	@printf '%s\n' \
		'Plazmic UI targets:' \
		'  capture          Capture an installed skin and layout' \
		'  studio           Open the local browser Studio' \
		'  publish          Publish workspace changes with backups' \
		'  sync             Derive a fresh skin from default_modern' \
		'  refresh          Rebuild the derived skin with a backup' \
		'  install-dry-run  Validate the offline install target' \
		'  install          Install while EverQuest is stopped' \
		'  check            Run the complete contributor gate'

sync:
	./plazmic-ui sync

refresh:
	./plazmic-ui sync --refresh

capture:
	./plazmic-ui capture

studio:
	./plazmic-ui studio

format:
	./plazmic-ui format

lint:
	@if [ -d .plazmic-ui-workspace/skin ]; then ./plazmic-ui lint; else printf '%s\n' 'Skipping local UI lint: the private skin workspace is not materialized.'; fi

install-dry-run:
	./plazmic-ui install --dry-run

install:
	./plazmic-ui install

publish:
	./plazmic-ui publish

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v

shellcheck:
	shellcheck $(SHELL_FILES)

shfmt:
	shfmt -d -i 2 -ci $(SHELL_FILES)

ruff:
	ruff check $(PYTHON_FILES)
	ruff format --check $(PYTHON_FILES)

pycompile:
	python3 -m py_compile $(PYTHON_FILES)

markdownlint:
	markdownlint-cli2 $(MARKDOWN_FILES)

hygiene:
	python3 tools/check_repository.py
	git diff --check
	git diff --cached --check

check: shellcheck shfmt ruff pycompile test markdownlint hygiene lint
