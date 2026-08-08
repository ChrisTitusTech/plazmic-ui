# Architecture and trust boundaries

## Components

`plazmic-ui` is a small POSIX shell entrypoint. It dispatches to focused tools:

- `sync-ui.sh` stages a derivative from the installed `default_modern` skin;
- `format-ui.sh` and `format_xml.py` normalize text without reserializing EQ's
  mixed-content XML dialect;
- `lint-ui.py` performs structural and formatting validation;
- `install-ui.sh` performs the offline staged skin install;
- `ui_studio.py` owns capture, INI/XML operations, the loopback server, and
  transactional live publish; and
- `studio/` is static HTML, CSS, and JavaScript with no build system or remote
  dependency.

Release executables package `ui_studio.py`, `studio/`, a Python runtime, and
PyInstaller runtime components into one file per target operating system. They
do not package the POSIX shell tools or any materialized workspace. Frozen
executables resolve the frontend from their temporary bundle and keep mutable
private data under the user's local application-data directory.

## Data flow

```text
EverQuest Legends installation
  |-- uifiles/default_modern ---- sync/capture ----+
  |-- uifiles/plazmic-ui -------- capture ----------+--> .plazmic-ui-workspace/skin
  |-- UI_*.ini ------------------ capture --------------> .plazmic-ui-workspace/layouts
  |                                                       |
  |                                             loopback Studio edits
  |                                                       |
  +<----------- explicit staged publish and backups ------+
```

No copied game file enters Git, CI, a package, an external review service, or
an external network request. The browser Studio exchanges copied content only
with its loopback server on `127.0.0.1`; that local traffic never leaves the
host.

The top-right game-layout selector also supports a reverse layout-only flow.
**Load from game** reads one selected top-level `UI_*.ini`, verifies that it
remained stable during the read, backs up the current workspace layout, and
replaces only that ignored local file. It never writes to the game.

Release CI builds on Linux and Windows separately, runs the synthetic test
suite, verifies the executable format and version, and asks the executable to
validate its embedded frontend before it can become a release asset.

## INI model

The parser reads Latin-1 bytes into a section/key model for presentation. A
save does not serialize that model. Instead, it scans the original lines and
replaces only approved keys in the selected section, appending missing approved
keys before the next section. This preserves unrelated data and newline style.

Positions use the Legends percentage anchor model:

- left/top: percentage offset from the leading edge;
- right/bottom: percentage offset from the trailing edge; and
- center: percentage offset from the canvas center after accounting for size.

Center anchors use half of the canvas extent for their percentage scale in
both directions. The Python loader and shared frontend model use the same
conversion and retain six decimal places so selecting and saving an unchanged
window does not move it.

Window size comes from the layout when present, then from a matching top-level
`EQUI_*.xml` screen, and finally from a conservative mock default.

The frontend keeps filtering and drag geometry in a small dependency-free
model shared by the layout list and canvas. Moving snaps the mock window's
top-left corner to the selected grid. Resizing keeps the top-left corner fixed
and snaps the lower-right edge. The browser converts the resulting pixels back
to the existing anchored percentage model; no INI write occurs until the user
selects the save action.

After a section save, the Studio reloads that section from disk but merges it
with the current in-browser state for every sibling window. This keeps unsaved
sibling placements from jumping back while retaining the saved section as the
server-authoritative result.

Multi-selection keeps a stable primary window for inspector values and group
layout references. Group drag snaps the primary once and applies the same pixel
delta to every selected window, preserving relative offsets. Match, align, and
distribution operations run in the same frontend model as single-window
geometry, then convert each result back to its own anchor percentages.
The group toolbar is visible only for multiple selections; **Deselect all**
clears both the group and primary selection without changing layout data.

The batch layout endpoint accepts a bounded list of unique section updates,
validates every setting before writing, verifies every named section appears
exactly once, and performs one atomic replacement with one backup. A validation
failure leaves the source layout untouched.

## XML model

The formatter changes line endings, indentation, and trailing whitespace only.
It does not reserialize elements. Studio saves require US-ASCII, well-formed
XML, root element `XML`, and root ID `EQInterfaceDefinitionLanguage`.

XML filenames must be top-level regular `.xml` files whose resolved parent is
the materialized skin root. Symlinks and files above 10 MiB are rejected.
`EQUI.xml` is excluded from the Studio editor because it is the skin manifest,
not a window definition. Capture, lint, install, and publish require it to have
one top-level `Composite` containing `Include` entries before any skin copy.

## Server boundary

The standard-library HTTP server binds to IPv4 loopback only. Each process
generates a 192-bit URL-safe token embedded in the served page. API requests
must supply that token, the exact loopback Host, and either no Origin or the
exact same loopback Origin. Request bodies are limited to 10 MiB.

The token protects the narrow local API from cross-site requests; it is not an
authentication system for remote or multi-user deployment. The server must not
be exposed beyond loopback.

## Write and rollback boundary

Workspace writes use a same-directory temporary file, `fsync`, owner-preserving
mode, and atomic `os.replace`. Existing files are copied into ignored backup
directories first.

Publish validates all source paths before writing, stages a complete skin copy,
moves an existing installed skin to a timestamped sibling backup, and atomically
replaces one selected existing layout. If the layout replacement fails, the
installed skin and layout are restored.

The shipped `default` and `default_modern` directories are read-only inputs.
