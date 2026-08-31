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

## Phase 4: First packaged Studio release

### Outcome

Users can download a one-file Studio executable for x86-64 Linux or Windows
without installing Python or cloning the repository.

### Included work

- Make runtime resource and private workspace discovery frozen-app aware.
- Package only the Studio Python code and static frontend with PyInstaller.
- Build and smoke-test each executable on its target operating system.
- Publish versioned release notes, both binaries, and SHA-256 checksums.

### Dependencies and risks

- PyInstaller is a build-time dependency pinned for the release workflow; a
  packager update requires a new binary review and smoke test.
- One-file executables extract runtime components to an operating-system temp
  directory while running.
- The packaged Studio excludes Linux shell-only sync, format, lint, and offline
  install commands.

### Exit criteria

- AC-11 passes on both target runners.
- A manual workflow run verifies both artifacts before tagging.
- The `v0.1.0` release exists publicly and its assets match `SHA256SUMS`.

### Validation

- Run the complete source gate and a local Linux package smoke test.
- Run source tests, version validation, binary format/size checks, and bundled
  frontend diagnostics on Linux and Windows GitHub runners.
- Download the published assets, verify checksums and executable formats, and
  run the Linux binary locally.

### Rollback

If an artifact is invalid, mark the release as affected, publish a corrected
patch version, and retain the original tag for auditability. Never replace a
published binary silently.

## Phase 5: Layout interaction improvements

### Outcome

The Studio canvas stays focused while filtering and supports predictable grid
alignment during drag and resize operations.

### Included work

- Apply the same visibility and case-insensitive name filter to the layout list
  and mock canvas.
- Add an enabled-by-default selectable snap grid for moving and resizing.
- Allow fine positioning by disabling snapping or holding Alt while dragging.
- Add deterministic frontend model tests and update the user workflow.

### Dependencies and risks

- Snapping changes only unsaved browser state until the user explicitly saves
  the selected INI section.
- The canvas remains a layout mock and cannot prove exact in-game rendering.

### Exit criteria

- AC-12 passes in automated model tests and a visible Studio smoke test.
- The complete repository gate and independent review complete without an
  unresolved critical or warning finding.

### Validation

- Exercise matching, nonmatching, and hidden filters against list and canvas.
- Exercise move and resize at every grid size, with snapping disabled, and with
  Alt held.
- Run `make check` and retain an ignored screenshot under `captures/`.

### Rollback

Revert the frontend model and controls. No workspace migration or INI rollback
is required because the new controls do not write until the existing save
action is used.

## Phase 6: Multi-window layout tools

### Outcome

Authors can select a group of mock windows and normalize their size, alignment,
or spacing without manually editing each set of coordinates.

### Included work

- Add Shift-click multi-selection on the canvas and layout list with a stable
  primary selection for the inspector.
- Move selected windows as one group while preserving relative spacing.
- Match size, align left or top, and distribute horizontally or vertically.
- Save all selected sections through one validated atomic INI update.

### Dependencies and risks

- Group actions change in-browser geometry for multiple windows; the action
  names and primary reference must remain explicit.
- Equal distribution can retain overlap when the selected bounding span is
  smaller than the combined window dimensions.

### Exit criteria

- AC-13 passes deterministic geometry, batch-save, and browser interaction
  tests.
- A visible synthetic-data capture demonstrates group selection and tools.
- The complete gate and independent review pass on the final diff.

### Validation

- Exercise Shift-add, Shift-remove, primary selection, group drag, and filtered
  selection rendering.
- Verify match-size, align, and both distribution algorithms with mixed sizes.
- Verify batch save creates one backup and changes only selected INI sections.
- Run `make check`, packaged Linux diagnostics, and a 1920x1080 browser smoke.

### Rollback

Revert the group-selection frontend, model helpers, and batch endpoint. Existing
single-window saves and backups remain compatible; no workspace migration is
required.

## Phase 7: Paired game-layout load and save

### Outcome

The top-right game-layout controls make both file directions explicit without
requiring a separate terminal capture command.

### Included work

- Rename the existing publish action to **Save to game**.
- Add **Load from game** for the selected existing `UI_*.ini`.
- Back up the current workspace layout before an atomic load.
- Reject symlinks, path escapes, oversized layouts, empty layouts, and files
  that change while being read.

### Exit criteria and validation

- AC-14 passes symlink, path-escape, oversized, empty, unstable-read, function,
  authenticated API, frontend syntax, and full-gate validation.
- A public-safe ignored screenshot shows the paired top-right controls.

### Rollback

Restore the timestamped workspace backup produced by Load from game. The load
action never changes the selected game file.

## Phase 8: Stable layout-save defaults

### Outcome

Centered windows retain their exact placement when saved, while the Studio
uses the requested 16-pixel default grid and provides a quick way to clear a
multi-window selection.

### Included work

- Share the exact Legends anchor conversions between frontend behavior and
  deterministic model tests.
- Preserve six-decimal positions through selection, drag, and save.
- Change the enabled snap-grid default from 8 to 16 pixels.
- Show **Deselect all** only with a multi-window selection and clear both the
  group and primary selection when invoked.

### Exit criteria and validation

- BagInv8's centered anchor round-trips without movement in model and Python
  tests.
- The source Studio and packaged Linux binary contain the 16-pixel default and
  Deselect all action; AC-11's cross-platform embedded-frontend verification
  applies the same requirement to the next Windows x86-64 binary.
- The complete repository gate, visible browser check, binary verification,
  and independent review pass.

### Rollback

Revert the frontend model, controls, and documentation. Layout files require
no migration because the change uses the existing atomic save format.

## Phase 9: Distributable EverQuest UI bundle

### Outcome

Players can install the complete Plazmic UI skin directly from the repository
or a release ZIP without copying `default_modern`, while personal layouts and
character identifiers remain excluded.

### Included work

- Track the reviewed skin under `ui-bundle/plazmic-ui/`.
- Add bundle-specific privacy, file-type, lint, and archive validation.
- Publish `plazmic-ui-bundle.zip` separately from the Studio executables.
- Update ownership, provenance, installation, contribution, and security docs.

### Dependencies and risks

- Bundled game UI assets retain their third-party ownership and are not covered
  by the project's GPL license.
- Binary texture review cannot prove visual behavior; validation relies on the
  known source, strict inventory, XML lint, and in-game testing.
- The repository and CI checkout become substantially larger.

### Exit criteria

- AC-15 passes and no `UI_*.ini`, personal identifier, local path, sidecar,
  executable, symlink, or credential is present in the bundle.
- The generated archive has `plazmic-ui/` as its root and passes the same bundle
  verification as the tracked tree.
- The complete source gate passes on the exact committed asset set.

### Validation

- Compare the tracked tree byte-for-byte with the approved local skin while
  excluding only local metadata.
- Run bundle verification, XML formatting/lint, repository hygiene, secret and
  privacy scans, `make check`, and archive structure inspection.
- Record live `/loadskin plazmic-ui 1` validation separately when available.

### Rollback

Remove the bundle tree and release-archive step while retaining the Studio and
local materialization workflow. Remove any affected public artifact immediately
if private data is discovered.
