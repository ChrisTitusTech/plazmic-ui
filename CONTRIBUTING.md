# Contributing to Plazmic UI

Thank you for improving Plazmic UI. Contributions should make the distributed
skin or local UI editing safer and clearer without weakening the asset, privacy,
path, or publish boundaries.

## Before opening an issue

- Read the [user guide](docs/user-guide.md) and
  [troubleshooting guide](docs/troubleshooting.md).
- Confirm the problem occurs on current `main`.
- Include your operating system, source or packaged version, browser family,
  game runner, command, and redacted error category.
- Do not attach local or unreviewed game assets, `UI_*.ini` files, Wine-prefix
  contents, character names, account data, crash dumps, credentials, or
  absolute personal paths. Reference an existing tracked bundle file by path.
- Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## Scope

In scope: the reviewed UI bundle, capture, local materialization, layout/XML
editing, validation, backups, safe publish, accessibility, documentation, Linux
source compatibility, and Linux/Windows Studio packaging.

Out of scope: character layouts or user data in the bundle, a proprietary-
texture renderer, macOS packaging, binary patching, code injection, macros,
gameplay automation, synthesized input, multibox control, and gameplay changes.

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

Never run review services over ignored local game files. Reviewed bundle
changes may be inspected from the public Git diff only after the privacy and
repository hygiene gates pass.

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
project's [GNU General Public License v3.0 only](LICENSE). This grant does not
apply to any third-party asset. Third-party assets require documented
provenance and express written redistribution authorization before inclusion in
the bundle; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
