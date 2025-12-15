#!/usr/bin/env bash

python --version
echo $PYTHON_VERSION

echo Generating requriements.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.txt \
    /requirements/requirements.in

echo Starting download
pip download -r /output/requirements.txt \
    --dest /vendor \
    --platform manylinux2014_x86_64 \
    --abi cp311 \
    --no-deps
echo Done with download

echo Generating requirements.dev.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.dev.txt \
    /requirements/requirements.dev.in

