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
- shfmt 3.10 or newer; and
- Markdownlint CLI2 0.23.x.

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
- CLI dispatch and shell failure paths.

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
2. Hidden-window filtering works.
3. Selection works from the list and canvas.
4. Drag, resize, field editing, and save create a backup.
5. XML open, invalid-save rejection, and valid save work.
6. Publish confirmation names the selected target.
7. A 1920x1080 screenshot contains no personal path or character data.

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
