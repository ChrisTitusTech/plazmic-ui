# Plazmic UI tasks

Task status changes only after acceptance criteria and validation pass. Record
skipped live checks and residual risk rather than marking them complete.

## Current phase

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
