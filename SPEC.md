# Plazmic UI specification

## Problem

EverQuest Legends stores window placement in top-level `UI_*.ini` files and
loads skins from `uifiles/`, but iterating on those files inside the game is
slow and error-prone. A useful public distribution needs both a ready-to-install
skin and tooling that keeps personal layouts and installation data private.

Plazmic UI provides a reviewed UI asset bundle plus a reproducible toolkit. It
offers a browser-based layout Studio, validated XML editing, and narrow
install/publish operations with rollback backups while keeping user files local.

## Users

- EverQuest Legends players running the game through Wine on Linux or natively
  on Windows.
- UI authors who want to derive a skin from their own installed files.
- Contributors who need deterministic tests without a game installation.

Users may have paths containing spaces, multiple `UI_*.ini` layouts, an active
game process, or a patched skin whose XML differs from the reviewed baseline.

## Required behavior

### Workspace creation and capture

- Accept the game directory through `--game-dir`, `EQ_LEGENDS_DIR`, or the
  ignored Studio configuration.
- `sync` copies the installed `uifiles/default_modern` into the ignored private
  skin workspace, excludes checksum/backup sidecars, applies only hash-reviewed
  transformations, formats XML, and validates the result.
- `capture` copies one explicitly selected current top-level `UI_*.ini` into
  the ignored layout workspace and captures the installed `plazmic-ui` skin,
  falling back to `default_modern` only when no installed Plazmic skin exists.
- Existing local workspaces are preserved as timestamped backups before a
  refresh or replacement.

### UI Studio

- Serve only on `127.0.0.1` using an ephemeral port by default.
- Require an unguessable per-process token for every API request.
- Preview editable INI sections on a configurable screen canvas, defaulting to
  2560x1440, using Legends left/center/right and top/center/bottom anchors.
- List visible windows, optionally include hidden windows, and apply the window
  name filter to both the list and mock canvas.
- Select, drag, resize, and edit supported position, size, visibility, alpha,
  fade, lock, background type, and tint fields.
- Snap drag and resize operations to a selectable 4, 8, 16, or 32 pixel grid,
  defaulting to 16 pixels, with a visible toggle and temporary Alt-key bypass.
- Select multiple windows with Shift-click from the canvas or list, retain one
  primary selection for the inspector, and move the selected group without
  changing its internal spacing.
- Show an explicit **Deselect all** action while multiple windows are selected
  and clear both the group and primary selection when it is used.
- Make selected windows consistent through explicit match-size, edge-alignment,
  and equal horizontal or vertical distribution actions.
- Save every selected window in one atomic INI replacement and one backup while
  preserving unrelated sections and unsaved nonselected browser state.
- Preserve unrelated INI sections, keys, comments, byte encoding, and newline
  style when saving one section.
- Preserve the six-decimal anchor position and the center-anchor half-canvas
  extent across an unchanged save.
- Preserve unsaved in-browser positions and sizes for every other window when
  saving and reloading one selected section.
- Open only top-level non-symlink window XML files from the local skin
  workspace; reserve `EQUI.xml` as a non-editable skin manifest.
- Save only US-ASCII, well-formed EQ interface XML after validation.
- Require `EQUI.xml` to contain exactly one top-level `Composite` manifest with
  at least one `Include` before capture, lint, install, or publish succeeds.
- Back up every replaced local INI or XML file and use atomic replacement.
- Pair the top-right game-layout selector with explicit **Load from game** and
  **Save to game** actions. Loading replaces only the current workspace layout
  after a backup and stable descriptor read; it rejects symlinks, path escapes,
  oversized or empty files, and sources that change while being read. Saving
  retains the transactional publish behavior below.
- Run from source or from one-file x86-64 Linux and Windows release binaries.
- Store packaged-app workspaces in the user's local application-data directory,
  with an explicit environment override for portable or test use.

### Install and publish

- The Linux source-only `install` command validates the materialized skin and
  writes only the sibling `uifiles/plazmic-ui` directory. It refuses while
  `eqgame.exe` is running.
- `publish` is the explicit live-test path. It validates and stages the skin,
  asks which existing top-level `UI_*.ini` to replace, backs up both targets,
  and writes no other game file.
- A failed publish must restore any target already moved during that publish.
- Neither operation may follow workspace symlinks or write to `default`,
  `default_modern`, the client executable, libraries, registry, or gameplay
  state.
- Success output provides the exact `/loadskin plazmic-ui 1` follow-up.

### Distributable UI bundle

- Track the ready-to-install skin only under `ui-bundle/plazmic-ui/` and package
  it as a separate `plazmic-ui-bundle.zip` release asset.
- The archive root is `plazmic-ui/`, ready to place under the game's `uifiles/`
  directory while the game is stopped.
- Include the reviewed XML, texture, cursor, and generic skin INI files required
  by the skin. Keep the Studio executables separate from the asset archive.
- Exclude every character `UI_*.ini`, backup, checksum sidecar, executable,
  symlink, local provenance timestamp, account value, character name, personal
  path, and credential.
- Treat bundled game assets as third-party content outside the GPL grant and
  retain the ownership and non-endorsement notice.
- Publish the bundle only after obtaining express written redistribution
  authorization from Daybreak Game Company covering the exact files and
  distribution channel. The EULA, ownership notice, and non-endorsement notice
  do not grant that permission.

### Validation and errors

- Reject missing dependencies, invalid game roots, absent `EQUI.xml`, unknown
  options, path escapes, symlinks, malformed XML, invalid settings, ambiguous
  non-interactive layout selection, and unreviewed source hashes with useful
  nonzero errors.
- Lint missing includes, malformed XML, duplicate screen properties, stale CRC
  sidecars, formatting drift, and incomplete skin roots.
- Never silently guess a layout target or overwrite `default_modern`.

## User experience

The primary path is:

1. Download a Studio executable or clone the repository and point it at the
   local Legends installation.
2. Capture an installed skin/layout or sync a fresh local derivative.
3. Open the Studio, edit, and save into ignored workspaces.
4. Publish explicitly, then reload the skin in game.
5. Restore timestamped backups or load `default_modern` if needed.

The Studio must remain usable at a 1080p browser viewport, expose labels for
form controls, provide keyboard-focus indicators, and communicate success and
errors in text rather than color alone. Its canvas is a bounds and alpha mock,
not a full renderer for EQ SIDL or proprietary textures.

## Architecture and data flow

```text
user-owned game files --> ignored local workspace --> loopback UI Studio
          |                        |                         |
          |                        +---- validated saves ----+
          |
          +<-- explicit staged publish plus timestamped backups
```

POSIX shell scripts handle materialization and offline installation. A Python
standard-library server owns path validation, INI/XML transformations, local
API authorization, backups, and staged publish. Static HTML/CSS/JavaScript
renders the editor; it has no build step and no external network dependency.

## Security and privacy

- No telemetry, analytics, updater, remote listener, account, or cloud service.
- Reviewed game UI assets are tracked only in `ui-bundle/plazmic-ui/` and
  packaged only in the separate UI bundle. No executable, character layout,
  personal path, account data, character identifier, user backup, or credential
  is included.
- The loopback API uses a random token and no-store responses. State-changing
  requests require the token and an allowed loopback Origin when present.
- Filenames are restricted to top-level expected forms; resolved targets must
  remain beneath their approved roots.
- Private workspace/config files default to owner-only permissions where the
  tool creates them.
- Publish is a local file operation only. It never injects code, automates
  gameplay, bypasses protections, or edits gameplay state.

## Performance and compatibility

- Source workflow: Linux with Python 3.11+, a POSIX shell, GNU coreutils, and
  `rsync`.
- Packaged Studio: x86-64 Linux or Windows and no separate Python installation.
- Current Chromium- and Firefox-family browsers.
- Default canvas 2560x1440; supported custom dimensions are 640-8192 pixels per
  axis.
- Parse and render typical layouts interactively; hard-limit API requests to
  10 MiB and reject XML above that bound.
- No recursive filesystem scan outside the selected skin tree and no network
  access beyond the loopback Studio server.

## Non-goals

- Reimplementing the full SIDL renderer or showing proprietary textures.
- Supporting macOS or non-x86-64 packaged hosts in the initial release.
- Editing game binaries, DLLs, registry state, memory, or gameplay state.
- Injecting code, macros, scripting, input automation, or multibox control.
- Automatically selecting a character layout when more than one exists.
- Modifying `default` or `default_modern` in place.

## Acceptance criteria

- AC-01: A clean clone contains original source, synthetic fixtures,
  documentation, CI metadata, and the reviewed UI bundle; privacy and asset
  boundary audits are clean.
- AC-02: Capture, sync, format, lint, install dry-run, and CLI failure paths are
  covered by deterministic tests or safe local validation.
- AC-03: The Studio renders the captured layout, supports the documented
  controls, and saves one INI section without changing unrelated content.
- AC-04: XML reads and saves stay within top-level regular files and reject
  symlinks, non-ASCII input, malformed XML, and invalid roots.
- AC-05: Install and publish validate source trees, exclude sidecars, create
  backups, and roll back partial failures without touching shipped skins.
- AC-06: The server binds only to loopback, authenticates API calls, rejects
  oversized bodies, and permits no arbitrary file reads or writes.
- AC-07: `make check` passes ShellCheck, shfmt, Ruff, Python compilation, unit
  tests, Markdownlint, and repository hygiene checks.
- AC-08: User, contributor, architecture, security, rollback, and live reload
  documentation is complete and contains no machine-specific path.
- AC-09: A 1920x1080 practice render demonstrates the current Studio against
  ignored local data, and the live `/loadskin` result is reported separately.
- AC-10: Independent review has no unresolved critical or warning findings,
  the exact reviewed commit is pushed to public `main`, and remote CI passes.
- AC-11: Releases provide verified Linux ELF and Windows PE x86-64 Studio
  executables with matching version output and embedded frontend files. Studio
  executables contain no game or personal assets.
- AC-12: Layout filtering hides nonmatching windows from both Studio views,
  and enabled move/resize snapping follows the selected grid while disabled or
  Alt-bypassed dragging remains unsnapped. Saving one section does not reset
  unsaved canvas changes for other windows.
- AC-13: Shift-click multi-selection works from canvas and list, group dragging
  preserves relative offsets, group layout actions produce deterministic
  geometry, and one batch save persists all selected sections atomically.
- AC-14: The selected game layout can be loaded into the Studio workspace with
  a local backup and no game write after rejecting symlinks, path escapes,
  oversized or empty files, and unstable reads, while the paired save action
  remains an explicit confirmed publish.
- AC-15: The tracked `ui-bundle/plazmic-ui/` tree and release ZIP contain a
  complete lint-clean skin and no character layout, user identifier, sidecar,
  executable, symlink, local path, credential, or GPL relicensing claim.

## Resolved decisions

- Repository: `ChrisTitusTech/plazmic-ui`, separate from Plazmic Legends.
- Visibility: public.
- License: GPL-3.0-only, matching the source project's public licensing
  boundary while preserving independent ownership of this implementation.
- Distribution: source, Studio-only Linux and Windows executables, and a
  separate ready-to-install `plazmic-ui-bundle.zip` containing reviewed game UI
  assets. The GPL applies only to original project code and documentation.
- Studio dependencies: Python standard library plus static browser files.
- Default canvas: 2560x1440 with an explicit configurable resolution.
