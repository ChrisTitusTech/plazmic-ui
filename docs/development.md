# Development and validation

## Toolchain

Runtime dependencies:

- Python 3.11 or newer;
- POSIX `sh`;
- GNU coreutils and findutils;
- `rsync`; and
- a current browser for manual Studio validation.

Contributor dependencies:

- Ruff 0.15.21;
- ShellCheck 0.11 or newer;
- shfmt 3.10 or newer;
- Markdownlint CLI2 0.23.x; and
- Node.js 20 or newer for dependency-free frontend model tests.

Release builds additionally pin PyInstaller 6.21.0. PyInstaller must run on
each target operating system; it is not used by normal source execution.

On Fedora, install the available distribution packages for Python, `rsync`,
ShellCheck, shfmt, and Node.js, then install the pinned Markdownlint CLI2 used
by CI. On Ubuntu, the GitHub Actions workflow documents the required apt and
tool commands.

## Commands

```bash
make help
make test
make shellcheck
make shfmt
make ruff
make pycompile
make jscheck
make markdownlint
make hygiene
make check
```

`make lint` checks a materialized ignored skin when one exists and reports a
clear skip in a clean clone.

## Test design

Tests use temporary synthetic game roots, XML, layouts, sidecars, and textures.
No fixture comes from EverQuest. Coverage includes:

- reviewed Advanced Loot transformations;
- XML formatting and structural lint;
- anchor and resolution conversion;
- surgical INI replacement and backups;
- capture filters and symlink rejection;
- XML/settings validation;
- transactional publish rollback;
- Host, token, Origin, and body-size server checks; and
- CLI dispatch and shell failure paths;
- shared window filtering for the list and mock canvas; and
- snapped move/resize geometry, disabled snapping, and Alt bypass behavior.

Add a regression test for every behavior fix. Prefer a temporary filesystem
over mocks; use a narrow mock only to force an otherwise impractical failure.

## Manual Studio validation

Keep all local data ignored. Start the server without opening the primary
browser when capturing through an isolated browser profile:

```bash
./plazmic-ui studio --no-browser --port 41783
```

Verify at minimum:

1. The layout list and canvas populate.
2. Window-name and hidden-window filtering affect both list and canvas.
3. Selection works from the list and canvas.
4. Drag and resize snap at every grid size; disabling Snap or holding Alt
   allows free positioning.
5. Field editing and save create a backup.
6. XML open, invalid-save rejection, and valid save work.
7. Publish confirmation names the selected target.
8. A 1920x1080 screenshot contains no personal path or character data.

## Review and release gate

Before committing:

1. Run `make check`.
2. Inspect `git status --short` and the complete diff.
3. Confirm ignored private paths are absent from `git ls-files`.
4. Run the repository hygiene and secret checks.
5. Review visible changes using an ignored screenshot.
6. Run independent review only after confirming the diff is public-safe.
7. Push the exact reviewed commit and verify hosted CI on that SHA.

Hosted CI cannot access EverQuest. Record live `/loadskin` validation separately
and never attach its assets or personal layout.

## Build a Studio executable

Install the pinned build dependency into an isolated environment, then use the
reviewed spec file:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install pyinstaller==6.21.0
python -m PyInstaller --clean --noconfirm plazmic-ui-studio.spec
python tools/verify_release_binary.py \
  --platform linux --version "$(python tools/release_version.py)" \
  dist/plazmic-ui-studio
```

PyInstaller is not a cross-compiler. The release workflow builds the Windows
`.exe` on a Windows runner and the ELF binary on a Linux runner. A manual
workflow dispatch builds and smoke-tests both without creating a release. A
matching `vMAJOR.MINOR.PATCH` tag publishes only after both jobs pass.
