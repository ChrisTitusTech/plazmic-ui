# Security policy

## Supported versions

Security fixes target the current `main` branch and the latest tagged Studio
release.

## Reporting a vulnerability

Use GitHub's private **Report a vulnerability** flow for this repository. Do
not open a public issue for path traversal, arbitrary file access, token
bypass, unsafe publish, or private-data exposure.

Include the affected commit, operating system, Python version, a minimal
synthetic reproduction, and impact. Never include real game assets, personal
layouts, account data, credentials, character names, or an unredacted Wine
path.

## Security boundary

The Studio binds to `127.0.0.1`, uses an unguessable process-local API token,
checks the request Host and any supplied Origin, and applies a 10 MiB request
limit. It is a local development server, not a hardened multi-user web service.
Do not expose it through a reverse proxy, container port publish, SSH remote
forward, or non-loopback bind.

File operations are deliberately narrow:

- reads come from the selected local skin and layout workspaces;
- XML access is limited to top-level regular `.xml` files;
- game writes target only `uifiles/plazmic-ui` and one selected existing
  top-level `UI_*.ini`;
- source and target symlinks are rejected; and
- existing targets are backed up before replacement, with rollback on a
  partial publish failure.

Packaged Studio workspaces live under the current user's local application-data
directory unless `PLAZMIC_UI_DATA_DIR` explicitly selects another root. Release
binaries contain no game files or user data.

The project does not patch the game, inject code, automate gameplay, synthesize
input, access credentials, or change gameplay state.

## Private-data response

If private data is committed or attached publicly:

1. Remove public access to the affected artifact immediately.
2. Revoke and rotate any exposed credential immediately; history cleanup does
   not make an exposed credential safe again.
3. Preserve a private incident record with the affected paths and commits.
4. For committed sensitive data, use GitHub's supported removal process to
   purge only affected objects and references, coordinate cached clones and
   forks, and preserve unrelated repository history.
5. Publish a reviewed follow-up that restores the repository hygiene gate.
6. Notify affected users when exposure extends beyond the reporter.
