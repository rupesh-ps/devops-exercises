#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 copy|sync SOURCE DEST [--dry-run|--apply]" >&2
  exit 2
fi
mode=$1; source_path=$2; destination=$3; option=${4:-}
case "$mode" in copy|sync) ;; *) exit 2 ;; esac
case "$option" in ''|--dry-run) ;; --apply) [[ "$mode" == sync ]] || exit 2 ;; *) exit 2 ;; esac
[[ -n "$source_path" && -n "$destination" && "$source_path" != "$destination" && "$destination" != / ]] || exit 2

umask 077
log_dir="$(cd "$(dirname "$0")" && pwd)/logs"
mkdir -p "$log_dir"
args=(--config /dev/null --progress --stats 2s --retries 3 --log-level INFO --log-file "$log_dir/transfer.log")
if [[ "$option" == --dry-run || ( "$mode" == sync && "$option" != --apply ) ]]; then
  args+=(--dry-run)
fi

printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$mode" >> "$log_dir/transfer.log"
if rclone "$mode" "$source_path" "$destination" "${args[@]}"; then
  echo 'Transfer completed. Log: logs/transfer.log'
else
  status=$?
  echo "Transfer failed with exit code $status. See logs/transfer.log" >&2
  exit "$status"
fi
