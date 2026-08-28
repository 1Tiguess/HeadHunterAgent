#!/usr/bin/env bash
# Install the skills authored by headhunt runs into your user-level Claude config,
# so they load in every project rather than only inside this repo.
#
#   bash install-skills.sh --dry-run     # show what would happen, change nothing
#   bash install-skills.sh               # install, skipping any name that already exists
#   bash install-skills.sh --force       # overwrite existing skills of the same name
#   bash install-skills.sh app-interface-design cli-ergonomics   # install only these
#
# These are outputs of the protocol, not part of the gate. Installing them does not
# install HeadHunter itself — see install.sh for that.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/authored-skills"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"

DRY=0
FORCE=0
WANTED=()

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --force)   FORCE=1 ;;
    -h|--help) sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*)        printf 'unknown option: %s\n' "$arg" >&2; exit 2 ;;
    *)         WANTED+=("$arg") ;;
  esac
done

[[ -d "$SRC" ]] || { printf 'no authored-skills/ directory at %s\n' "$SRC" >&2; exit 4; }

installed=0
skipped=0
overwritten=0

for path in "$SRC"/*/; do
  name="$(basename "$path")"

  if [[ ${#WANTED[@]} -gt 0 ]]; then
    match=0
    for w in "${WANTED[@]}"; do [[ "$w" == "$name" ]] && match=1; done
    [[ $match -eq 1 ]] || continue
  fi

  target="$DEST/$name"

  if [[ -e "$target" && $FORCE -eq 0 ]]; then
    printf '  skip      %-26s (already exists; --force to overwrite)\n' "$name"
    skipped=$((skipped + 1))
    continue
  fi

  if [[ -e "$target" ]]; then
    action="overwrite"
    overwritten=$((overwritten + 1))
  else
    action="install"
    installed=$((installed + 1))
  fi

  if [[ $DRY -eq 1 ]]; then
    printf '  %-9s %-26s -> %s\n' "would $action" "$name" "$target"
  else
    mkdir -p "$DEST"
    rm -rf "$target"
    cp -R "$path" "$target"
    printf '  %-9s %-26s -> %s\n' "$action" "$name" "$target"
  fi
done

printf '\n'
if [[ $DRY -eq 1 ]]; then
  printf 'dry run: %d to install, %d to overwrite, %d skipped. Nothing was changed.\n' \
    "$installed" "$overwritten" "$skipped"
else
  printf '%d installed, %d overwritten, %d skipped.\n' "$installed" "$overwritten" "$skipped"
  printf 'Skills load from %s in every project.\n' "$DEST"
fi

# 0 = something happened, 1 = nothing to do, 2 = usage error.
if [[ $((installed + overwritten)) -eq 0 ]]; then exit 1; fi
