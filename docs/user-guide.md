# User guide

## Install the UI bundle

Stop EverQuest before replacing a skin. Extract `plazmic-ui-bundle.zip` and
copy its complete `plazmic-ui/` directory into the game's `uifiles/` directory.
From a source checkout, copy `ui-bundle/plazmic-ui/` to the same destination.
Do not merge the files into `default` or `default_modern`.

Start EverQuest and load the skin:

```text
/loadskin plazmic-ui 1
```

The bundle contains no character `UI_*.ini`, so it does not change a
character's saved window layout. The Studio workflow below can capture and edit
one explicitly selected local layout when desired.

## Packaged Studio executables

Release downloads provide a Linux x86-64 binary and a Windows x86-64 `.exe`.
They need no separate Python installation and support the `capture`, `studio`,
and `publish` commands documented below.

Linux example:

```bash
chmod +x plazmic-ui-studio-linux-x86_64
./plazmic-ui-studio-linux-x86_64 capture \
  --game-dir '/path/to/EverQuest Legends'
./plazmic-ui-studio-linux-x86_64 studio
```

Windows PowerShell example:

```powershell
.\plazmic-ui-studio-windows-x86_64.exe capture `
  --game-dir 'C:\Path\To\EverQuest Legends'
.\plazmic-ui-studio-windows-x86_64.exe studio
```

Verify a download against the release's `SHA256SUMS` before running it. The
packaged Studio stores private data in these default roots:

- Linux: `${XDG_DATA_HOME:-~/.local/share}/plazmic-ui/.plazmic-ui-workspace`;
- Windows: `%LOCALAPPDATA%\plazmic-ui\.plazmic-ui-workspace`.

Set `PLAZMIC_UI_DATA_DIR` to use a different private application-data root.
The repository-only `sync`, format, lint, and offline install commands still
require the Linux source checkout and its system dependencies.

The first Windows release is not Authenticode-signed. Windows may show a
SmartScreen warning; verify the SHA-256 checksum before deciding to run it.

## Choose the local game directory

Every command that reads or writes the game accepts `--game-dir`. The
environment variable is more convenient for a terminal session:

```bash
export EQ_LEGENDS_DIR='/path/to/EverQuest Legends'
```

The directory must directly contain `eqgame.exe`, `uifiles/`, and the top-level
`UI_*.ini` files. Plazmic UI stores the selected path only in the private
workspace's `studio.json`.

Paths with spaces are supported. Quote an explicit path:

```bash
./plazmic-ui capture --game-dir '/path/with spaces/EverQuest Legends'
```

## Path A: Capture the current UI

Use this when `uifiles/plazmic-ui` is already installed or when you want to
start from the shipped modern UI:

```bash
./plazmic-ui capture
```

The command copies the installed `plazmic-ui` skin when present; otherwise it
copies `default_modern`. It excludes `.crc`, Wine `:crc`, `.bak`, and Plazmic
metadata sidecars. It then copies one selected top-level `UI_*.ini`.

When multiple layouts exist, choose interactively or pass a filename:

```bash
./plazmic-ui capture --layout UI_example.ini
```

Capture replaces the local skin workspace only after staging the new copy. An
existing skin is renamed to a timestamped `skin.backup-*` path.

## Path B: Build the reviewed derivative

Use this to create a fresh private skin workspace from `default_modern`:

```bash
./plazmic-ui sync
./plazmic-ui capture --layout-only --layout UI_example.ini
```

`sync` applies the repository's small, hash-reviewed transformations, formats
top-level XML, and runs structural lint. It stops when the upstream Advanced
Loot XML hash changes; this is intentional. Review a game patch before changing
`ui-tools/upstream.sha256`.

If a workspace already exists, preserve it while rebuilding:

```bash
./plazmic-ui sync --refresh
```

## Open the Studio

```bash
./plazmic-ui studio
```

The server chooses an ephemeral `127.0.0.1` port and opens a browser. It serves
only static project files and authenticated local API requests. Stop it with
Ctrl+C in the terminal.

The default mock canvas is 2560x1440. Set another size while capturing or when
starting the Studio:

```bash
./plazmic-ui capture --resolution 1920x1080
./plazmic-ui studio --resolution 1920x1080
```

Each dimension must be between 640 and 8192 pixels. Capture stores the choice
in ignored local configuration.

### Window tab

- Select a layout section from the left list.
- Type in **Filter windows** to hide nonmatching sections from both the list and
  mock canvas.
- Enable **Show hidden** to inspect sections whose `Show` value is `0`.
- Leave **Snap** enabled to align movement and resizing to the selected 4, 8,
  16, or 32 pixel grid. The default is 16 pixels.
- Drag a mock window to update its anchored percentage position. Hold Alt while
  dragging to bypass snapping temporarily.
- Drag the lower-right handle to update width and height; Alt also bypasses
  snapping while resizing.
- Shift-click windows on the canvas or in the list to build a group. The first
  window remains the primary reference and keeps the stronger outline.
- Drag any selected window to move the entire group without changing its
  internal spacing.
- Use **Match size** to copy the primary width and height, or **Align left** and
  **Align top** to copy the corresponding primary edge.
- With three or more selected windows, use **Space across** or **Space down**
  to distribute the windows with equal gaps across their current outer span.
- Use **Deselect all** to clear the group and primary selection. It appears
  only while multiple windows are selected.
- Edit anchors, percentage positions, size, alpha, fade alpha, background type,
  tint, visibility, lock, and fade values in the right inspector.
- Click **Save window settings** to replace only supported keys in that section.
- Click **Save selected** to persist the full group through one atomic layout
  replacement and one backup.

Saving one window keeps unsaved placements for the other windows visible on the
canvas. Those placements remain browser-only until each window is selected and
saved separately or included in **Save selected**.

Unknown sections, keys, comments, encoding, and CRLF/LF newline style are
preserved. Each save creates an ignored backup before atomic replacement.
Center-anchored positions retain their six-decimal percentage precision across
an unchanged save.

### Load and save the selected game layout

The top-right **Game layout** selector is shared by two explicit actions:

- **Load from game** discards unsaved browser positions and replaces the
  current Studio layout with the selected live `UI_*.ini`. It backs up the
  local Studio layout first and does not modify the game file.
- **Save to game** is the existing publish operation. After confirmation, it
  validates and backs up the skin and selected game layout before replacing
  them with the Studio workspace.

### XML tab

Choose a top-level skin XML file, edit its source, then click
**Validate and save XML**. The Studio requires US-ASCII, well-formed XML with
the EQ interface root. Nested paths and symlinks are not editable. The main
`EQUI.xml` skin manifest is deliberately excluded from the editor and is
validated again before capture or publish.

## Validate and publish

Run local checks before a game test:

```bash
./plazmic-ui lint
./plazmic-ui install --dry-run
```

For an offline install, exit EverQuest and run:

```bash
./plazmic-ui install
```

For intentional live iteration, use the Studio button or:

```bash
./plazmic-ui publish --target-ini UI_example.ini
```

Publish stages and validates the skin, backs up both the installed
`uifiles/plazmic-ui` directory and selected layout, and restores both targets
after a partial publish failure. The skin backup is a timestamped sibling of
`uifiles/plazmic-ui`; the layout backup is a timestamped sibling of the selected
top-level `UI_*.ini`. It does not stop or control the game.

Reload in game:

```text
/loadskin plazmic-ui 1
```

If the edited layout belongs to another character or a generic source layout,
use EverQuest's `/copylayout` interface to apply it, then reload the skin.

## Local files

| Path | Purpose | Public? |
| --- | --- | --- |
| `ui-bundle/plazmic-ui/` | Reviewed installable skin assets | Yes |
| `.plazmic-ui-workspace/skin/` | Materialized skin and copied assets | No |
| `.plazmic-ui-workspace/layouts/` | Selected personal layouts | No |
| `.plazmic-ui-workspace/backups/` | Local Studio edit backups | No |
| `.plazmic-ui-workspace/studio.json` | Local path, layout, and resolution | No |
| `captures/` | Screenshots and local evidence | No |

The private workspace and capture paths are ignored. Do not force-add or upload
them; only the reviewed `ui-bundle/plazmic-ui/` tree is public.
