# Source and asset provenance

## Original project source

The shell, Python, HTML, CSS, JavaScript, tests, and documentation in this
repository are original Plazmic UI implementation. Initial development took
place on a local `plazmic-ui` worktree associated with the Plazmic Legends
project. The public UI toolkit was then detached into a new repository with a
fresh history and a narrower purpose.

No Plazmic Legends companion implementation, process reader, compatibility
offset, map, package payload, or release artifact was copied into this project.

## User-owned inputs

At runtime, users may direct the tools to files from their own EverQuest
Legends installation:

- `uifiles/default_modern`;
- an installed `uifiles/plazmic-ui`; and
- top-level `UI_*.ini` layouts.

Those inputs and every derived copy stay in private local paths. They are not
part of the project license, Git history, CI, package, review data, or public
release.

`ui-tools/upstream.sha256` contains only the reviewed SHA-256 identity of one
local input used to fail closed after game patches. A hash is not the source
asset.

## Synthetic tests

Tests create minimal XML, INI, sidecar, and texture-shaped byte fixtures in
temporary directories. They model the input grammar and failure behavior but
do not reproduce a shipped skin or personal layout.

## Third-party dependencies

Runtime source uses Python's standard library and system tools. The static
Studio has no third-party JavaScript or CSS dependency. Release CI uses pinned
PyInstaller 6.21.0 as a build-time dependency. Published executables contain
the Python runtime and PyInstaller bootloader components required to start the
original GPL-3.0-only Studio; they contain no game input. PyInstaller retains
its GPL-2.0-or-later licensing exception and other applicable notices. Removing
PyInstaller removes one-file releases but does not affect source execution.

Other contributor and CI tools are not redistributed by this repository and
retain their own licenses.

EverQuest and its assets are the property of their respective owners. Plazmic
UI is independent and is not affiliated with or endorsed by Daybreak Game
Company.
