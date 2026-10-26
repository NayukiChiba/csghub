#!/bin/sh

set -eu

public_url="${CSGHUB_PORTAL_STARHUB_PUBLIC_BASE_URL:-}"
if [ -z "$public_url" ]; then
  exit 0
fi

env_dir=/opt/csghub/service/portal/env
while ! pgrep -x csghub-portal >/dev/null 2>&1; do
  sleep 2
done

printf '%s' "$public_url" > "$env_dir/CSGHUB_PORTAL_STARHUB_PUBLIC_BASE_URL"
csghub-ctl restart portal
