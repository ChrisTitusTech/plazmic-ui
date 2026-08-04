#!/bin/sh

set -eu

script_dir=$(CDPATH='' cd -P -- "$(dirname -- "$0")" && pwd)

usage() {
  cat <<'EOF'
Usage: ui-tools/format-ui.sh UI_DIRECTORY

Normalize every top-level XML file without reserializing the EQ XML dialect.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -ne 1 ]; then
  usage >&2
  exit 2
fi

ui_dir=$1

if [ ! -d "$ui_dir" ]; then
  printf 'UI directory does not exist: %s\n' "$ui_dir" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'python3 is required.' >&2
  exit 1
fi

exec python3 "$script_dir/format_xml.py" --in-place "$ui_dir"
