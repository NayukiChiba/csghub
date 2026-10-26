#!/bin/sh

set -eu

api_url='http://127.0.0.1/api/v1/datasets?page=1&page_size=1'
timeout_seconds=${CSGHUB_API_READY_TIMEOUT_SECONDS:-900}
started_at=$(date +%s)
consecutive_successes=0

while [ "$consecutive_successes" -lt 3 ]; do
  if curl -fsS --max-time 15 "$api_url" >/dev/null 2>&1; then
    consecutive_successes=$((consecutive_successes + 1))
    sleep 1
    continue
  fi

  consecutive_successes=0
  now=$(date +%s)
  if [ $((now - started_at)) -ge "$timeout_seconds" ]; then
    echo "CSGHub API did not become ready within ${timeout_seconds}s." >&2
    exit 1
  fi
  sleep 2
done

echo "CSGHub API is ready."
