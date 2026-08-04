# Contributing to Plazmic UI

Thank you for improving Plazmic UI. Contributions should make local UI editing
safer and clearer without weakening the asset, path, or publish boundaries.

## Before opening an issue

- Read the [user guide](docs/user-guide.md) and
  [troubleshooting guide](docs/troubleshooting.md).
- Confirm the problem occurs on current `main`.
- Include your operating system, source or packaged version, browser family,
  game runner, command, and redacted error category.
- Do not attach game assets, `UI_*.ini` files, Wine-prefix contents, character
  names, account data, crash dumps, credentials, or absolute personal paths.
- Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## Scope

In scope: capture, local materialization, layout/XML editing, validation,
backups, safe publish, accessibility, documentation, Linux source
compatibility, and Linux/Windows Studio packaging.

Out of scope: bundled game files, a proprietary-texture renderer, macOS
packaging, binary patching, code injection, macros, gameplay automation,
synthesized input, multibox control, and changes to gameplay state.

## Development workflow

1. Fork the repository and create a focused branch from `main`.
2. Read [AGENTS.md](AGENTS.md), [SPEC.md](SPEC.md), and
   [docs/development.md](docs/development.md).
3. Add deterministic synthetic coverage for behavior changes.
4. Run the complete gate:

   ```bash
   make check
   ```

5. Inspect `git status`, the complete diff, ignored files, and executable bits.
6. Include a screenshot for visible changes using only synthetic or redacted
   local data.

Never run review services over ignored game files. A normal review should see
only the public Git diff.

## Style

- Keep shell scripts POSIX `sh`, quoted, ShellCheck-clean, and shfmt-clean.
- Support Python 3.11+ and keep Python source Ruff-clean.
- Use plain browser APIs; the Studio intentionally has no package manager or
  generated bundle.
- Keep documentation lines within 100 characters where practical.
- Use simple ASCII punctuation unless a file format requires otherwise.
- Document any new dependency, its license, purpose, and removal impact.

## License

By contributing, you agree that your contribution is licensed under the
project's [GNU General Public License v3.0 only](LICENSE).
