#!/bin/sh

set -eu

script_dir=$(CDPATH='' cd -P -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH='' cd -P -- "$script_dir/.." && pwd)
destination="$repo_dir/.plazmic-ui-workspace/skin"
game_dir=${EQ_LEGENDS_DIR:-}
refresh=0
staging_dir=
backup_dir=

usage() {
  cat <<'EOF'
Usage: ui-tools/sync-ui.sh [OPTIONS]

Options:
  --game-dir DIR      EverQuest Legends installation directory
  --destination DIR   Materialized UI directory
  --refresh           Preserve the old destination as a timestamped backup
  -h, --help          Show this help
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
    [ ! -e "$destination" ]; then
    mv -- "$backup_dir" "$destination"
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
    --destination)
      [ "$#" -ge 2 ] || {
        printf '%s\n' '--destination requires a value.' >&2
        exit 2
      }
      destination=$2
      shift 2
      ;;
    --refresh)
      refresh=1
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

source_dir="$game_dir/uifiles/default_modern"

if [ ! -f "$game_dir/eqgame.exe" ]; then
  printf '%s\n' 'eqgame.exe was not found in the selected game directory.' >&2
  exit 1
fi

if [ ! -f "$source_dir/EQUI.xml" ]; then
  printf '%s\n' 'The installed default_modern skin was not found.' >&2
  exit 1
fi

source_symlink=$(find "$source_dir" -type l -print -quit)
if [ -n "$source_symlink" ]; then
  printf '%s\n' 'The installed default_modern skin contains a symlink.' >&2
  exit 1
fi

for required_command in realpath rsync python3; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'Required command is not installed: %s\n' "$required_command" >&2
    exit 1
  fi
done

source_canonical=$(realpath -e -- "$source_dir")
approved_destination="$repo_dir/.plazmic-ui-workspace/skin"
if [ "$destination" != "$approved_destination" ]; then
  printf '%s\n' 'Destination must be the repository private skin workspace.' >&2
  exit 1
fi
if [ -L "$repo_dir/.plazmic-ui-workspace" ] || [ -L "$destination" ]; then
  printf '%s\n' 'Private workspace components must not be symlinks.' >&2
  exit 1
fi
if [ -e "$repo_dir/.plazmic-ui-workspace" ] &&
  [ ! -d "$repo_dir/.plazmic-ui-workspace" ]; then
  printf '%s\n' 'The private workspace root must be a physical directory.' >&2
  exit 1
fi
if [ -e "$destination" ] && [ ! -d "$destination" ]; then
  printf '%s\n' 'The private skin workspace must be a physical directory.' >&2
  exit 1
fi
destination_canonical=$(realpath -m -- "$destination")
case "$destination_canonical" in
  "$source_canonical" | "$source_canonical"/*)
    printf '%s\n' 'Destination must not replace default_modern.' >&2
    exit 1
    ;;
esac
case "$source_canonical" in
  "$destination_canonical" | "$destination_canonical"/*)
    printf '%s\n' 'Destination must not contain default_modern.' >&2
    exit 1
    ;;
esac

destination_parent=$(dirname -- "$destination")
mkdir -p -- "$destination_parent"

if [ -e "$destination" ]; then
  if [ "$refresh" -ne 1 ]; then
    printf '%s\n' 'The private skin workspace already exists.' >&2
    printf '%s\n' 'Use --refresh to preserve it as a timestamped backup.' >&2
    exit 1
  fi

  backup_dir="${destination}.backup-$(date +%Y%m%d-%H%M%S-%N)"
  if [ -e "$backup_dir" ]; then
    printf '%s\n' 'The generated workspace backup location already exists.' >&2
    exit 1
  fi

  mv -- "$destination" "$backup_dir"
  printf '%s\n' 'Preserved the previous workspace in a timestamped sibling backup.'
fi

staging_dir=$(mktemp -d "${destination}.staging.XXXXXX")

rsync \
  --archive \
  --exclude='*.crc' \
  --exclude='*:crc' \
  --exclude='*.bak' \
  "$source_dir/" \
  "$staging_dir/"

python3 "$script_dir/apply-improvements.py" "$staging_dir"
"$script_dir/format-ui.sh" "$staging_dir"
python3 "$script_dir/lint-ui.py" --check-format "$staging_dir"

cat >"$staging_dir/.plazmic-upstream" <<EOF
source=default_modern
synced_at=$(date --iso-8601=seconds)
EOF

mv -- "$staging_dir" "$destination"
staging_dir=

printf '%s\n' 'Materialized Plazmic UI in the private repository workspace.'
if [ -n "$backup_dir" ]; then
  printf '%s\n' 'Previous workspace backup retained as a timestamped sibling.'
fi
