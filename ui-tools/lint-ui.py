#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from format_xml import format_bytes


@dataclass(frozen=True)
class Finding:
    path: Path
    message: str


def local_name(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1]


def element_with_item(root: ET.Element, item: str) -> ET.Element | None:
    for element in root.iter():
        if element.get("item") == item:
            return element
    return None


def child_text(element: ET.Element, child_name: str) -> str | None:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return None


def direct_child_count(element: ET.Element, child_name: str) -> int:
    return sum(1 for child in element if local_name(child.tag) == child_name)


def parse_xml(path: Path) -> tuple[ET.Element | None, list[Finding]]:
    try:
        return ET.parse(path).getroot(), []
    except (ET.ParseError, OSError) as error:
        return None, [Finding(path, f"not well-formed XML: {error}")]


def lint_advanced_loot(path: Path, root: ET.Element) -> list[Finding]:
    findings: list[Finding] = []

    advanced_window = element_with_item(root, "AdvancedLootWnd")
    if advanced_window is None:
        return [Finding(path, "missing AdvancedLootWnd screen")]

    size = next(
        (child for child in advanced_window if local_name(child.tag) == "Size"),
        None,
    )
    if size is None or child_text(size, "CX") != "800":
        findings.append(Finding(path, "AdvancedLootWnd width must be 800"))
    if size is None or child_text(size, "CY") != "600":
        findings.append(Finding(path, "AdvancedLootWnd height must be 600"))

    for item, unique_children in (
        ("ADLW_LootListScreen", ("Style_Border",)),
        ("ADLW_CheckboxesScreen", ("DrawTemplate", "Style_Border")),
    ):
        element = element_with_item(root, item)
        if element is None:
            findings.append(Finding(path, f"missing {item}"))
            continue
        for child_name in unique_children:
            count = direct_child_count(element, child_name)
            if count != 1:
                findings.append(
                    Finding(
                        path,
                        f"{item} must contain one {child_name}; found {count}",
                    )
                )

    try:
        text = path.read_text(encoding="us-ascii")
    except (OSError, UnicodeError) as error:
        findings.append(Finding(path, f"could not inspect Advanced Loot text: {error}"))
    else:
        if "tradeskill depo or item hoard" in text:
            findings.append(Finding(path, "contains the upstream depot typo"))

    return findings


def lint_directory(ui_dir: Path, *, check_format: bool) -> tuple[list[Finding], int]:
    findings: list[Finding] = []

    if not ui_dir.is_dir():
        return [Finding(ui_dir, "UI directory does not exist")], 0
    if ui_dir.is_symlink():
        return [Finding(ui_dir, "UI directory must not be a symlink")], 0

    symlink_paths = sorted(path for path in ui_dir.rglob("*") if path.is_symlink())
    for path in symlink_paths:
        findings.append(Finding(path, "symlinks are not allowed in a UI workspace"))

    xml_paths = sorted(path for path in ui_dir.glob("*.xml") if not path.is_symlink())
    if not xml_paths:
        return [Finding(ui_dir, "no top-level XML files found")], 0

    crc_paths = sorted(
        path
        for path in ui_dir.rglob("*")
        if path.is_file() and (path.name.endswith(".crc") or path.name.endswith(":crc"))
    )
    for path in crc_paths:
        findings.append(Finding(path, "stale launcher CRC sidecars are not allowed"))

    parsed: dict[Path, ET.Element] = {}
    for path in xml_paths:
        root, parse_findings = parse_xml(path)
        findings.extend(parse_findings)
        if root is None:
            continue
        parsed[path] = root

        if local_name(root.tag) != "XML":
            findings.append(Finding(path, "root element must be XML"))
        if root.get("ID") != "EQInterfaceDefinitionLanguage":
            findings.append(
                Finding(
                    path,
                    "root ID must be EQInterfaceDefinitionLanguage",
                )
            )

        for element in root.iter():
            item = element.get("item")
            if item is not None and (
                not item.strip() or any(ord(character) < 32 for character in item)
            ):
                findings.append(Finding(path, f"invalid item identifier: {item!r}"))

    equi_path = ui_dir / "EQUI.xml"
    equi_root = parsed.get(equi_path)
    if equi_root is None:
        findings.append(Finding(equi_path, "missing or invalid EQUI.xml"))
    else:
        includes = [
            (element.text or "").strip()
            for element in equi_root.iter()
            if local_name(element.tag) == "Include"
        ]
        available_paths = sorted(ui_dir.glob("*.xml"))
        available_names: dict[str, Path] = {}
        for candidate in available_paths:
            folded_name = candidate.name.casefold()
            if folded_name in available_names:
                findings.append(
                    Finding(
                        candidate,
                        f"top-level XML name conflicts case-insensitively: {candidate.name}",
                    )
                )
            else:
                available_names[folded_name] = candidate
        include_names = {name.casefold(): name for name in includes}
        for folded_include, count in Counter(name.casefold() for name in includes).items():
            include = include_names[folded_include]
            if not include:
                findings.append(Finding(equi_path, "contains an empty Include"))
            elif Path(include).name != include or not include.endswith(".xml"):
                findings.append(Finding(equi_path, f"unsafe Include path: {include!r}"))
            elif folded_include not in available_names:
                findings.append(Finding(equi_path, f"missing included file: {include}"))
            if count > 1:
                findings.append(Finding(equi_path, f"duplicate Include: {include}"))

    advanced_path = ui_dir / "EQUI_AdvancedLootWnd.xml"
    advanced_root = parsed.get(advanced_path)
    if advanced_root is None:
        findings.append(Finding(advanced_path, "missing or invalid Advanced Loot XML"))
    else:
        findings.extend(lint_advanced_loot(advanced_path, advanced_root))

    if check_format:
        for path in parsed:
            try:
                expected = format_bytes(path.read_bytes())
            except UnicodeError as error:
                findings.append(Finding(path, f"formatter failed: {error}"))
                continue
            if path.read_bytes() != expected:
                findings.append(
                    Finding(
                        path,
                        "format differs; run ./plazmic-ui format",
                    )
                )

    return findings, len(xml_paths)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint a materialized Plazmic EverQuest UI.")
    parser.add_argument("--check-format", action="store_true")
    parser.add_argument("ui_directory", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings, xml_count = lint_directory(args.ui_directory, check_format=args.check_format)
    if findings:
        for finding in findings:
            print(f"{finding.path}: {finding.message}", file=sys.stderr)
        print(
            f"UI lint failed with {len(findings)} finding(s).",
            file=sys.stderr,
        )
        return 1

    format_suffix = " and formatting" if args.check_format else ""
    print(f"UI lint passed: {xml_count} XML files{format_suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
