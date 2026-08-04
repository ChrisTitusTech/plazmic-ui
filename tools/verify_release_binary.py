from __future__ import annotations

import argparse
import stat
import subprocess
import sys
from pathlib import Path

MINIMUM_BINARY_SIZE = 1 * 1024 * 1024
MAXIMUM_BINARY_SIZE = 100 * 1024 * 1024
EXPECTED_MAGIC = {
    "linux": b"\x7fELF",
    "windows": b"MZ",
}


def physical_path(path: Path) -> Path:
    absolute = path.absolute()
    current = Path(absolute.parts[0])
    for part in absolute.parts[1:]:
        current /= part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or (
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise ValueError("release artifact path must not contain links or reparse points")
    return absolute


def verify_binary(path: Path, platform: str, version: str) -> None:
    path = physical_path(path)
    if not path.is_file():
        raise ValueError("release artifact must be a physical regular file")
    size = path.stat().st_size
    if not MINIMUM_BINARY_SIZE <= size <= MAXIMUM_BINARY_SIZE:
        raise ValueError(f"release artifact size is outside the approved range: {size} bytes")
    with path.open("rb") as handle:
        magic = handle.read(4)
    if not magic.startswith(EXPECTED_MAGIC[platform]):
        raise ValueError(f"release artifact is not a {platform} executable")

    expected_version = f"Plazmic UI Studio {version}"
    version_result = subprocess.run(
        [path.resolve(), "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if version_result.stdout.strip() != expected_version:
        raise ValueError("release artifact reported an unexpected version")

    diagnose_result = subprocess.run(
        [path.resolve(), "diagnose"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if diagnose_result.stdout.strip() != f"{expected_version}: frontend bundle is ready":
        raise ValueError("release artifact did not validate its bundled frontend")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify a packaged Plazmic UI Studio binary")
    parser.add_argument("--platform", choices=sorted(EXPECTED_MAGIC), required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("binary", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        verify_binary(args.binary, args.platform, args.version)
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError) as error:
        print(f"verify-release-binary: {error}", file=sys.stderr)
        return 1
    print(f"Verified {args.platform} Studio {args.version} release binary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
