# Plazmic UI tasks

Task status changes only after acceptance criteria and validation pass. Record
skipped live checks and residual risk rather than marking them complete.

## Current phase

### B-02: Add Aya distribution and multi-skin selection

- [x] Track the reviewed Aya skin and exact generic layout with an independent
  checksum inventory.
- [x] Add separate verified Plazmic and Aya release archives.
- [x] Add allowlisted, remembered Plazmic/Aya selection across capture, Studio,
  install, publish, and reload instructions.
- [x] Add bundle-specific XML, privacy, mode, layout, and archive validation.
- [x] Update attribution, installation, development, security, and rollback
  documentation.
- [x] Pass real local capture for both skins, the complete source gate, and the
  final diff/privacy review.
- Acceptance criteria: AC-16 and the Phase 10 exit criteria.
- Automated validation: selector and target-routing tests, both bundle
  verifiers, generic/Plazmic XML checks, exact archive comparison, repository
  hygiene, privacy scan, Markdownlint, Python checks, and `make check`.
- Manual validation: capture both installed skins without game writes; live
  `/loadskin plazmic-ui 1` and `/loadskin AYA_Legends 1` remain separate.

B-02 added 1,681 normalized Aya package files plus an independent checksum
inventory and verified archive. Real Aya capture and offline-install dry-run
passed against the installed tree; the existing real Plazmic capture also
passed its selected structural profile. The complete gate passed with 62
Python tests, 12 frontend tests, both bundle/archive inventories, 258 Plazmic
XML files, 268 Aya XML files, and repository/privacy checks. Live `/loadskin`
was skipped to avoid changing game state; in-game rendering remains the
residual risk.

### B-01: Distribute the complete Plazmic UI skin

- [x] Track the reviewed skin as `ui-bundle/plazmic-ui/`.
- [x] Exclude character layouts, identifiers, local paths, sidecars,
  executables, symlinks, credentials, and local provenance metadata.
- [x] Add bundle validation and a separate release ZIP.
- [x] Update the specification, ownership, installation, contribution, and
  security boundaries.
- [x] Pass the complete source, bundle, archive, privacy, and repository gates.
- Acceptance criteria: AC-15 and the Phase 9 exit criteria.
- Automated validation: bundle verifier, EQ XML lint, archive inventory,
  byte-for-byte source comparison, repository hygiene, secret/privacy scan,
  Markdownlint, Python checks, and `make check`.
- Manual validation: install the ZIP's `plazmic-ui/` directory under `uifiles/`
  and run `/loadskin plazmic-ui 1`, or record the skipped live check and risk.

### S-05: Stabilize centered saves and selection defaults

- [x] Keep BagInv8 and other center-anchored windows position-stable across an
  unchanged save.
- [x] Default the enabled snap grid to 16 pixels.
- [x] Show **Deselect all** for multi-window selections and clear selection
  safely.
- [x] Complete the source gate, visible Studio check, packaged Linux binary,
  and independent review.
- Acceptance criteria: centered anchors round-trip at six decimals without
  movement, the enabled grid starts at 16 pixels, and Deselect all clears both
  the primary and grouped selections, per Phase 8 and updated AC-12/AC-13.
- Automated validation: exact BagInv8 Python/frontend anchor assertions, the
  16-pixel default and empty-selection model assertions, syntax, source gate,
  and packaged-binary diagnostics.
- Manual validation: verify BagInv8, the 16-pixel selector, and Deselect all in
  the loopback Studio without publishing to the game.

### S-04: Add paired game-layout load and save

- [x] Add **Load from game** beside the renamed **Save to game** action.
- [x] Load the selected existing `UI_*.ini` into the workspace atomically with
  a local backup and stable-read validation.
- [x] Cover the file operation and authenticated API route with synthetic data.
- [x] Complete the visible screenshot and full repository gate.
- Acceptance criteria: AC-14 and the Phase 7 exit criteria.
- Automated validation: authenticated load API tests, stable-read and backup
  tests, frontend syntax checks, and `make check`.
- Manual validation: retain an ignored public-safe screenshot of the paired
  top-right actions under `captures/`.

### S-03: Add multi-window layout tools

- [x] Add Shift-click multi-selection with a stable primary window.
- [x] Move groups without changing their internal spacing.
- [x] Add match-size, align-left/top, and equal-spacing actions.
- [x] Save selected sections atomically with one backup.
- [x] Add model, API, browser, documentation, and packaged-app validation.
- Acceptance criteria: AC-13 and the Phase 6 exit criteria.
- Automated validation: frontend geometry tests, batch INI tests, API tests,
  JavaScript syntax, Python tests, and `make check`.
- Manual validation: exercise group tools at 1920x1080 against synthetic data
  and retain an ignored public-safe screenshot under `captures/`.

### S-02: Improve Studio layout interactions

- [x] Hide nonmatching mock windows when the layout list is filtered.
- [x] Add selectable grid snapping for move and resize with an Alt bypass.
- [x] Preserve unsaved sibling positions when one window section is saved.
- [x] Add deterministic frontend coverage and update user documentation.
- [x] Pass visible Studio validation, the complete gate, and review.
- Acceptance criteria: AC-12 and the Phase 5 exit criteria.
- Automated validation: Node model tests, JavaScript syntax checks, Python
  tests, and `make check`.
- Manual validation: confirm filter and snap behavior with ignored local data
  and retain a public-safe screenshot under ignored `captures/`.

### P-01: Package and publish Studio 0.1.0

- [x] Make Studio resources and private storage work in frozen applications.
- [x] Add versioned PyInstaller builds for x86-64 Linux and Windows.
- [x] Document binary installation, scope, checksums, and workspace locations.
- [x] Pass the local Linux artifact build and smoke test.
- [x] Pass hosted Linux and Windows artifact smoke tests.
- [x] Review, push, tag `v0.1.0`, publish the release, and verify every asset.
- Acceptance criteria: AC-11 and the Phase 4 exit criteria.
- Automated validation: `make check`, PyInstaller build, binary verifier,
  GitHub Actions matrix, release checksum verification, and artifact audit.
- Manual validation: launch the Linux binary against ignored local data;
  Windows browser/game interaction remains separate from runner smoke tests.

### F-01: Establish the standalone public repository

- [x] Create a clean `main` history with only public-safe UI tooling.
- [x] Add project planning, license, security, contributor, and CI files.
- [x] Confirm the old Plazmic Legends worktree and private files remain outside
  the new repository.
- Acceptance criteria: AC-01 and the Phase 1 exit criteria.
- Automated validation: repository inventory, history, ignore, secret, and
  private-data audits.
- Manual validation: inspect the old backup and new repository roots.

### S-01: Harden the Studio and file workflow

- [x] Add configurable canvas dimensions with validated bounds.
- [x] Require token and loopback-origin checks for API access.
- [x] Reject unsafe paths, symlinks, invalid lengths, and incomplete skins.
- [x] Make game publish transactional with rollback.
- Acceptance criteria: AC-02 through AC-06.
- Automated validation: focused unit/API tests and shell failure-path tests.
- Manual validation: load the ignored local layout in the Studio and save a
  disposable copied section/XML file.

### D-01: Complete public documentation and contributor tooling

- [x] Document quick start, both creation workflows, Studio controls, publish,
  rollback, troubleshooting, architecture, security, and development.
- [x] Add a complete `make check` gate and public GitHub Actions workflow.
- Acceptance criteria: AC-07 and AC-08.
- Automated validation: Markdownlint, command-help tests, and CI syntax review.
- Manual validation: follow the quick start from a clean repository state.

### R-01: Review and publish

- [x] Produce and inspect a 1920x1080 practice Studio render.
- [x] Run the complete local gate and public-safe secret/artifact audit.
- [x] Complete iterative CodeRabbit review with no critical or warning issues.
- [x] Create `ChrisTitusTech/plazmic-ui`, push the reviewed commit to `main`,
  and verify hosted CI on the exact SHA.
- Acceptance criteria: AC-09 and AC-10.
- Manual validation: live `/loadskin plazmic-ui 1`, or record why it was
  skipped and the resulting residual risk.

## Completed

Local implementation, documentation, render, and validation are complete.
Live `/loadskin` was deliberately skipped to avoid changing the running game;
the remaining risk is that the mock canvas cannot prove in-game SIDL behavior.

B-01 added 1,669 reviewed bundle files plus a SHA-256 inventory and verified
release ZIP. The complete gate passed with 52 Python tests, 12 frontend tests,
258 XML files, repository/privacy checks, exact archive comparison, and
independent review. Live bundle loading was skipped to avoid changing game
state; in-game rendering remains the residual risk. Release upload additionally
rebuilds and verifies the exact reviewed bundle from its manifest.
All CodeRabbit findings from three completed review passes were addressed. A
final confirmation pass was rate-limited, so the exact reviewed diff received
the same local static, test, secret, whitespace, and clean-clone gates before
push. GitHub Actions then passed on the published implementation commit.

Studio 0.1.0 is published with Linux x86-64 and Windows x86-64 executables plus
verified SHA-256 checksums. Both artifacts passed version and embedded-frontend
diagnostics on native GitHub runners; the downloaded Linux release also served
the ignored local workspace successfully. Native Windows browser/game
interaction was not available for manual testing, and the first Windows binary
is not Authenticode-signed, as documented in the release notes.

Studio layout interaction improvements now apply one filter predicate to the
window list and canvas and provide selectable grid snapping with an Alt bypass.
Saving one section also preserves unsaved sibling geometry in the browser.
Synthetic browser validation passed at 1920x1080, the ignored practice capture
is `captures/plazmic-ui-studio-snapping.png`, and the packaged Linux diagnostic
contains the new frontend model. Live game validation was not required because
the feature does not write until the existing explicit save action is used.
The follow-up review found one minor snap-selector validation gap, which was
fixed and covered by the complete gate. A final confirmation review was
rate-limited; targeted browser regression, syntax, static, hygiene, and full
test gates passed on the exact staged diff.

Multi-window layout tools now support Shift-click selection from list or
canvas, stable-primary group movement, size matching, top/left alignment, equal
horizontal/vertical spacing, and atomic Save selected updates. The 1920x1080
synthetic browser workflow passed and is retained in ignored
`captures/plazmic-ui-studio-multi-select.png`; 27 Python tests, 10 frontend
model tests, the complete source gate, and the packaged Linux diagnostic pass.
CodeRabbit was rate-limited for this follow-up, so the exact staged diff
received focused geometry, API, rollback, workflow, secret, and whitespace
review locally instead.

Centered-window saves now share the half-canvas anchor conversion and preserve
six-decimal positions, including the BagInv8 regression fixture. The enabled
grid defaults to 16 pixels and multi-selection exposes Deselect all, which
clears the primary and grouped selections. The 1920x1080 browser check is
retained in ignored `captures/plazmic-ui-studio-stable-layout.png`; 31 Python
tests, 12 frontend model tests, the complete source gate, rebuilt Linux binary
diagnostics, and a zero-finding independent review pass.
