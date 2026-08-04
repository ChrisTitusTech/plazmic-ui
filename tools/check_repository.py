#!/usr/bin/env python3

from __future__ import annotations

import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOTS = {
    ".plazmic-ui-workspace",
    ".plazmic-ui-studio.json",
    "captures",
    "logs",
    "plazmic-ui.backup",
    "ui-backups",
    "ui-layouts",
}
FORBIDDEN_SUFFIXES = {
    ".bak",
    ".bmp",
    ".crc",
    ".dds",
    ".dll",
    ".dmp",
    ".eqg",
    ".exe",
    ".ini",
    ".mp3",
    ".s3d",
    ".tga",
    ".wav",
    ".xml",
}
ALLOWED_EXECUTABLES = {
    Path("plazmic-ui"),
    Path("ui-tools/apply-improvements.py"),
    Path("ui-tools/format-ui.sh"),
    Path("ui-tools/format_xml.py"),
    Path("ui-tools/install-ui.sh"),
    Path("ui-tools/lint-ui.py"),
    Path("ui-tools/plazmic-ui"),
    Path("ui-tools/sync-ui.sh"),
}
SENSITIVE_PATTERNS = {
    "absolute home path": re.compile(rb"/home/[A-Za-z0-9._-]+/"),
    "Wine user path": re.compile(rb"drive_c/users/[A-Za-z0-9._-]+", re.IGNORECASE),
    "GitHub token": re.compile(rb"(?:gh[opsur]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
MAX_PUBLIC_FILE_SIZE = 2 * 1024 * 1024


def candidate_paths() -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [Path(item.decode("utf-8")) for item in result.stdout.split(b"\0") if item]


def private_path(path: Path) -> bool:
    first = path.parts[0]
    return (
        first in PRIVATE_ROOTS
        or (first == "plazmic-ui" and len(path.parts) > 1)
        or first.startswith("plazmic-ui.backup-")
        or first.startswith(".plazmic-ui.capture.")
    )


def inspect_path(relative: Path) -> list[str]:
    findings: list[str] = []
    path = ROOT / relative
    if private_path(relative):
        findings.append("private workspace path is public")
        return findings
    if path.is_symlink():
        findings.append("symbolic links are not allowed")
        return findings
    if not path.is_file():
        findings.append("repository entry is not a regular file")
        return findings
    if path.name.endswith(":crc") or path.suffix.lower() in FORBIDDEN_SUFFIXES:
        findings.append("game, backup, checksum, or private file type is not allowed")
    size = path.stat().st_size
    if size > MAX_PUBLIC_FILE_SIZE:
        findings.append(f"file exceeds {MAX_PUBLIC_FILE_SIZE} bytes")
    executable = bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    if executable and relative not in ALLOWED_EXECUTABLES:
        findings.append("unexpected executable bit")
    if relative in ALLOWED_EXECUTABLES and not executable:
        findings.append("required executable bit is missing")
    if size <= MAX_PUBLIC_FILE_SIZE:
        contents = path.read_bytes()
        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(contents):
                findings.append(f"possible {label}")
    return findings


def main() -> int:
    try:
        paths = candidate_paths()
    except (OSError, subprocess.CalledProcessError, UnicodeError) as error:
        print(f"repository-check: {error}", file=sys.stderr)
        return 1

    findings = [
        f"repository entry {index}: {message}"
        for index, path in enumerate(paths, start=1)
        for message in inspect_path(path)
    ]
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print(f"Repository hygiene passed: {len(paths)} public files inspected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
