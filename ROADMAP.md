# Plazmic UI roadmap

## Phase 1: Standalone public foundation

### Outcome

Detach the generic UI tooling from Plazmic Legends into a clean public
repository with an explicit local-only asset boundary.

### Included work

- Establish the standalone repository, license, project instructions,
  specification, task tracker, security policy, and contributor workflow.
- Retain only original tooling, synthetic tests, and static Studio source.
- Remove companion-application code, history, packaging, and requirements.
- Add public CI and repository hygiene checks.

### Dependencies and risks

- The source worktree contains ignored Daybreak assets and personal INIs that
  must remain in the preserved old worktree and outside the new repository.
- GitHub repository creation and push are external state changes explicitly
  authorized by the owner.

### Exit criteria

- The new Git history has no Plazmic Legends implementation or private files.
- Project scope and asset ownership are unambiguous.
- A clean local gate passes before the first commit.

### Validation

- Inspect tracked and untracked files, history, ignore rules, file types,
  executable bits, and secret/private-data scans.
- Compare the public tree against the explicit allowlist of copied tooling.

### Rollback

The original dirty worktree and all local-only data remain preserved at its
backup path until the new repository is verified.

## Phase 2: Safe UI Studio workflow

### Outcome

Users can capture or materialize a local skin, edit an INI/XML workspace in a
browser, and publish intentional changes with rollback.

### Included work

- Harden CLI dispatch, path validation, sidecar filtering, and symlink rules.
- Support configurable canvas resolution and preserved INI semantics.
- Harden token/origin/body validation on the loopback Studio API.
- Make publish transactional across the skin and selected layout.
- Expand synthetic unit and failure-path coverage.

### Dependencies and risks

- EQ XML and INI behavior is only partially documented; preserve unknown data
  byte-for-byte and constrain edits to approved fields.
- The mock canvas cannot prove final in-game SIDL rendering.

### Exit criteria

- AC-02 through AC-06 pass.
- Practice render and safe local dry-run evidence are recorded.
- Live game validation is completed or explicitly reported as skipped.

### Validation

- Run focused unit tests, shell syntax/static checks, Ruff, and browser/API
  smoke tests before the complete gate.
- Exercise paths with spaces, malformed inputs, missing dependencies, symlinks,
  multiple layouts, publish rollback, and a running game process.

### Rollback

Local workspace saves and game publishes create timestamped backups. Users can
restore them or load `default_modern` without changing the shipped skin.

## Phase 3: Public release readiness

### Outcome

The repository is understandable, independently reviewed, reproducible, and
green on public `main`.

### Included work

- Complete user, contributor, architecture, security, troubleshooting, and
  development documentation.
- Run local and independent review loops to closure.
- Create the public GitHub repository, push the reviewed commit, and verify CI.

### Dependencies and risks

- CodeRabbit review transmits only the public-safe diff; secrets and private
  files must be audited before invoking it.
- Hosted CI cannot access EverQuest and validates only synthetic/source paths.

### Exit criteria

- AC-01 and AC-07 through AC-10 pass.
- Public `main` matches the exact locally reviewed commit.
- Hosted CI succeeds on that commit.

### Validation

- Run `make check`, inspect the full diff, run CodeRabbit iteratively, verify
  GitHub Actions on the exact SHA, and inspect the remote repository metadata.

### Rollback

If the first push has a normal code or documentation defect, keep the
repository public and correct it with a reviewed follow-up commit. If private
data leaks, immediately remove public access to the affected artifact and use
the provider's supported sensitive-data removal process to purge only affected
objects and references while preserving unrelated history. Credential
revocation and rotation is a separate immediate action even when history is
purged. Follow the incident steps in `SECURITY.md`.
