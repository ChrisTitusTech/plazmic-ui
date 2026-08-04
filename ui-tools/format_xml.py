#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

LEADING_WHITESPACE = re.compile(r"^[ \t]+")


def format_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    output_lines: list[str] = []

    for line in normalized.splitlines():
        line = line.rstrip(" \t")
        match = LEADING_WHITESPACE.match(line)
        if match is not None:
            indentation = match.group(0).expandtabs(2)
            line = indentation + line[match.end() :]
        output_lines.append(line)

    return "\n".join(output_lines) + "\n"


def format_bytes(contents: bytes) -> bytes:
    return format_text(contents.decode("us-ascii")).encode("us-ascii")


def format_directory(ui_dir: Path, *, in_place: bool) -> tuple[int, int]:
    paths = sorted(ui_dir.glob("*.xml"))

    if not paths:
        raise ValueError(f"No XML files found in: {ui_dir}")

    formatted_files: dict[Path, tuple[bytes, bytes]] = {}
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"XML input must be a physical regular file: {path.name}")
        original = path.read_bytes()
        formatted = format_bytes(original)
        if formatted == original:
            continue
        formatted_files[path] = (original, formatted)

    if in_place:
        temporary_files: dict[Path, Path] = {}
        replaced: list[Path] = []
        try:
            for path, (_, formatted) in formatted_files.items():
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
                )
                temporary = Path(temporary_name)
                temporary_files[path] = temporary
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(formatted)
                    handle.flush()
                    os.fsync(handle.fileno())
                temporary.chmod(path.stat().st_mode & 0o777)
            for path, temporary in temporary_files.items():
                os.replace(temporary, path)
                replaced.append(path)
        except Exception:
            for path in reversed(replaced):
                descriptor, rollback_name = tempfile.mkstemp(
                    prefix=f".{path.name}.", suffix=".rollback", dir=path.parent
                )
                rollback = Path(rollback_name)
                try:
                    with os.fdopen(descriptor, "wb") as handle:
                        handle.write(formatted_files[path][0])
                        handle.flush()
                        os.fsync(handle.fileno())
                    rollback.chmod(path.stat().st_mode & 0o777)
                    os.replace(rollback, path)
                finally:
                    rollback.unlink(missing_ok=True)
            raise
        finally:
            for temporary in temporary_files.values():
                temporary.unlink(missing_ok=True)

    return len(paths), len(formatted_files)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize EQ XML line endings and indentation without "
            "reserializing mixed-content elements."
        )
    )
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("ui_directory", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        total, changed = format_directory(args.ui_directory, in_place=args.in_place)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"format-xml: {error}", file=sys.stderr)
        return 1

    if not args.in_place and changed:
        print(
            f"{changed} of {total} XML files need formatting.",
            file=sys.stderr,
        )
        return 1

    action = "Formatted" if args.in_place else "Checked"
    print(f"{action} {total} XML files ({changed} changed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
