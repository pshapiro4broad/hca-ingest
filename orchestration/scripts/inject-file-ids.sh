set -euo pipefail

# Staged rows have: {file_type}_id, version, crc32c, content, source_file_id, source_file_version, data_file_name
# Output rows need: {file_type}_id, version, file_id, source_file_id, source_file_version, content
# Run the transformation by joining on the datarepo_load_history table, via crc32c

declare -r TARGET_TABLE=${TABLE}_with_ids

declare -ra BQ_QUERY=(
  bq
  --location=US
  --project_id=${STAGING_PROJECT}
  --synchronous_mode=true
  --headless=true
  --format=none
  query
  --use_legacy_sql=false
  --replace=true
  --external_table_definition=${TABLE}::${TABLE}_id:STRING,version:TIMESTAMP,crc32c:STRING,content:STRING,source_file_id:STRING,source_file_version:TIMESTAMP,data_file_name:STRING@NEWLINE_DELIMITED_JSON=${GCS_PREFIX}/*
  --destination_table=${STAGING_PROJECT}:${STAGING_DATASET}.${TARGET_TABLE}
)
1>&2 ${BQ_QUERY[@]} "SELECT S.${TABLE}_id, S.version, J.file_id, S.source_file_id, S.source_file_version, S.content
  FROM ${TABLE} S LEFT JOIN \`${JADE_PROJECT}.${JADE_DATASET}.datarepo_load_history\` J
  ON S.crc32c = J.checksum_crc32c"

# Echo the output table name to Argo can slurp it into a parameter.
echo ${TARGET_TABLE}