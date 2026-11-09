"""The purpose of this script is to pull in files from the insights/etls directory, encode them, and post them
to the its-log API. This aids in testing the its-log API locally, by programmatically creating the ETLs and bb sequence
rather than needing to do it manually.

If you add a new ETL for its-log, add the file in the etls directory. If you want the file to be ignored and not posted in this
script, prefix the file with an underscore.

Must run the script from the project root and set the ITS_LOG_API_KEY value in your terminal before running.
"""

import base64
import os
from pathlib import Path

import requests

ETL_FILE_EXTENSIONS = ['.star', '.sql', '.go']
ETL_FILE_DIR = 'insights/etls'
ETL_CREATION_ENDPOINT = 'http://localhost:8888/v1/etl/create'
SEQUENCE_CREATION_ENDPOINT = 'http://localhost:8888/v1/sequence/create'
ETL_DIRECTORY = Path('insights/etls')
# Can't use settings in this script so retrieve via getenv
API_KEY = os.getenv('ITS_LOG_API_KEY')


def encode_file(file_path: Path) -> str:
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    encoded_file = base64.b64encode(file_bytes).decode('ascii')
    return encoded_file


def post_etl_to_its_log(etl_name: str, file_extension: str, encoded_file: str) -> None:
    if file_extension == 'star':
        file_extension = 'starlark'
    payload = {
        'name': etl_name,
        'kind': file_extension,
        'body': encoded_file,
        'date': 'today',
    }

    response = requests.post(ETL_CREATION_ENDPOINT, headers={'x-api-key': API_KEY}, json=payload, timeout=5)
    print(f'response status code: {response.status_code}')


def main():
    files = [
        f for f in ETL_DIRECTORY.iterdir() if f.is_file() and (not f.name.startswith('_') or f.name == 'README.md')
    ]
    file_names_list = []

    for file in files:
        print(f'file: {file.name}')
        encoded_file = encode_file(file)
        etl_name = file.stem
        file_extension = file.suffix.replace('.', '')
        post_etl_to_its_log(etl_name, file_extension, encoded_file)
        file_names_list.append({'name': etl_name})

    sequence_payload = {
        'name': 'bb',
        'kind': 'sequence',
        'body': file_names_list,
        'date': 'today',
    }
    sequence_response = requests.post(
        SEQUENCE_CREATION_ENDPOINT, headers={'x-api-key': API_KEY}, json=sequence_payload, timeout=5
    )
    print(f'sequence creation status code: {sequence_response.status_code}')


if __name__ == '__main__':
    main()
