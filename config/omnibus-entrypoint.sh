#!/bin/bash
set -euo pipefail
mkdir -p /opt/csghub/service
/opt/csghub/embedded/bin/runsvdir-start &
supervisor_pid=$!
cleanup() {
  kill -TERM "$supervisor_pid" 2>/dev/null || true
  wait "$supervisor_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
for pass in 1 2; do
  success=false
  for attempt in 1 2 3; do
    if /usr/bin/csghub-ctl reconfigure; then
      success=true
      break
    fi
    sleep 5
  done
  if [ "$success" != true ]; then
    echo 'CSGHub configuration failed' >&2
    exit 1
  fi
done
wait "$supervisor_pid"
