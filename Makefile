SHELL := /bin/sh

PYTHON_FILES := \
	tests/test_plazmic_ui_tools.py \
	tools/check_repository.py \
	tools/release_version.py \
	tools/verify_ui_bundle.py \
	tools/verify_release_binary.py \
	ui-tools/apply-improvements.py \
	ui-tools/format_xml.py \
	ui-tools/lint-ui.py \
	ui-tools/ui_studio.py
JAVASCRIPT_FILES := \
	tests/test_studio_model.js \
	ui-tools/studio/app.js \
	ui-tools/studio/studio-model.js
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
	THIRD_PARTY_NOTICES.md \
	docs/*.md \
	docs/releases/*.md

.PHONY: help sync refresh capture studio format lint install-dry-run install publish studio-binary bundle-check bundle-archive test jscheck shellcheck shfmt ruff pycompile markdownlint hygiene check

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
		'  studio-binary    Build and verify the local Linux Studio binary' \
		'  bundle-check     Validate the distributable EverQuest UI bundle' \
		'  bundle-archive   Build the distributable UI bundle ZIP' \
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

studio-binary:
	python3 -m PyInstaller --clean --noconfirm plazmic-ui-studio.spec
	python3 tools/verify_release_binary.py \
		--platform linux \
		--version "$$(python3 tools/release_version.py)" \
		dist/plazmic-ui-studio

bundle-check:
	python3 tools/verify_ui_bundle.py ui-bundle/plazmic-ui
	python3 ui-tools/lint-ui.py --check-format ui-bundle/plazmic-ui

bundle-archive: bundle-check
	mkdir -p release-assets
	python3 -c "import shutil; shutil.make_archive('release-assets/plazmic-ui-bundle', 'zip', 'ui-bundle', 'plazmic-ui')"
	python3 tools/verify_ui_bundle.py \
		--archive release-assets/plazmic-ui-bundle.zip \
		ui-bundle/plazmic-ui

test:
	python3 -m unittest discover -s tests -p 'test_*.py' -v
	node --test tests/test_studio_model.js

jscheck:
	@for file in $(JAVASCRIPT_FILES); do \
		node --check "$$file" || exit 1; \
	done

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

check: shellcheck shfmt ruff pycompile jscheck test markdownlint hygiene bundle-archive lint
