"""The purpose of this script is to pull in files from the insights/etls directory, encode them, and post them
to the its-log API. This aids in testing the its-log API locally, by programmatically creating the ETLs and bb sequence
rather than needing to do it manually.

If you add a new ETL for its-log, add the file in the etls directory. Then, add the file path to the files list in the main
function below. If you want the ETL added to the bb sequence, you'll also need to modify the sequence_payload.
"""

import base64
import logging

import requests

logger = logging.getLogger('etl_creation_script')

ETL_FILE_EXTENSIONS = ['.star', '.sql', '.go']
ETL_FILE_DIR = 'insights/etls'
ETL_CREATION_ENDPOINT = 'http://localhost:8888/v1/etl/create'
SEQUENCE_CREATION_ENDPOINT = 'http://localhost:8888/v1/sequence/create'
# Note: This is a dummy API key for local development
API_KEY = 'abcdefghabcdefghabcdefghabcdefghabcdefghabcdefghabcdefghabcdefgh'


def encode_file(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    encoded_file = base64.b64encode(file_bytes).decode('ascii')
    return encoded_file


def post_etl_to_its_log(etl_name: str, file_extension: str, encoded_file: str) -> None:
    print('file extension: ', file_extension)
    if file_extension == 'go':
        file_extension = 'golang'
    elif file_extension == 'star':
        file_extension = 'starlark'
    payload = {
        'name': etl_name,
        'kind': file_extension,
        'body': encoded_file,
        'date': 'today',
    }

    response = requests.post(ETL_CREATION_ENDPOINT, headers={'x-api-key': API_KEY}, json=payload, timeout=5)
    logger.info(f'response status code: {response.status_code}')


def main():
    files = [
        'insights/etls/app-summary.star',
        'insights/etls/remove-outdated-summaries.sql',
        'insights/etls/global-metrics.star',
        'insights/etls/db-to-csv.go',
    ]
    for file in files:
        logger.info(f'file: {file}')
        encoded_file = encode_file(file)
        etl_name = file.split('/')[2]
        file_extension = etl_name.split('.')[1]
        etl_name = etl_name.split('.')[0]
        post_etl_to_its_log(etl_name, file_extension, encoded_file)

    sequence_payload = {
        'name': 'bb',
        'kind': 'sequence',
        'body': [
            {'name': 'app-summary'},
            {'name': 'global-metrics'},
            {'name': 'remove-outdated-summaries'},
            {'name': 'db-to-csv'},
        ],
        'date': 'today',
    }
    sequence_response = requests.post(
        SEQUENCE_CREATION_ENDPOINT, headers={'x-api-key': API_KEY}, json=sequence_payload, timeout=5
    )
    logger.info(f'sequence creation status code: {sequence_response.status_code}')


if __name__ == '__main__':
    main()
