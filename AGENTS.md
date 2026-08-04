# Project instructions

## Purpose

Plazmic UI is a public toolkit for building and editing a local EverQuest
Legends UI. Its source workflow targets Linux, while GitHub releases package
the browser Studio as one-file Linux and Windows executables.
It copies UI source from the user's own game installation, previews and edits
`UI_*.ini` layouts in a loopback-only browser Studio, validates EQ XML, and
publishes explicit local changes with backups.

The repository never contains or distributes Daybreak assets, user layouts,
game binaries, Wine-prefix content, account data, or character data.

## Architecture

- `plazmic-ui`: public command-line entrypoint.
- `ui-tools/`: POSIX shell and Python implementation for sync, capture,
  formatting, linting, Studio serving, install, and publish operations.
- `ui-tools/studio/`: dependency-free HTML, CSS, and JavaScript browser client.
- `tests/`: synthetic unit and integration fixtures with no game content.
- `docs/`: user workflow, architecture, development, and security guidance.
- `.plazmic-ui-workspace/` contains the generated skin, layouts, backups, and
  local configuration; the entire directory must remain ignored.

The source workflow requires Linux, Python 3.11 or newer, a POSIX shell, GNU
coreutils, and `rsync`. Packaged Studio binaries target x86-64 Linux and
Windows. The Studio uses a current browser and binds only to `127.0.0.1`.

## Working boundaries

- Read `SPEC.md`, `ROADMAP.md`, and `TASKS.md` before changing behavior.
- Preserve unrelated user changes and local ignored workspaces.
- Never commit or print private UI assets, personal `UI_*.ini` contents, game
  paths, account data, character names, logs, crash dumps, or credentials.
- Never ship files copied from `default`, `default_modern`, or another installed
  Daybreak skin.
- Release binaries may contain only project source, the static Studio frontend,
  the Python runtime, and PyInstaller runtime components.
- Do not modify `default` or `default_modern` in place.
- Restrict writes to the local repository workspaces, `uifiles/plazmic-ui`, and
  one explicitly selected top-level `UI_*.ini`.
- Back up an existing target before replacement and fail closed on symlinks,
  invalid paths, malformed XML/INI data, or incomplete source trees.
- Do not patch binaries, inject code, automate gameplay, synthesize input, or
  alter game state.
- Add dependencies only when an approved requirement needs them; prefer the
  standard library and system tools.

## Commands

```bash
./plazmic-ui --help
make test
make lint
make check
```

Local game workflows require either `EQ_LEGENDS_DIR` or `--game-dir`:

```bash
EQ_LEGENDS_DIR='/path/to/EverQuest Legends' ./plazmic-ui capture
EQ_LEGENDS_DIR='/path/to/EverQuest Legends' ./plazmic-ui studio
EQ_LEGENDS_DIR='/path/to/EverQuest Legends' ./plazmic-ui publish
```

## Validation

- Run focused tests while implementing and `make check` before completion.
- Run ShellCheck and shfmt for every shell-script change.
- Run Ruff, Python compilation, and unit tests for every Python change.
- Run Markdownlint for documentation changes.
- Verify the browser Studio against synthetic or local ignored data and retain
  a screenshot under ignored `captures/` for visible changes.
- Inspect the final status, diff, ignored-file boundary, executable bits, and
  secret scan before committing.
- Record skipped live game validation and residual risk explicitly.

## Documentation routing

- Read `SPEC.md` for requirements and acceptance criteria.
- Read `ROADMAP.md` for phase order, exit criteria, and rollback.
- Read `TASKS.md` for current authorization and validation status.
- Read `docs/user-guide.md` for the supported end-user workflow.
- Read `docs/architecture.md` before changing trust boundaries or file flow.
- Read `SECURITY.md` before changing the Studio listener or publish behavior.
