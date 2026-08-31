#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
import threading
import webbrowser
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

DEFAULT_SCREEN_WIDTH = 2560
DEFAULT_SCREEN_HEIGHT = 1440
VERSION = "0.1.0"
APPLICATION_NAME = "Plazmic UI Studio"
MIN_SCREEN_EXTENT = 640
MAX_SCREEN_EXTENT = 8192
MAX_REQUEST_BYTES = 10 * 1024 * 1024
WORKSPACE_DIRECTORY = ".plazmic-ui-workspace"
LAYOUT_NAME_PATTERN = re.compile(r"^UI_[^/\\]+\.ini$", re.IGNORECASE)
RESOLUTION_PATTERN = re.compile(r"^([0-9]{3,4})x([0-9]{3,4})$", re.IGNORECASE)
SECTION_PATTERN = re.compile(r"^\[([^\]]+)\][ \t]*$")
KEY_PATTERN = re.compile(r"^([A-Za-z0-9_.]+)=(.*)$")
VARIANT_PATTERN = re.compile(r"^(.*)_([0-9]+)$")
EDITABLE_KEYS = {
    "XRef",
    "YRef",
    "XPos",
    "YPos",
    "Width",
    "Height",
    "Alpha",
    "FadeToAlpha",
    "Fades",
    "Locked",
    "Show",
    "BGType",
    "BGTint.red",
    "BGTint.green",
    "BGTint.blue",
}
STATIC_CONTENT_TYPES = {
    "index.html": "text/html; charset=utf-8",
    "studio-model.js": "text/javascript; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
}
REQUIRED_FRONTEND_MARKERS = {
    "index.html": (
        b'<option value="16" selected>',
        b'id="deselect-all"',
        b'id="load-button"',
    ),
    "studio-model.js": (
        b"const DEFAULT_GRID_SIZE = 16;",
        b"anchoredPosition",
        b"positionPercent",
    ),
    "app.js": (
        b"deselectAllWindows",
        b"studioModel.anchoredPosition",
        b'api("/api/load"',
    ),
}


def frozen_application() -> bool:
    return bool(getattr(sys, "frozen", False))


def application_data_root(script_dir: Path) -> Path:
    if not frozen_application():
        return script_dir.parent

    override = os.environ.get("PLAZMIC_UI_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "plazmic-ui"


def static_directory(script_dir: Path) -> Path:
    if frozen_application():
        bundle_root = Path(getattr(sys, "_MEIPASS", script_dir))
        return bundle_root / "studio"
    return script_dir / "studio"


def validate_frontend_bundle(static_dir: Path) -> None:
    if not all((static_dir / name).is_file() for name in STATIC_CONTENT_TYPES):
        raise ValueError("Studio frontend files are missing from this installation")
    for name, markers in REQUIRED_FRONTEND_MARKERS.items():
        contents = (static_dir / name).read_bytes()
        if not all(marker in contents for marker in markers):
            raise ValueError(f"Studio frontend is incomplete: {name}")


@dataclass(frozen=True)
class StudioPaths:
    repo: Path
    skin: Path
    layouts: Path
    backups: Path
    config: Path
    game: Path
    layout: Path
    screen_width: int = DEFAULT_SCREEN_WIDTH
    screen_height: int = DEFAULT_SCREEN_HEIGHT


def timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")


def local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def parse_resolution(value: str | None) -> tuple[int, int]:
    if value is None:
        return DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT
    match = RESOLUTION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("resolution must use WIDTHxHEIGHT, for example 2560x1440")
    width, height = (int(part) for part in match.groups())
    if not all(MIN_SCREEN_EXTENT <= item <= MAX_SCREEN_EXTENT for item in (width, height)):
        raise ValueError(
            f"resolution dimensions must be between {MIN_SCREEN_EXTENT} and "
            f"{MAX_SCREEN_EXTENT} pixels"
        )
    return width, height


def ignored_game_sidecar(_directory: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name.endswith(".crc")
        or name.endswith(":crc")
        or name.endswith(".bak")
        or name == ".plazmic-upstream"
    }


def is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def first_symlink(root: Path) -> Path | None:
    if is_link_like(root):
        return root
    return next((path for path in root.rglob("*") if is_link_like(path)), None)


def constant_time_header(value: str, expected: str) -> bool:
    try:
        return secrets.compare_digest(value.encode("latin-1"), expected.encode("ascii"))
    except UnicodeEncodeError:
        return False


def local_workspace(repo: Path, *, create: bool) -> Path:
    workspace = repo / WORKSPACE_DIRECTORY
    if is_link_like(workspace):
        raise ValueError(f"private workspace must not be a symlink: {workspace}")
    if create:
        workspace.mkdir(mode=0o700, parents=True, exist_ok=True)
        workspace.chmod(0o700)
    elif not workspace.is_dir():
        raise ValueError("capture or sync a local workspace first")
    return workspace


def atomic_write(path: Path, contents: bytes, backup_root: Path) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if path.exists():
        backup_dir = backup_root / path.name
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{timestamp()}.bak"
        shutil.copy2(path, backup)

    file_mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(file_mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return backup


def parse_ini(contents: bytes) -> dict[str, dict[str, str]]:
    text = contents.decode("latin-1")
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for raw_line in text.splitlines():
        section_match = SECTION_PATTERN.match(raw_line)
        if section_match:
            current = sections.setdefault(section_match.group(1), {})
            continue
        key_match = KEY_PATTERN.match(raw_line)
        if current is not None and key_match:
            current[key_match.group(1)] = key_match.group(2)
    return sections


def update_ini_sections(
    path: Path,
    section_updates: dict[str, dict[str, str]],
    backup_root: Path,
) -> Path | None:
    if not section_updates:
        raise ValueError("at least one layout section is required")
    source = path.read_bytes()
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    text = source.decode("latin-1")
    lines = text.splitlines(keepends=True)
    section_counts = dict.fromkeys(section_updates, 0)
    for line in lines:
        match = SECTION_PATTERN.match(line.rstrip("\r\n"))
        if match and match.group(1) in section_counts:
            section_counts[match.group(1)] += 1
    for section, count in section_counts.items():
        if count != 1:
            raise ValueError(f"layout section must appear exactly once: {section} (found {count})")
    output: list[bytes] = []
    current: str | None = None
    seen: set[str] = set()

    def finish_current() -> None:
        if current not in section_updates:
            return
        for key, value in section_updates[current].items():
            if key not in seen:
                if output and not output[-1].endswith((b"\n", b"\r")):
                    output[-1] += newline
                output.append(f"{key}={value}".encode("latin-1") + newline)

    for line in lines:
        plain = line.rstrip("\r\n")
        section_match = SECTION_PATTERN.match(plain)
        if section_match:
            finish_current()
            current = section_match.group(1)
            seen = set()
            output.append(line.encode("latin-1"))
            continue
        key_match = KEY_PATTERN.match(plain)
        if current in section_updates and key_match:
            key = key_match.group(1)
            seen.add(key)
            if key in section_updates[current]:
                output.append(f"{key}={section_updates[current][key]}".encode("latin-1") + newline)
                continue
        output.append(line.encode("latin-1"))

    finish_current()
    return atomic_write(path, b"".join(output), backup_root)


def update_ini_section(
    path: Path,
    section: str,
    updates: dict[str, str],
    backup_root: Path,
) -> Path | None:
    return update_ini_sections(path, {section: updates}, backup_root)


def percent_value(value: str, default: float = 0.0) -> float:
    try:
        return float(value.rstrip("%"))
    except (AttributeError, ValueError):
        return default


def anchored_position(reference: str, percent: float, size: int, extent: int) -> float:
    offset_extent = extent / 2.0 if reference == "center" else extent
    offset = offset_extent * percent / 100.0
    if reference in {"right", "bottom"}:
        return extent - offset - size
    if reference == "center":
        return extent / 2.0 + offset - size / 2.0
    return offset


def position_percent(reference: str, position: float, size: int, extent: int) -> float:
    if reference in {"right", "bottom"}:
        return (extent - position - size) * 100.0 / extent
    if reference == "center":
        return (position + size / 2.0 - extent / 2.0) * 100.0 / (extent / 2.0)
    return position * 100.0 / extent


def screen_identity(section: str) -> tuple[str, list[str]]:
    if section == "MainChat" or section.startswith("Chat "):
        return "ChatWindow", ["EQUI_ChatWindow.xml"]
    variant_match = VARIANT_PATTERN.match(section)
    if variant_match:
        base, variant = variant_match.groups()
        return base, [f"EQUI_{base}{variant}.xml", f"EQUI_{base}.xml"]
    return section, [f"EQUI_{section}.xml"]


def xml_window_size(path: Path, item: str) -> tuple[int, int] | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    for element in root.iter():
        if element.get("item") != item:
            continue
        size = next((child for child in element if local_name(child.tag) == "Size"), None)
        if size is None:
            continue
        values = {local_name(child.tag): (child.text or "").strip() for child in size}
        try:
            return int(values["CX"]), int(values["CY"])
        except (KeyError, ValueError):
            return None
    return None


def xml_for_section(skin: Path, section: str) -> tuple[str | None, int, int]:
    item, candidates = screen_identity(section)
    for filename in candidates:
        path = skin / filename
        if not path.is_file() or is_link_like(path):
            continue
        size = xml_window_size(path, item)
        if size is not None:
            return filename, size[0], size[1]
        return filename, 240, 120
    return None, 240, 120


def layout_state(paths: StudioPaths) -> dict[str, Any]:
    sections = parse_ini(paths.layout.read_bytes())
    windows: list[dict[str, Any]] = []
    for name, values in sections.items():
        if name in {"Main", "Default"}:
            continue
        if not EDITABLE_KEYS.intersection(values):
            continue
        xml_file, xml_width, xml_height = xml_for_section(paths.skin, name)
        width = _integer(values.get("Width"), xml_width, 1, 8192)
        height = _integer(values.get("Height"), xml_height, 1, 8192)
        x_ref = values.get("XRef", "left").lower()
        y_ref = values.get("YRef", "top").lower()
        if x_ref not in {"left", "center", "right"}:
            x_ref = "left"
        if y_ref not in {"top", "center", "bottom"}:
            y_ref = "top"
        x_percent = percent_value(values.get("XPos", "0"))
        y_percent = percent_value(values.get("YPos", "0"))
        windows.append(
            {
                "section": name,
                "values": {key: values.get(key, "") for key in sorted(EDITABLE_KEYS)},
                "x": anchored_position(x_ref, x_percent, width, paths.screen_width),
                "y": anchored_position(y_ref, y_percent, height, paths.screen_height),
                "width": width,
                "height": height,
                "visible": values.get("Show", "1") != "0",
                "xmlFile": xml_file,
            }
        )
    targets = [path.name for path in game_layouts(paths.game)]
    xml_files = [
        path.name
        for path in sorted(paths.skin.glob("*.xml"))
        if path.name.casefold() != "equi.xml" and path.is_file() and not is_link_like(path)
    ]
    return {
        "screen": {"width": paths.screen_width, "height": paths.screen_height},
        "layout": paths.layout.name,
        "skin": paths.skin.name,
        "windows": windows,
        "xmlFiles": xml_files,
        "targets": targets,
    }


def _integer(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return default
    return min(maximum, max(minimum, parsed))


def validated_settings(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("settings must be an object")
    result: dict[str, str] = {}
    for key, value in raw.items():
        if key not in EDITABLE_KEYS:
            raise ValueError(f"setting is not editable: {key}")
        text = str(value).strip()
        if key == "XRef" and text not in {"left", "center", "right"}:
            raise ValueError("XRef must be left, center, or right")
        if key == "YRef" and text not in {"top", "center", "bottom"}:
            raise ValueError("YRef must be top, center, or bottom")
        if key in {"XPos", "YPos"}:
            number = percent_value(text, float("nan"))
            if not -200 <= number <= 200:
                raise ValueError(f"{key} must be between -200% and 200%")
            text = f"{number:.6f}%"
        elif key in {"Width", "Height"}:
            number = int(text)
            if not 1 <= number <= 8192:
                raise ValueError(f"{key} must be between 1 and 8192")
            text = str(number)
        elif key in {
            "Alpha",
            "FadeToAlpha",
            "BGTint.red",
            "BGTint.green",
            "BGTint.blue",
        }:
            number = int(text)
            if not 0 <= number <= 255:
                raise ValueError(f"{key} must be between 0 and 255")
            text = str(number)
        elif key in {"Fades", "Locked", "Show"}:
            if text not in {"0", "1"}:
                raise ValueError(f"{key} must be 0 or 1")
        elif key == "BGType":
            number = int(text)
            if not 0 <= number <= 3:
                raise ValueError("BGType must be between 0 and 3")
            text = str(number)
        result[key] = text
    return result


def validated_layout_sections(raw: Any) -> dict[str, dict[str, str]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("sections must be a nonempty array")
    if len(raw) > 256:
        raise ValueError("no more than 256 sections may be saved at once")
    result: dict[str, dict[str, str]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each section update must be an object")
        section = str(item.get("section", ""))
        if not section or any(character in section for character in "[]\r\n"):
            raise ValueError("section name is invalid")
        if section in result:
            raise ValueError(f"layout section is duplicated in the request: {section}")
        result[section] = validated_settings(item.get("settings"))
    return result


def safe_xml_path(skin: Path, filename: str) -> Path:
    if Path(filename).name != filename or not filename.lower().endswith(".xml"):
        raise ValueError("XML file must be a top-level .xml filename")
    if filename.casefold() == "equi.xml":
        raise ValueError("EQUI.xml is the skin manifest and is not editable in Studio")
    path = skin / filename
    if not path.is_file():
        raise ValueError(f"XML file does not exist: {filename}")
    if is_link_like(path):
        raise ValueError(f"XML symlinks are not editable: {filename}")
    if path.resolve().parent != skin.resolve():
        raise ValueError(f"XML file escapes the skin workspace: {filename}")
    if path.stat().st_size > MAX_REQUEST_BYTES:
        raise ValueError(f"XML file exceeds {MAX_REQUEST_BYTES} bytes: {filename}")
    return path


def equi_manifest_includes(root: ET.Element) -> list[str]:
    top_level_names = [local_name(element.tag) for element in root]
    composites = [element for element in root if local_name(element.tag) == "Composite"]
    if len(composites) != 1:
        raise ValueError(
            "EQUI.xml must contain exactly one top-level Composite manifest; "
            f"found {len(composites)}"
        )
    unexpected = sorted({name for name in top_level_names if name not in {"Composite", "Schema"}})
    if unexpected:
        raise ValueError(
            f"EQUI.xml contains unexpected top-level elements: {', '.join(unexpected)}"
        )
    includes = [
        (element.text or "").strip()
        for element in composites[0].iter()
        if local_name(element.tag) == "Include"
    ]
    if not includes:
        raise ValueError("EQUI.xml Composite manifest contains no Include entries")
    return includes


def validate_xml(contents: str, *, filename: str | None = None) -> bytes:
    try:
        encoded = contents.encode("us-ascii")
    except UnicodeEncodeError as error:
        raise ValueError("EQ UI XML must remain US-ASCII") from error
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ValueError(f"EQ UI XML must not exceed {MAX_REQUEST_BYTES} bytes")
    try:
        root = ET.fromstring(encoded)
    except ET.ParseError as error:
        raise ValueError(f"XML is not well formed: {error}") from error
    if local_name(root.tag) != "XML":
        raise ValueError("root element must be XML")
    if root.get("ID") != "EQInterfaceDefinitionLanguage":
        raise ValueError("root ID must be EQInterfaceDefinitionLanguage")
    if filename is not None and filename.casefold() == "equi.xml":
        equi_manifest_includes(root)
    return encoded


def skin_manifest_includes(skin: Path) -> list[str]:
    path = skin / "EQUI.xml"
    if is_link_like(path) or not path.is_file() or path.resolve().parent != skin.resolve():
        raise ValueError("workspace skin must contain a physical top-level EQUI.xml manifest")
    if path.stat().st_size > MAX_REQUEST_BYTES:
        raise ValueError(f"EQUI.xml exceeds {MAX_REQUEST_BYTES} bytes")
    try:
        contents = path.read_text(encoding="us-ascii")
    except (OSError, UnicodeError) as error:
        raise ValueError("EQUI.xml must be readable US-ASCII") from error
    encoded = validate_xml(contents, filename=path.name)
    root = ET.fromstring(encoded)
    return equi_manifest_includes(root)


def validated_manifest_includes(includes: list[str]) -> list[tuple[str, str]]:
    validated: list[tuple[str, str]] = []
    seen: set[str] = set()
    for include in includes:
        folded = include.casefold()
        if not include or Path(include).name != include or not include.endswith(".xml"):
            raise ValueError(f"EQUI.xml contains an unsafe Include: {include!r}")
        if folded in seen:
            raise ValueError(f"EQUI.xml contains a duplicate Include: {include}")
        validated.append((include, folded))
        seen.add(folded)
    return validated


def validate_skin_manifest(skin: Path) -> None:
    includes = validated_manifest_includes(skin_manifest_includes(skin))
    available = {
        candidate.name.casefold()
        for candidate in skin.glob("*.xml")
        if candidate.is_file() and not is_link_like(candidate)
    }
    for include, folded in includes:
        if folded not in available:
            raise ValueError(f"EQUI.xml includes a missing XML file: {include}")


def materialize_manifest_fallback(skin: Path, fallback: Path) -> None:
    includes = validated_manifest_includes(skin_manifest_includes(skin))
    available = {
        candidate.name.casefold()
        for candidate in skin.glob("*.xml")
        if candidate.is_file() and not is_link_like(candidate)
    }
    missing = [(include, folded) for include, folded in includes if folded not in available]
    if not missing:
        validate_skin_manifest(skin)
        return
    if is_link_like(fallback):
        raise ValueError("default skin fallback must not be a symlink")
    if fallback.is_dir():
        fallback_xml = sorted(fallback.glob("*.xml"))
        for include, folded in missing:
            matches = [
                candidate for candidate in fallback_xml if candidate.name.casefold() == folded
            ]
            if len(matches) > 1:
                raise ValueError(f"default skin fallback is ambiguous for: {include}")
            if not matches:
                continue
            candidate = matches[0]
            if (
                is_link_like(candidate)
                or not candidate.is_file()
                or candidate.resolve().parent != fallback.resolve()
            ):
                raise ValueError(f"default skin fallback is unsafe for: {include}")
            destination = skin / candidate.name
            shutil.copy2(candidate, destination, follow_symlinks=False)
            if destination.stat().st_size > MAX_REQUEST_BYTES:
                raise ValueError(f"default skin fallback XML exceeds size limit: {include}")
            try:
                contents = destination.read_text(encoding="us-ascii")
            except (OSError, UnicodeError) as error:
                raise ValueError(
                    f"default skin fallback XML is not readable US-ASCII: {include}"
                ) from error
            try:
                validate_xml(contents)
            except ValueError as error:
                raise ValueError(
                    f"default skin fallback XML is invalid: {include}: {error}"
                ) from error
    validate_skin_manifest(skin)


def game_layouts(game: Path) -> list[Path]:
    return sorted(
        path for path in game.glob("UI_*.ini") if path.is_file() and not is_link_like(path)
    )


def choose_layout(game: Path, requested: str | None) -> Path:
    candidates = game_layouts(game)
    if requested:
        if Path(requested).name != requested or not LAYOUT_NAME_PATTERN.fullmatch(requested):
            raise ValueError("layout must be a top-level UI_*.ini filename")
        path = game / requested
        if path not in candidates:
            raise ValueError(f"layout is not a current game UI INI: {requested}")
        return path
    if not candidates:
        raise ValueError("no top-level UI_*.ini files were found in the selected game directory")
    if len(candidates) == 1:
        return candidates[0]
    if not sys.stdin.isatty():
        raise ValueError("multiple UI INIs found; pass --layout UI_name.ini")
    print("Choose the current layout to capture:")
    for index, path in enumerate(candidates, start=1):
        recommendation = " (recommended)" if path.name == "UI_plazmic_1440p.ini" else ""
        print(f"  {index}. {path.name}{recommendation}")
    while True:
        try:
            answer = input("Layout number: ").strip()
        except EOFError as error:
            raise ValueError("layout selection ended; pass --layout UI_name.ini") from error
        try:
            selected = int(answer)
            if selected < 1:
                raise ValueError
            return candidates[selected - 1]
        except (ValueError, IndexError):
            print("Enter one of the listed numbers.")


def write_config(
    repo: Path,
    game: Path,
    layout_name: str,
    resolution: tuple[int, int],
) -> None:
    width, height = resolution
    contents = (
        json.dumps(
            {
                "game_dir": str(game),
                "active_layout": layout_name,
                "resolution": f"{width}x{height}",
            },
            indent=2,
        ).encode("utf-8")
        + b"\n"
    )
    workspace = local_workspace(repo, create=True)
    atomic_write(workspace / "studio.json", contents, workspace / "backups")


def read_layout_contents(game: Path, layout: Path) -> bytes:
    if not LAYOUT_NAME_PATTERN.fullmatch(layout.name):
        raise ValueError(f"invalid layout filename: {layout.name}")
    if is_link_like(layout) or layout.parent.resolve() != game.resolve():
        raise ValueError("layout must be a top-level regular game file")
    before = layout.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("layout must be a top-level regular game file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if os.name != "nt":
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        if not no_follow:
            raise ValueError("safe no-follow layout reads are unsupported on this platform")
        flags |= no_follow
    try:
        descriptor = os.open(layout, flags)
    except OSError as error:
        raise ValueError(f"unable to safely open layout: {layout.name}") from error

    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
    )
    with os.fdopen(descriptor, "rb") as source:
        opened = os.fstat(source.fileno())
        identity_opened = (
            opened.st_dev,
            opened.st_ino,
            opened.st_mode,
            opened.st_size,
            opened.st_mtime_ns,
        )
        if identity_opened != identity_before or not stat.S_ISREG(opened.st_mode):
            raise ValueError(f"layout changed before it could be read: {layout.name}")
        contents = source.read(MAX_REQUEST_BYTES + 1)
        after = os.fstat(source.fileno())
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_opened != identity_after or len(contents) != after.st_size:
        raise ValueError(f"layout changed while it was being read; try again: {layout.name}")
    if len(contents) > MAX_REQUEST_BYTES:
        raise ValueError(f"layout exceeds the {MAX_REQUEST_BYTES}-byte limit")
    if not contents:
        raise ValueError(f"layout is empty: {layout.name}")
    return contents


def capture_layout(
    repo: Path,
    game: Path,
    layout: Path,
    resolution: tuple[int, int],
) -> Path:
    contents = read_layout_contents(game, layout)
    workspace = local_workspace(repo, create=True)
    destination = workspace / "layouts" / layout.name
    atomic_write(destination, contents, workspace / "backups")
    write_config(repo, game, layout.name, resolution)
    return destination


def capture_workspace(
    repo: Path,
    game: Path,
    layout: Path,
    resolution: tuple[int, int] = (DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT),
) -> tuple[Path, Path]:
    read_layout_contents(game, layout)
    installed_skin = game / "uifiles" / "plazmic-ui"
    source_skin = (
        installed_skin
        if (installed_skin / "EQUI.xml").is_file()
        else game / "uifiles" / "default_modern"
    )
    if not (source_skin / "EQUI.xml").is_file():
        raise ValueError("no usable UI skin was found in the selected game directory")
    symlink = first_symlink(source_skin)
    if symlink is not None:
        raise ValueError("source skin contains a symlink")
    validated_manifest_includes(skin_manifest_includes(source_skin))
    workspace = local_workspace(repo, create=True)
    skin_destination = workspace / "skin"
    staging = Path(tempfile.mkdtemp(prefix=".capture.", dir=workspace))
    skin_backup: Path | None = None
    try:
        shutil.copytree(
            source_skin,
            staging,
            ignore=ignored_game_sidecar,
            dirs_exist_ok=True,
        )
        materialize_manifest_fallback(staging, game / "uifiles" / "default")
        (staging / ".plazmic-upstream").write_text(
            f"source={source_skin.name}\ncaptured_at={datetime.now().astimezone().isoformat()}\n",
            encoding="ascii",
        )
        if skin_destination.exists():
            skin_backup = workspace / f"skin.backup-{timestamp()}"
            os.replace(skin_destination, skin_backup)
        os.replace(staging, skin_destination)
    except Exception:
        if skin_backup is not None and not skin_destination.exists():
            os.replace(skin_backup, skin_destination)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    layout_destination = capture_layout(repo, game, layout, resolution)
    return skin_destination, layout_destination


def copy_skin_atomically(source: Path, target: Path) -> Path | None:
    symlink = first_symlink(source)
    if symlink is not None:
        raise ValueError("workspace skin contains a symlink")
    if is_link_like(target):
        raise ValueError("installed skin target is a symlink")
    if target.exists() and not target.is_dir():
        raise ValueError("installed skin target must be a physical directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".plazmic-ui.install.", dir=target.parent))
    backup: Path | None = None
    try:
        shutil.rmtree(staging)
        shutil.copytree(source, staging, ignore=ignored_game_sidecar)
        if target.exists():
            backup = target.parent / f"{target.name}.backup-{timestamp()}"
            os.replace(target, backup)
        os.replace(staging, target)
    except Exception:
        if backup is not None and not target.exists():
            os.replace(backup, target)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return backup


def restore_skin_after_failed_publish(target: Path, backup: Path | None) -> None:
    if target.exists():
        if is_link_like(target) or not target.is_dir():
            raise OSError("cannot roll back an unexpected skin target")
        shutil.rmtree(target)
    if backup is not None:
        os.replace(backup, target)


def load_layout_from_game(paths: StudioPaths, source_name: str) -> dict[str, str]:
    source_layout = choose_layout(paths.game, source_name)
    contents = read_layout_contents(paths.game, source_layout)
    if not parse_ini(contents):
        raise ValueError(f"source UI INI has no layout sections: {source_name}")
    if (
        is_link_like(paths.layout)
        or not paths.layout.is_file()
        or paths.layout.resolve().parent != paths.layouts.resolve()
    ):
        raise ValueError("workspace layout must be a top-level physical file")
    backup = atomic_write(paths.layout, contents, paths.backups)
    return {
        "source": source_layout.name,
        "layout": paths.layout.name,
        "layoutBackup": backup.name if backup else "",
    }


def publish_workspace(paths: StudioPaths, target_name: str) -> dict[str, str]:
    if not LAYOUT_NAME_PATTERN.fullmatch(target_name):
        raise ValueError("choose an existing UI_*.ini target")
    target_layout = paths.game / target_name
    if target_layout not in game_layouts(paths.game):
        raise ValueError(f"target UI INI does not exist: {target_name}")
    if is_link_like(target_layout):
        raise ValueError(f"target UI INI must not be a symlink: {target_name}")
    if not (paths.skin / "EQUI.xml").is_file():
        raise ValueError("workspace skin is incomplete")
    symlink = first_symlink(paths.skin)
    if symlink is not None:
        raise ValueError("workspace skin contains a symlink")
    validate_skin_manifest(paths.skin)
    if is_link_like(paths.layout) or not paths.layout.is_file():
        raise ValueError("workspace layout must be a physical regular file")
    layout_contents = paths.layout.read_bytes()
    if len(layout_contents) > MAX_REQUEST_BYTES:
        raise ValueError(f"layout exceeds the {MAX_REQUEST_BYTES}-byte limit")

    skin_target = paths.game / "uifiles" / "plazmic-ui"
    skin_backup = copy_skin_atomically(paths.skin, skin_target)
    layout_backup = target_layout.parent / f"{target_layout.name}.backup-{timestamp()}"
    temporary: Path | None = None
    layout_replaced = False
    try:
        shutil.copy2(target_layout, layout_backup)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target_layout.name}.", suffix=".tmp", dir=target_layout.parent
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(layout_contents)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(target_layout.stat().st_mode & 0o777)
        os.replace(temporary, target_layout)
        temporary = None
        layout_replaced = True
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if layout_replaced and layout_backup.exists():
            os.replace(layout_backup, target_layout)
        elif layout_backup.exists():
            layout_backup.unlink()
        restore_skin_after_failed_publish(skin_target, skin_backup)
        raise
    return {
        "skin": skin_target.name,
        "skinBackup": skin_backup.name if skin_backup else "",
        "layout": target_layout.name,
        "layoutBackup": layout_backup.name,
        "instructions": (
            "In EQ run /loadskin plazmic-ui 1, then /copylayout if the target "
            "character is different."
        ),
    }


def load_local_config(repo: Path) -> dict[str, str]:
    workspace = repo / WORKSPACE_DIRECTORY
    if is_link_like(workspace):
        raise ValueError(f"private workspace must not be a symlink: {workspace}")
    path = workspace / "studio.json"
    if not path.is_file():
        return {}
    if is_link_like(path):
        raise ValueError(f"Studio configuration must not be a symlink: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {key: str(item) for key, item in value.items() if isinstance(item, str)}


def resolve_paths(args: argparse.Namespace, repo: Path) -> StudioPaths:
    config = load_local_config(repo)
    game_value = args.game_dir or os.environ.get("EQ_LEGENDS_DIR") or config.get("game_dir")
    if not game_value:
        raise ValueError("set EQ_LEGENDS_DIR or pass --game-dir")
    game = Path(game_value).expanduser().resolve()
    if not (game / "eqgame.exe").is_file():
        raise ValueError("eqgame.exe was not found in the selected game directory")
    layout_name = args.layout or config.get("active_layout")
    workspace = local_workspace(repo, create=False)
    layout_dir = workspace / "layouts"
    if layout_name:
        if Path(layout_name).name != layout_name:
            raise ValueError("local layout must be a filename inside the workspace layouts")
        layout = layout_dir / layout_name
    else:
        local_layouts = sorted(layout_dir.glob("UI_*.ini"))
        if len(local_layouts) != 1:
            raise ValueError("capture or select a local layout with --layout")
        layout = local_layouts[0]
    if not layout.is_file():
        raise ValueError("the selected local layout was not found")
    if is_link_like(layout):
        raise ValueError("the selected local layout must not be a symlink")
    if layout.stat().st_size > MAX_REQUEST_BYTES:
        raise ValueError(f"local layout exceeds the {MAX_REQUEST_BYTES}-byte limit")
    resolution = parse_resolution(args.resolution or config.get("resolution"))
    return StudioPaths(
        repo=repo,
        skin=workspace / "skin",
        layouts=layout_dir,
        backups=workspace / "backups",
        config=workspace / "studio.json",
        game=game,
        layout=layout,
        screen_width=resolution[0],
        screen_height=resolution[1],
    )


class StudioHandler(BaseHTTPRequestHandler):
    server: StudioServer

    def log_message(self, message: str, *args: object) -> None:
        pass

    def _valid_host(self) -> bool:
        return constant_time_header(self.headers.get("Host", ""), self.server.authority)

    def _authorized(self) -> bool:
        token_valid = constant_time_header(
            self.headers.get("X-Plazmic-Token", ""), self.server.token
        )
        origin = self.headers.get("Origin")
        return token_valid and origin in {None, self.server.origin}

    def _security_headers(self) -> None:
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "style-src 'self'; script-src 'self'; base-uri 'none'; "
            "form-action 'none'; frame-ancestors 'none'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")

    def _json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        contents = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(contents)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(contents)

    def _error(self, error: Exception) -> None:
        message = "local file operation failed" if isinstance(error, OSError) else str(error)
        self._json({"error": message}, HTTPStatus.BAD_REQUEST)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0:
            raise ValueError("invalid request length")
        if length > MAX_REQUEST_BYTES:
            raise ValueError("request is too large")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("request body must be an object")
        return value

    def do_GET(self) -> None:
        if not self._valid_host():
            self.send_error(HTTPStatus.MISDIRECTED_REQUEST)
            return
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/"):
            if not self._authorized():
                self._json({"error": "unauthorized"}, HTTPStatus.FORBIDDEN)
                return
            try:
                if parsed.path == "/api/state":
                    self._json(layout_state(self.server.paths))
                    return
                if parsed.path == "/api/xml":
                    filename = parse_qs(parsed.query).get("file", [""])[0]
                    path = safe_xml_path(self.server.paths.skin, filename)
                    self._json({"file": filename, "contents": path.read_text(encoding="ascii")})
                    return
                raise ValueError("unknown API endpoint")
            except (OSError, UnicodeError, ValueError) as error:
                self._error(error)
            return

        filename = "index.html" if parsed.path in {"", "/"} else parsed.path[1:]
        if filename not in STATIC_CONTENT_TYPES:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        path = self.server.static_dir / filename
        try:
            contents = path.read_bytes()
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if filename == "index.html":
            contents = contents.replace(b"__PLAZMIC_TOKEN__", self.server.token.encode("ascii"))
        content_type = STATIC_CONTENT_TYPES[filename]
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(contents)))
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()
        self.wfile.write(contents)

    def do_POST(self) -> None:
        if not self._valid_host() or not self._authorized():
            self._json({"error": "unauthorized"}, HTTPStatus.FORBIDDEN)
            return
        try:
            body = self._body()
            with self.server.write_lock:
                if self.path == "/api/layout":
                    if "sections" in body:
                        updates = validated_layout_sections(body.get("sections"))
                        update_ini_sections(
                            self.server.paths.layout,
                            updates,
                            self.server.paths.backups,
                        )
                    else:
                        section = str(body.get("section", ""))
                        settings = validated_settings(body.get("settings"))
                        update_ini_section(
                            self.server.paths.layout,
                            section,
                            settings,
                            self.server.paths.backups,
                        )
                    self._json({"ok": True, "state": layout_state(self.server.paths)})
                    return
                if self.path == "/api/xml":
                    filename = str(body.get("file", ""))
                    path = safe_xml_path(self.server.paths.skin, filename)
                    contents = validate_xml(str(body.get("contents", "")), filename=filename)
                    atomic_write(path, contents, self.server.paths.backups)
                    self._json({"ok": True})
                    return
                if self.path == "/api/load":
                    result = load_layout_from_game(
                        self.server.paths, str(body.get("sourceIni", ""))
                    )
                    self._json({"ok": True, **result})
                    return
                if self.path == "/api/publish":
                    result = publish_workspace(self.server.paths, str(body.get("targetIni", "")))
                    self._json({"ok": True, **result})
                    return
                raise ValueError("unknown API endpoint")
        except (json.JSONDecodeError, OSError, UnicodeError, ValueError) as error:
            self._error(error)


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], paths: StudioPaths, static: Path):
        super().__init__(address, StudioHandler)
        self.paths = paths
        self.static_dir = static
        self.token = secrets.token_urlsafe(24)
        self.write_lock = threading.Lock()
        self.authority = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.authority}"


def serve(paths: StudioPaths, static_dir: Path, port: int, open_browser: bool) -> None:
    server = StudioServer(("127.0.0.1", port), paths, static_dir)
    url = f"{server.origin}/"
    print(f"Plazmic UI Studio: {url}")
    print(f"Editing layout: {paths.layout.name}")
    print("Press Ctrl-C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Plazmic UI Studio.")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline Plazmic EQ UI studio")
    parser.add_argument("--version", action="version", version=f"{APPLICATION_NAME} {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture_parser = subparsers.add_parser(
        "capture", help="capture the installed skin and one current UI INI"
    )
    capture_parser.add_argument("--game-dir")
    capture_parser.add_argument("--layout")
    capture_parser.add_argument(
        "--resolution",
        help="mock canvas size as WIDTHxHEIGHT (default: 2560x1440)",
    )
    capture_parser.add_argument(
        "--layout-only",
        action="store_true",
        help="capture only the selected layout and keep the existing skin workspace",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        aliases=["studio"],
        help="open the local drag-and-drop UI editor",
    )
    serve_parser.add_argument("--game-dir")
    serve_parser.add_argument("--layout")
    serve_parser.add_argument("--resolution", help="mock canvas size as WIDTHxHEIGHT")
    serve_parser.add_argument("--port", type=int, default=0)
    serve_parser.add_argument("--no-browser", action="store_true")

    publish_parser = subparsers.add_parser(
        "publish", help="publish the workspace skin and layout into EQ"
    )
    publish_parser.add_argument("--game-dir")
    publish_parser.add_argument("--layout")
    publish_parser.add_argument("--resolution", help=argparse.SUPPRESS)
    publish_parser.add_argument("--target-ini")

    subparsers.add_parser(
        "diagnose",
        help="verify the packaged Studio frontend without accessing game files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    repo = application_data_root(script_dir)
    static_dir = static_directory(script_dir)
    try:
        if args.command == "diagnose":
            validate_frontend_bundle(static_dir)
            print(f"{APPLICATION_NAME} {VERSION}: frontend bundle is ready")
            return 0

        if args.command == "capture":
            game_value = args.game_dir or os.environ.get("EQ_LEGENDS_DIR")
            if not game_value:
                raise ValueError("set EQ_LEGENDS_DIR or pass --game-dir")
            game = Path(game_value).expanduser().resolve()
            if not (game / "eqgame.exe").is_file():
                raise ValueError("eqgame.exe was not found in the selected game directory")
            layout = choose_layout(game, args.layout)
            resolution = parse_resolution(args.resolution)
            if args.layout_only:
                skin = repo / WORKSPACE_DIRECTORY / "skin"
                if not (skin / "EQUI.xml").is_file():
                    raise ValueError(
                        "layout-only capture requires an existing private skin workspace"
                    )
                local_layout = capture_layout(repo, game, layout, resolution)
            else:
                skin, local_layout = capture_workspace(repo, game, layout, resolution)
                print("Captured the private skin workspace.")
            print(f"Captured layout: {local_layout.name}")
            print("Open the editor with: ./plazmic-ui studio")
            return 0

        paths = resolve_paths(args, repo)
        if args.command in {"serve", "studio"}:
            if not all((static_dir / name).is_file() for name in STATIC_CONTENT_TYPES):
                raise ValueError("Studio frontend files are missing from this installation")
            serve(paths, static_dir, args.port, not args.no_browser)
            return 0
        if args.command == "publish":
            target = choose_layout(paths.game, args.target_ini).name
            result = publish_workspace(paths, target)
            print(f"Published skin: {result['skin']}")
            print(f"Published layout: {result['layout']}")
            print(result["instructions"])
            return 0
        raise ValueError(f"unknown command: {args.command}")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"plazmic-ui-studio: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
