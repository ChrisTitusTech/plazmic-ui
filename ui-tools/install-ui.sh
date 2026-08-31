#!/bin/sh

set -eu

script_dir=$(CDPATH='' cd -P -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH='' cd -P -- "$script_dir/.." && pwd)
source_dir="$repo_dir/.plazmic-ui-workspace/skin"
game_dir=${EQ_LEGENDS_DIR:-}
skin_id=
dry_run=0
staging_dir=
backup_dir=
target_dir=

usage() {
  cat <<'EOF'
Usage: ui-tools/install-ui.sh [OPTIONS]

Options:
  --game-dir DIR   EverQuest Legends installation directory
  --source DIR     Materialized UI workspace directory
  --skin ID        Install plazmic-ui or aya (default: remembered selection)
  --dry-run        Validate and print the intended target without installing
  -h, --help       Show this help
EOF
}

cleanup() {
  status=$?
  trap - 0 HUP INT TERM

  if [ -n "$staging_dir" ] && [ -d "$staging_dir" ]; then
    rm -rf -- "$staging_dir"
  fi

  if [ "$status" -ne 0 ] &&
    [ -n "$backup_dir" ] &&
    [ -d "$backup_dir" ] &&
    [ -n "$target_dir" ] &&
    [ ! -e "$target_dir" ]; then
    mv -- "$backup_dir" "$target_dir"
  fi

  exit "$status"
}

trap cleanup 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

while [ "$#" -gt 0 ]; do
  case "$1" in
    --game-dir)
      [ "$#" -ge 2 ] || {
        printf '%s\n' '--game-dir requires a value.' >&2
        exit 2
      }
      game_dir=$2
      shift 2
      ;;
    --source)
      [ "$#" -ge 2 ] || {
        printf '%s\n' '--source requires a value.' >&2
        exit 2
      }
      source_dir=$2
      shift 2
      ;;
    --skin)
      [ "$#" -ge 2 ] || {
        printf '%s\n' '--skin requires a value.' >&2
        exit 2
      }
      skin_id=$2
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$game_dir" ]; then
  printf '%s\n' 'Set EQ_LEGENDS_DIR or pass --game-dir.' >&2
  exit 1
fi

uifiles_dir="$game_dir/uifiles"

if [ ! -f "$game_dir/eqgame.exe" ] || [ ! -d "$uifiles_dir/default_modern" ]; then
  printf '%s\n' 'EverQuest Legends UI installation was not found.' >&2
  exit 1
fi

for required_command in pgrep python3 realpath rsync; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'Required command is not installed: %s\n' "$required_command" >&2
    exit 1
  fi
done

if [ -z "$skin_id" ]; then
  config_path="$repo_dir/.plazmic-ui-workspace/studio.json"
  if [ -f "$config_path" ] && [ ! -L "$config_path" ]; then
    skin_id=$(
      python3 - "$config_path" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        value = json.load(handle)
except (OSError, ValueError):
    value = {}
print(value.get("active_skin", "") if isinstance(value, dict) else "")
PY
    )
  fi
fi
skin_id=${skin_id:-plazmic-ui}

case "$skin_id" in
  plazmic-ui)
    skin_directory=plazmic-ui
    skin_display='Plazmic UI'
    ;;
  aya)
    skin_directory=AYA_Legends
    skin_display='Aya Legends'
    ;;
  *)
    printf 'Invalid skin: %s (expected plazmic-ui or aya)\n' "$skin_id" >&2
    exit 2
    ;;
esac
target_dir="$uifiles_dir/$skin_directory"

if [ ! -f "$source_dir/EQUI.xml" ] || [ ! -f "$source_dir/.plazmic-upstream" ]; then
  printf '%s\n' 'The selected source is not a materialized UI workspace.' >&2
  exit 1
fi

recorded_skin=$(sed -n 's/^skin=//p' "$source_dir/.plazmic-upstream" | head -n 1)
recorded_source=$(sed -n 's/^source=//p' "$source_dir/.plazmic-upstream" | head -n 1)
if { [ "$skin_id" = aya ] && [ "$recorded_skin" != aya ] &&
  [ "$recorded_source" != AYA_Legends ]; } ||
  { [ -n "$recorded_skin" ] && [ "$recorded_skin" != "$skin_id" ]; }; then
  printf '%s\n' 'The workspace was captured for a different skin.' >&2
  exit 1
fi

source_canonical=$(realpath -e -- "$source_dir")
uifiles_canonical=$(realpath -e -- "$uifiles_dir")
case "$source_canonical" in
  "$uifiles_canonical" | "$uifiles_canonical"/*)
    printf '%s\n' 'An installed Daybreak skin cannot be used as the install source.' >&2
    exit 1
    ;;
esac

source_symlink=$(find "$source_dir" -type l -print -quit)
if [ -n "$source_symlink" ]; then
  printf '%s\n' 'The materialized UI contains a symlink.' >&2
  exit 1
fi

if [ -L "$target_dir" ] || { [ -e "$target_dir" ] && [ ! -d "$target_dir" ]; }; then
  printf '%s\n' 'The install target must be a physical directory when it exists.' >&2
  exit 1
fi

if [ "$skin_id" = aya ] || grep -q '^captured_at=' "$source_dir/.plazmic-upstream"; then
  python3 "$script_dir/lint-ui.py" \
    --profile generic \
    --inherited-include SIDL.xml \
    "$source_dir"
else
  python3 "$script_dir/lint-ui.py" --check-format "$source_dir"
fi

printf '%s\n' 'Materialized source and install target validated.'

if [ "$dry_run" -eq 1 ]; then
  printf '%s\n' 'Dry run complete; no files changed.'
  exit 0
fi

if pgrep -x eqgame.exe >/dev/null 2>&1; then
  printf '%s\n' 'eqgame.exe is running. Exit the game before installing the UI.' >&2
  exit 1
fi

staging_dir=$(mktemp -d "$uifiles_dir/.plazmic-ui.install.XXXXXX")

rsync \
  --archive \
  --exclude='.plazmic-upstream' \
  --exclude='*.crc' \
  --exclude='*:crc' \
  --exclude='*.bak' \
  "$source_dir/" \
  "$staging_dir/"

if [ -e "$target_dir" ]; then
  backup_dir="${target_dir}.backup-$(date +%Y%m%d-%H%M%S-%N)"
  if [ -e "$backup_dir" ]; then
    printf '%s\n' 'The generated backup location already exists.' >&2
    exit 1
  fi

  mv -- "$target_dir" "$backup_dir"
  printf '%s\n' 'Preserved the previous installation in a timestamped sibling backup.'
fi

mv -- "$staging_dir" "$target_dir"
staging_dir=

printf 'Installed %s.\n' "$skin_display"
printf 'Load it in game with: /loadskin %s 1\n' "$skin_directory"
