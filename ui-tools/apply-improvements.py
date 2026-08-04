#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
HASH_MANIFEST = SCRIPT_DIR / "upstream.sha256"
ADVANCED_LOOT_FILE = "EQUI_AdvancedLootWnd.xml"


def expected_hash(filename: str) -> str:
    for raw_line in HASH_MANIFEST.read_text(encoding="ascii").splitlines():
        digest, manifest_filename = raw_line.split(maxsplit=1)
        if manifest_filename == filename:
            return digest
    raise ValueError(f"No reviewed source hash for {filename}")


def replace_once(text: str, old: str, new: str, description: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{description}: expected one source match, found {count}")
    return text.replace(old, new, 1)


def deduplicate_screen_properties(
    text: str,
    item: str,
    property_names: tuple[str, ...],
) -> str:
    screen_pattern = re.compile(
        rf'(<Screen item="{re.escape(item)}">)(.*?)(</Screen>)',
        re.DOTALL,
    )
    match = screen_pattern.search(text)
    if match is None:
        raise ValueError(f"duplicate cleanup: missing screen {item}")
    body = match.group(2)
    for property_name in property_names:
        line_pattern = re.compile(
            rf"^[ \t]*<{re.escape(property_name)}>.*?</{re.escape(property_name)}>"
            rf"[ \t]*(?:\n|$)",
            re.MULTILINE,
        )
        matches = list(line_pattern.finditer(body))
        if len(matches) != 2:
            raise ValueError(
                f"{item} {property_name}: expected two source properties, found {len(matches)}"
            )
        second = matches[1]
        body = body[: second.start()] + body[second.end() :]
    return text[: match.start(2)] + body + text[match.end(2) :]


def improve_advanced_loot(text: str) -> str:
    text = replace_once(
        text,
        "tradeskill depo or item hoard",
        "tradeskill depot or item hoard",
        "depot tooltip correction",
    )

    text = deduplicate_screen_properties(
        text,
        "ADLW_LootListScreen",
        ("Style_Border",),
    )
    text = deduplicate_screen_properties(
        text,
        "ADLW_CheckboxesScreen",
        ("DrawTemplate", "Style_Border"),
    )

    size_pattern = re.compile(
        r'(<Screen item="AdvancedLootWnd">.*?<Size>\s*<CX>)450'
        r"(</CX>\s*<CY>)450(</CY>)",
        re.DOTALL,
    )
    text, count = size_pattern.subn(r"\g<1>800\g<2>600\g<3>", text, count=1)
    if count != 1:
        raise ValueError(f"advanced loot default size: expected one source match, found {count}")

    marker = "\n\t<!-- Templates for dynamic loot list -->"
    text = replace_once(
        text,
        marker,
        (f"\n\t<!-- Plazmic: locally derived from default_modern; see README.md. -->{marker}"),
        "Plazmic source marker",
    )
    return text


def apply(ui_dir: Path) -> None:
    if ui_dir.is_symlink() or not ui_dir.is_dir():
        raise ValueError("UI source must be a physical directory")
    if not (ui_dir / "EQUI.xml").is_file():
        raise ValueError("UI source is incomplete")
    path = ui_dir / ADVANCED_LOOT_FILE
    if path.is_symlink() or not path.is_file():
        raise ValueError("Advanced Loot source must be a physical regular file")

    source_bytes = path.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()
    reviewed_hash = expected_hash(ADVANCED_LOOT_FILE)
    if actual_hash != reviewed_hash:
        raise ValueError(
            "The shipped Advanced Loot XML changed. "
            f"Expected {reviewed_hash}, found {actual_hash}. "
            "Review the new source before updating ui-tools/upstream.sha256."
        )

    source_text = source_bytes.decode("us-ascii").replace("\r\n", "\n")
    improved_text = improve_advanced_loot(source_text)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="us-ascii", newline="\n") as handle:
            handle.write(improved_text)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply reviewed Plazmic transformations to a fresh UI clone."
    )
    parser.add_argument("ui_directory", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        apply(args.ui_directory)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"apply-improvements: {error}", file=sys.stderr)
        return 1

    print(f"Applied Plazmic improvements to {args.ui_directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
