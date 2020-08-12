import google.auth
from google.cloud import bigquery
import re
import sys

# TODO use ENV vars instead
# take contextual information as arguments
project_id = sys.argv[1]
dataset_name = sys.argv[2]
load_tag = sys.argv[3]

# Set up BigQuery client
credentials, project = google.auth.default(scopes=['openid', 'email', 'profile'])
bqclient = bigquery.Client(credentials=credentials, project=project_id,)


# log a checksum error for the given source and target path
def log_checksum_error(source_path: str, target_path: str):
    filename = re.search(r'([^/]*)$', source_path).group(1)
    error_log = {
        "errorType": "ChecksumError",
        "filePath": source_path,
        "fileName": filename,
        "message": f"Checksums do not match for the file ingested to ${target_path}."
    }
    log_file = open("../../logs/errors.log", "w")
    log_file.writelines(error_log)
    log_file.close()


# Validate the checksums for a single file ingested into the jade repo.
# Log an error if the checksums do not match.
def validate_checksum(load_history_row):
    target_path = load_history_row["target_path"]
    jade_checksum = load_history_row["checksum_crc32c"]

    # check that the original checksum matches the new one
    original_checksum = re.search(r'([^/]*)$', target_path).group(1)
    if not (original_checksum == jade_checksum):
        log_checksum_error(load_history_row["source_path"], target_path)


# Query the BQ API for summary information about each successful file load.
sql_query = f"""
SELECT source_name, target_path, checksum_crc32c
FROM `{project_id}.{dataset_name}.datarepo_load_history`
WHERE state='succeeded'
AND load_tag='{load_tag}'
LIMIT 10
    """
query_job = bqclient.query(sql_query)
for result_row in query_job:
    validate_checksum(result_row)

# TODO test helper functions with fake data