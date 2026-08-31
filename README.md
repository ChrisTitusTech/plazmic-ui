# Plazmic UI

[![CI](https://github.com/ChrisTitusTech/plazmic-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisTitusTech/plazmic-ui/actions/workflows/ci.yml)

Plazmic UI is a public EverQuest Legends UI bundle and editing toolkit. It
includes ready-to-install Plazmic UI and Aya Legends skins, previews `UI_*.ini` window layouts in a
browser Studio, validates EQ XML, and publishes changes with rollback backups.
The full source workflow targets Linux; the Studio is also released as one-file
Linux and Windows executables.

The reviewed `ui-bundle/plazmic-ui/` and `ui-bundle/aya-legends/` trees contain
the game UI assets required by each skin. Aya includes its upstream generic
layout template; neither bundle contains account data, a personal character
layout, character name, local path, game executable, backup, or checksum sidecar.

## Features

- Captures either an installed `plazmic-ui` skin (falling back to
  `default_modern`) or an installed `AYA_Legends` skin, plus one explicitly
  selected top-level layout.
- Provides complete Plazmic UI and Aya Legends packages for direct installation.
- Builds a reviewed local derivative from `default_modern` without changing the
  shipped skin.
- Shows window bounds and alpha on a configurable canvas, defaulting to
  2560x1440.
- Supports selection, drag, resize, configurable grid snapping, anchors,
  percentage positions, visibility, alpha, fade, lock, background type, and
  tint.
- Filters the layout list and mock canvas together so unrelated windows stay
  out of the way while editing.
- Supports Shift-click groups, shared movement, matching sizes, edge alignment,
  equal spacing, and one atomic save for every selected window.
- Opens and validates top-level EQ interface XML without a web dependency or
  external service.
- Preserves unrelated INI content and creates timestamped backups before every
  replacement.
- Publishes only the selected allowlisted skin directory and one selected
  existing `UI_*.ini`.
- Runs locally with no telemetry, account, updater, or non-loopback listener.

The Studio is a layout mock. It does not reimplement EQ's SIDL renderer or
display proprietary textures, so the final visual check still happens in game.

## Download the Studio

Tagged releases provide:

- `plazmic-ui-studio-linux-x86_64`;
- `plazmic-ui-studio-windows-x86_64.exe`; and
- `plazmic-ui-bundle.zip`;
- `aya-legends-bundle.zip`; and
- `SHA256SUMS` for every release asset.

The current packages are also available in
[`ui-bundle/plazmic-ui`](ui-bundle/plazmic-ui) and
[`ui-bundle/aya-legends`](ui-bundle/aya-legends). To install Plazmic UI, stop
EverQuest, copy the entire `plazmic-ui/` directory into the game's `uifiles/`
directory, then start the game and run:

```text
/loadskin plazmic-ui 1
```

The ZIP has the same `plazmic-ui/` root. Do not merge it into `default` or
`default_modern`.

For Aya, extract `aya-legends-bundle.zip` into the EverQuest Legends directory.
It preserves the upstream `uifiles/AYA_Legends/` directory and generic
`UI_Character_Server_LO1.ini` template. Load it with `/loadskin AYA_Legends 1`.

On Linux:

```bash
chmod +x plazmic-ui-studio-linux-x86_64
./plazmic-ui-studio-linux-x86_64 capture \
  --game-dir '/path/to/EverQuest Legends'
./plazmic-ui-studio-linux-x86_64 studio
```

On Windows PowerShell:

```powershell
.\plazmic-ui-studio-windows-x86_64.exe capture `
  --game-dir 'C:\Path\To\EverQuest Legends'
.\plazmic-ui-studio-windows-x86_64.exe studio
```

The binaries support `capture`, `studio`, and `publish`. The separate Studio
executables contain the Studio and its Python runtime, not EverQuest assets.
The Linux-only `sync`, format, lint, and offline install commands remain in the
source workflow.

## Source requirements

- Linux
- Python 3.11 or newer
- POSIX shell and GNU coreutils
- `rsync`
- A current browser
- A user-owned EverQuest Legends installation under Wine

Contributor checks additionally use Ruff, ShellCheck, shfmt, and
Markdownlint CLI2.

## Source quick start

```bash
git clone https://github.com/ChrisTitusTech/plazmic-ui.git
cd plazmic-ui
export EQ_LEGENDS_DIR='/path/to/EverQuest Legends'
./plazmic-ui capture --resolution 2560x1440
./plazmic-ui studio
```

When several `UI_*.ini` files exist, `capture` asks which one to use. Scripts
and automation should pass only its top-level filename:

```bash
./plazmic-ui capture --layout UI_example.ini
```

Choose Aya instead and remember that choice for Studio, install, and publish:

```bash
./plazmic-ui capture --skin aya --layout UI_example.ini
```

Save edits in the Studio, then select the destination layout and click
**Publish to game**, or publish from the terminal:

```bash
./plazmic-ui publish --target-ini UI_example.ini
```

Reload inside EverQuest:

```text
/loadskin plazmic-ui 1
```

For a fresh reviewed derivative instead of capturing an installed skin:

```bash
./plazmic-ui sync
./plazmic-ui capture --layout-only --layout UI_example.ini
./plazmic-ui studio
```

See the [user guide](docs/user-guide.md) for offline installation, live reload,
backup restoration, resolution settings, and both workspace paths.

## Privacy and asset boundary

The distributable skins are tracked only under `ui-bundle/plazmic-ui/` and
`ui-bundle/aya-legends/`. Bundle validation permits required XML, textures,
cursors, generic skin INIs, and Aya's exact reviewed generic layout while
rejecting every other `UI_*.ini` layout, backups, checksum sidecars, symlinks,
executables, local paths, credentials, and private workspace metadata. Separate
SHA-256 manifests pin each reviewed inventory and its exact asset bytes.

Generated UI content stays under ignored `.plazmic-ui-workspace/`:

- `skin/`: copied local skin and assets;
- `layouts/`: selected personal layouts;
- `backups/`: local edit backups;
- `studio.json`: local game path and Studio selection.

Local screenshots and validation evidence stay in the separate ignored
`captures/` directory.

Do not force-add, publish, package, or attach private workspace files to an
issue or release. Only reviewed asset changes under the two approved bundle
roots belong in a public bundle. The tool never changes `default` or
`default_modern` in place.

Packaged binaries store the same private workspace under the user's local
application-data directory. Set `PLAZMIC_UI_DATA_DIR` before running a binary
to select another private storage root.

Plazmic UI is independent and is not affiliated with or endorsed by Daybreak
Game Company. EverQuest and its assets belong to their respective owners.

## Documentation

- [User guide](docs/user-guide.md)
- [Troubleshooting and rollback](docs/troubleshooting.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Source and asset provenance](docs/provenance.md)
- [Development and validation](docs/development.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

Original Plazmic UI source is licensed under the
[GNU General Public License v3.0 only](LICENSE). The license does not apply to
the bundled EverQuest or Daybreak assets, which remain the property of their
respective owners. See [third-party notices](THIRD_PARTY_NOTICES.md).
