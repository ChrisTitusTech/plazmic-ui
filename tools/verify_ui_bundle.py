#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

ALLOWED_SUFFIXES = {".cur", ".dds", ".ini", ".tga", ".xml"}
MANIFEST_NAME = "SHA256SUMS"
AYA_MANIFEST_NAME = "AYA_LEGENDS_SHA256SUMS"
AYA_LAYOUT_NAME = "UI_Character_Server_LO1.ini"
SENSITIVE_PATTERNS = {
    "absolute home path": re.compile(rb"/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "Wine user path": re.compile(rb"drive_c/users/[A-Za-z0-9._-]+", re.IGNORECASE),
    "Windows absolute path": re.compile(
        rb"\b[A-Za-z]:[\\/](?:[A-Za-z0-9._ -]{2,}[\\/]){1,}[A-Za-z0-9._ -]{2,}"
    ),
    "Windows UNC path": re.compile(
        rb"\\\\[A-Za-z0-9._-]+\\[A-Za-z0-9$._-]+\\(?:Users|[A-Za-z0-9 ._-]{8,})"
    ),
    "GitHub token": re.compile(rb"(?:gh[opsur]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
ASCII_TEXT = re.compile(rb"[\x20-\x7e]{4,}")
UTF16LE_TEXT = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")


@dataclass(frozen=True)
class BundleKind:
    name: str
    manifest_name: str
    manifest_prefix: str
    skin_relative: Path
    archive_prefix: Path | None
    allowed_layouts: frozenset[Path]


BUNDLE_KINDS = {
    "plazmic-ui": BundleKind(
        name="plazmic-ui",
        manifest_name=MANIFEST_NAME,
        manifest_prefix="plazmic-ui",
        skin_relative=Path("."),
        archive_prefix=Path("plazmic-ui"),
        allowed_layouts=frozenset(),
    ),
    "aya-legends": BundleKind(
        name="aya-legends",
        manifest_name=AYA_MANIFEST_NAME,
        manifest_prefix="aya-legends",
        skin_relative=Path("uifiles/AYA_Legends"),
        archive_prefix=None,
        allowed_layouts=frozenset({Path(AYA_LAYOUT_NAME)}),
    ),
}


def bundle_kind(name: str | None, root: Path) -> BundleKind:
    resolved_name = name or ("aya-legends" if root.name == "aya-legends" else "plazmic-ui")
    try:
        return BUNDLE_KINDS[resolved_name]
    except KeyError as error:
        raise ValueError(f"unsupported bundle kind: {resolved_name}") from error


def embedded_text(contents: bytes) -> bytes:
    runs = ASCII_TEXT.findall(contents)
    runs.extend(run[::2] for run in UTF16LE_TEXT.findall(contents))
    return b"\n".join(runs)


def validate_dds(contents: bytes) -> None:
    if (
        len(contents) < 128
        or not contents.startswith(b"DDS ")
        or int.from_bytes(contents[4:8], "little") != 124
        or int.from_bytes(contents[76:80], "little") != 32
    ):
        raise ValueError("bundle contains an invalid DDS file")
    flags = int.from_bytes(contents[8:12], "little")
    height = int.from_bytes(contents[12:16], "little")
    width = int.from_bytes(contents[16:20], "little")
    declared_size = int.from_bytes(contents[20:24], "little")
    data_offset = 148 if contents[84:88] == b"DX10" else 128
    if width == 0 or height == 0 or len(contents) < data_offset:
        raise ValueError("bundle contains an invalid DDS file")
    required_size = 1
    if flags & 0x80000:
        required_size = declared_size
    elif flags & 0x8:
        required_size = declared_size * height
    if required_size == 0 or len(contents) - data_offset < required_size:
        raise ValueError("bundle contains an invalid DDS file")


def validate_cursor(contents: bytes) -> None:
    cursor_count = int.from_bytes(contents[4:6], "little") if len(contents) >= 6 else 0
    directory_end = 6 + (16 * cursor_count)
    if (
        not contents.startswith(b"\x00\x00\x02\x00")
        or cursor_count == 0
        or len(contents) < directory_end
    ):
        raise ValueError("bundle contains an invalid cursor file")
    for index in range(cursor_count):
        entry = contents[6 + (16 * index) : 22 + (16 * index)]
        width = entry[0] or 256
        height = entry[1] or 256
        image_size = int.from_bytes(entry[8:12], "little")
        image_offset = int.from_bytes(entry[12:16], "little")
        if (
            width == 0
            or height == 0
            or image_size == 0
            or image_offset < directory_end
            or image_offset + image_size > len(contents)
        ):
            raise ValueError("bundle contains an invalid cursor file")


def validate_tga(contents: bytes) -> None:
    if len(contents) < 18 or contents[2] not in {1, 2, 3, 9, 10, 11}:
        raise ValueError("bundle contains an invalid TGA file")
    color_map_type = contents[1]
    image_type = contents[2]
    color_map_length = int.from_bytes(contents[5:7], "little")
    color_map_depth = contents[7]
    width = int.from_bytes(contents[12:14], "little")
    height = int.from_bytes(contents[14:16], "little")
    pixel_depth = contents[16]
    if (
        width == 0
        or height == 0
        or color_map_type not in {0, 1}
        or (image_type in {1, 9}) != (color_map_type == 1)
        or pixel_depth not in {8, 15, 16, 24, 32}
        or (color_map_type == 1 and (color_map_length == 0 or color_map_depth == 0))
    ):
        raise ValueError("bundle contains an invalid TGA file")
    color_map_size = (color_map_length * color_map_depth + 7) // 8
    data_offset = 18 + contents[0] + color_map_size
    bytes_per_pixel = (pixel_depth + 7) // 8
    pixel_count = width * height
    if data_offset > len(contents):
        raise ValueError("bundle contains an invalid TGA file")
    if image_type in {1, 2, 3}:
        if len(contents) - data_offset < pixel_count * bytes_per_pixel:
            raise ValueError("bundle contains an invalid TGA file")
        return
    position = data_offset
    decoded_pixels = 0
    while decoded_pixels < pixel_count:
        if position >= len(contents):
            raise ValueError("bundle contains an invalid TGA file")
        packet = contents[position]
        position += 1
        packet_pixels = (packet & 0x7F) + 1
        packet_bytes = bytes_per_pixel if packet & 0x80 else packet_pixels * bytes_per_pixel
        if decoded_pixels + packet_pixels > pixel_count or position + packet_bytes > len(contents):
            raise ValueError("bundle contains an invalid TGA file")
        position += packet_bytes
        decoded_pixels += packet_pixels


def validate_format(path: Path, contents: bytes) -> None:
    suffix = path.suffix.lower()
    if not contents:
        raise ValueError("bundle must not contain empty files")
    if suffix == ".dds":
        validate_dds(contents)
    if suffix == ".cur":
        validate_cursor(contents)
    if suffix == ".tga":
        validate_tga(contents)
    text_contents = embedded_text(contents)
    for label, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text_contents):
            raise ValueError(f"bundle contains a possible {label}")


def read_manifest(manifest: Path, prefix: str = "plazmic-ui") -> dict[str, str]:
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("bundle checksum manifest must be a physical regular file")
    expected: dict[str, str] = {}
    folded_names: set[str] = set()
    for line in manifest.read_text(encoding="ascii").splitlines():
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or not re.fullmatch(r"[0-9a-f]{64}", fields[0]):
            raise ValueError("bundle checksum manifest contains an invalid entry")
        name = fields[1].removeprefix("*")
        path = Path(name)
        if (
            path.is_absolute()
            or len(path.parts) < 2
            or path.parts[0] != prefix
            or ".." in path.parts
            or "\\" in name
        ):
            raise ValueError("bundle checksum manifest contains an unsafe path")
        relative = Path(*path.parts[1:]).as_posix()
        folded_name = relative.casefold()
        if folded_name in folded_names:
            raise ValueError("bundle checksum manifest contains duplicate paths")
        folded_names.add(folded_name)
        expected[relative] = fields[0]
    if not expected:
        raise ValueError("bundle checksum manifest is empty")
    return expected


def verify_bundle(
    root: Path,
    manifest: Path | None = None,
    kind: str | None = None,
) -> int:
    selected_kind = bundle_kind(kind, root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("bundle root must be a physical directory")
    skin_root = root / selected_kind.skin_relative
    if not (skin_root / "EQUI.xml").is_file():
        raise ValueError("bundle is missing EQUI.xml")

    actual_files: dict[str, str] = {}
    folded_names: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("bundle must not contain symbolic links")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("bundle entries must be regular files")
        lower_name = path.name.lower()
        relative_path = path.relative_to(root)
        if (
            lower_name.startswith("ui_")
            and lower_name.endswith(".ini")
            and relative_path not in selected_kind.allowed_layouts
        ):
            raise ValueError("bundle contains an unapproved character UI_*.ini layout")
        if path.name.endswith(":crc") or path.suffix.lower() in {".bak", ".crc"}:
            raise ValueError("bundle must not contain backup or checksum sidecars")
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ValueError("bundle contains an unexpected file type")
        if path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            raise ValueError("bundle files must not be executable")
        contents = path.read_bytes()
        validate_format(path, contents)
        relative = path.relative_to(root).as_posix()
        folded_name = relative.casefold()
        if folded_name in folded_names:
            raise ValueError("bundle contains case-insensitive duplicate paths")
        folded_names.add(folded_name)
        actual_files[relative] = hashlib.sha256(contents).hexdigest()

    if not actual_files:
        raise ValueError("bundle is empty")
    expected_files = read_manifest(
        manifest or root.parent / selected_kind.manifest_name,
        selected_kind.manifest_prefix,
    )
    if set(actual_files) != set(expected_files):
        raise ValueError("bundle inventory differs from the reviewed checksum manifest")
    for relative, digest in actual_files.items():
        if digest != expected_files[relative]:
            raise ValueError("bundle content differs from the reviewed checksum manifest")
    return len(actual_files)


def verify_archive(archive: Path, root: Path, kind: str | None = None) -> int:
    selected_kind = bundle_kind(kind, root)
    if archive.is_symlink() or not archive.is_file():
        raise ValueError("bundle archive must be a physical regular file")

    expected_files = {
        path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()
    }
    archived_files: dict[str, zipfile.ZipInfo] = {}
    folded_names: set[str] = set()

    with zipfile.ZipFile(archive) as handle:
        for entry in handle.infolist():
            name = entry.filename
            path = Path(name)
            expected_prefix = selected_kind.archive_prefix
            if "\\" in name or path.is_absolute() or not path.parts or ".." in path.parts:
                raise ValueError("bundle archive contains an unsafe or unexpected path")
            if expected_prefix is not None and path.parts[0] != expected_prefix.as_posix():
                raise ValueError("bundle archive contains an unsafe or unexpected path")
            if expected_prefix is None and path.parts[0] not in {"uifiles", AYA_LAYOUT_NAME}:
                raise ValueError("bundle archive contains an unsafe or unexpected path")
            normalized_name = Path(*path.parts).as_posix()
            folded_name = normalized_name.casefold()
            if folded_name in folded_names:
                raise ValueError("bundle archive contains duplicate paths")
            folded_names.add(folded_name)

            mode = entry.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("bundle archive contains a symbolic link")
            if entry.is_dir():
                continue
            if expected_prefix is not None and len(path.parts) == 1:
                raise ValueError("bundle archive contains a file at its root")
            if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                raise ValueError("bundle archive contains an executable file")

            relative = (
                Path(*path.parts[1:]).as_posix()
                if expected_prefix is not None
                else Path(*path.parts).as_posix()
            )
            archived_files[relative] = entry

        if set(archived_files) != set(expected_files):
            raise ValueError("bundle archive inventory differs from the source tree")

        for relative, entry in archived_files.items():
            with handle.open(entry) as archived:
                archive_digest = hashlib.file_digest(archived, "sha256").digest()
            with expected_files[relative].open("rb") as source:
                source_digest = hashlib.file_digest(source, "sha256").digest()
            if archive_digest != source_digest:
                raise ValueError("bundle archive content differs from the source tree")

    return len(archived_files)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the distributable EverQuest UI bundle")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--kind", choices=sorted(BUNDLE_KINDS))
    parser.add_argument("bundle", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        file_count = verify_bundle(args.bundle, args.manifest, args.kind)
        if args.archive is not None:
            archive_count = verify_archive(args.archive, args.bundle, args.kind)
            if archive_count != file_count:
                raise ValueError("bundle archive file count differs from the source tree")
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"verify-ui-bundle: {error}", file=sys.stderr)
        return 1
    archive_suffix = " and release archive" if args.archive is not None else ""
    print(
        f"Verified UI bundle{archive_suffix}: {file_count} files, "
        "no unexpected layouts or sidecars."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
