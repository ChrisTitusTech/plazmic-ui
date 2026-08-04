# Plazmic UI

[![CI](https://github.com/ChrisTitusTech/plazmic-ui/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisTitusTech/plazmic-ui/actions/workflows/ci.yml)

Plazmic UI is a public EverQuest Legends UI toolkit. It creates a local skin
from files you already own, previews `UI_*.ini` window layouts in a browser
Studio, validates EQ XML, and publishes changes with rollback backups. The full
source workflow targets Linux; the Studio is also released as one-file Linux
and Windows executables.

The repository contains no EverQuest executable, texture, map, user layout, or
other Daybreak asset. All copied game files stay in ignored local workspaces.

## Features

- Captures an installed `plazmic-ui` skin, or falls back to `default_modern`,
  plus one explicitly selected top-level layout.
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
- Publishes only `uifiles/plazmic-ui` and one selected existing `UI_*.ini`.
- Runs locally with no telemetry, account, updater, or non-loopback listener.

The Studio is a layout mock. It does not reimplement EQ's SIDL renderer or
display proprietary textures, so the final visual check still happens in game.

## Download the Studio

The [latest GitHub release](https://github.com/ChrisTitusTech/plazmic-ui/releases/latest)
contains:

- `plazmic-ui-studio-linux-x86_64`;
- `plazmic-ui-studio-windows-x86_64.exe`; and
- `SHA256SUMS` for both files.

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

The binaries support `capture`, `studio`, and `publish`. They contain the
Studio and its Python runtime, not any EverQuest assets. The Linux-only `sync`,
format, lint, and offline install commands remain in the source workflow.

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

## Safety and asset boundary

Generated UI content stays under ignored `.plazmic-ui-workspace/`:

- `skin/`: copied local skin and assets;
- `layouts/`: selected personal layouts;
- `backups/`: local edit backups;
- `studio.json`: local game path and Studio selection.

Local screenshots and validation evidence stay in the separate ignored
`captures/` directory.

Do not force-add, publish, package, or attach these files to an issue or
release. The tool never changes `default` or `default_modern` in place.

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
EverQuest or Daybreak assets, which are not included.
