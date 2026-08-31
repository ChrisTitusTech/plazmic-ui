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

`make bundle-check` verifies and lints both tracked installable packages.
`make bundle-archive` creates `release-assets/plazmic-ui-bundle.zip` with
`plazmic-ui/` as its archive root and `release-assets/aya-legends-bundle.zip`
with the upstream `uifiles/AYA_Legends/` plus generic layout structure. The
verifier compares each tree with its independent manifest, validates asset
formats, checksums, modes, allowlisted layouts, and privacy patterns, and
compares each completed archive with its source tree.

## Test design

Tests use temporary synthetic game roots, XML, layouts, sidecars, and textures.
No fixture comes from EverQuest. Coverage includes:

- reviewed Advanced Loot transformations;
- XML formatting and structural lint;
- anchor and resolution conversion;
- surgical INI replacement and backups;
- capture filters and symlink rejection;
- capture materialization of missing manifest XML from the default skin;
- XML/settings validation;
- transactional publish rollback;
- Host, token, Origin, and body-size server checks;
- CLI dispatch and shell failure paths;
- shared window filtering for the list and mock canvas;
- snapped move/resize geometry, disabled snapping, and Alt bypass behavior;
- exact left, center, and right anchor round trips at six-decimal precision;
- multi-window drag, size, alignment, and distribution geometry; and
- atomic multi-section INI updates and request validation.

Bundle coverage verifies both manifests and rejects unapproved `UI_*.ini`
layouts, backups, checksum sidecars, unexpected file types, symlinks, and
executable bits. Aya's exact generic layout is the sole layout exception.

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
5. Shift-click selects and removes group members from both list and canvas.
6. Group drag, match size, align, spacing, and Save selected work without
   changing an unselected window.
7. Deselect all appears for a group and clears every selected window.
8. BagInv8 remains stationary through an unchanged save and the default grid
   selector reads 16 pixels.
9. Field editing and save create a backup.
10. XML open, invalid-save rejection, and valid save work.
11. Publish confirmation names the selected target.
12. A 1920x1080 screenshot contains no personal path or character data.

## Review and release gate

Before committing:

1. Run `make check`.
2. Inspect `git status --short` and the complete diff.
3. Confirm every added asset belongs to one of the reviewed user-created UI
   packages and record its source and attribution.
4. Confirm ignored private paths are absent from `git ls-files` and all tracked
   game assets are confined to the two approved `ui-bundle/` roots.
5. Run the bundle, repository hygiene, privacy, and secret checks.
6. Review visible changes using an ignored screenshot.
7. Run independent review only after confirming the diff is public-safe.
8. Build the bundle archive and confirm its root and inventory.
9. Push the exact reviewed commit and verify hosted CI on that SHA.

Hosted CI cannot launch EverQuest. Record live `/loadskin` validation separately
and never attach a personal layout or locally modified asset.

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
The release workflow rebuilds and verifies both UI archives from their reviewed
manifests, then publishes them alongside the Studio executables and the release
checksum file.
