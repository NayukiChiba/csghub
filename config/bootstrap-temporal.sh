#!/bin/sh

set -eu

temporal_cli=/opt/csghub/embedded/bin/temporal
temporal_address=127.0.0.1:7233

until [ -x "$temporal_cli" ]; do
  sleep 1
done

until "$temporal_cli" --address "$temporal_address" operator cluster health 2>/dev/null | grep -q SERVING; do
  sleep 1
done

if ! "$temporal_cli" --address "$temporal_address" operator namespace describe --namespace default >/dev/null 2>&1; then
  "$temporal_cli" --address "$temporal_address" operator namespace create \
    --namespace default \
    --retention 7d \
    --description "Default namespace for Temporal Server."
fi

until "$temporal_cli" --address "$temporal_address" operator search-attribute list --namespace default >/dev/null 2>&1; do
  sleep 1
done

ensure_search_attribute() {
  name=$1
  type=$2
  if ! "$temporal_cli" --address "$temporal_address" operator search-attribute list --namespace default | grep -q "$name"; then
    "$temporal_cli" --address "$temporal_address" operator search-attribute create \
      --namespace default \
      --name "$name" \
      --type "$type"
  fi
}

ensure_search_attribute CustomKeywordField Keyword
ensure_search_attribute CustomStringField Text
ensure_search_attribute CustomTextField Text
ensure_search_attribute CustomIntField Int
ensure_search_attribute CustomDatetimeField Datetime
ensure_search_attribute CustomDoubleField Double
ensure_search_attribute CustomBoolField Bool

# The v2.6.0 migration targets a database named "casdoor", while Omnibus
# creates "csghub_casdoor". Correct the FDW and rerun the idempotent sync.
psql=/opt/csghub/embedded/bin/psql
server_database=csghub_server
role_sync_script=/opt/csghub/service/server/scripts/1789619535_server_sync_role_mask_admin.sql

until "$psql" -U csghub -d "$server_database" -Atc \
  "select 1 from pg_foreign_server where srvname = 'csghub_casdoor_fdw'" 2>/dev/null | grep -q 1; do
  sleep 1
done

"$psql" -U csghub -v ON_ERROR_STOP=1 -d "$server_database" \
  -c "ALTER SERVER csghub_casdoor_fdw OPTIONS (SET dbname 'csghub_casdoor')"

if [ -f "$role_sync_script" ]; then
  "$psql" -U csghub -v ON_ERROR_STOP=1 -d "$server_database" -f "$role_sync_script"
fi

# The bundled setup loop keeps retrying localhost through IPv6. Its work is
# complete here, so stop that orphaned bootstrap process and its noisy retries.
if command -v pkill >/dev/null 2>&1; then
  pkill -f /opt/csghub/embedded/etc/temporal/setup.sh || true
fi

echo "Temporal namespace bootstrap completed."
