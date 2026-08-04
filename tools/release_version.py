from __future__ import annotations

import argparse
import importlib.util
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO_SOURCE = ROOT / "ui-tools" / "ui_studio.py"


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
            raise ValueError("GitHub output path must not contain links or reparse points")
    return absolute


def studio_version() -> str:
    spec = importlib.util.spec_from_file_location("plazmic_ui_release", STUDIO_SOURCE)
    if spec is None or spec.loader is None:
        raise ValueError("could not load the Studio version")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    version = getattr(module, "VERSION", "")
    parts = str(version).split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("Studio version must use MAJOR.MINOR.PATCH")
    return str(version)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read and validate the Studio release version")
    parser.add_argument("--check-tag", action="store_true")
    parser.add_argument("--github-output", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        version = studio_version()
        if args.check_tag and os.environ.get("GITHUB_REF_TYPE") == "tag":
            expected_tag = f"v{version}"
            if os.environ.get("GITHUB_REF_NAME") != expected_tag:
                raise ValueError(f"release tag must match Studio version {expected_tag}")
        if args.github_output:
            output_path = os.environ.get("GITHUB_OUTPUT")
            if not output_path:
                raise ValueError("GITHUB_OUTPUT is not set")
            with physical_path(Path(output_path)).open("a", encoding="utf-8") as handle:
                handle.write(f"version={version}\n")
        else:
            print(version)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"release-version: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
