#!/usr/bin/env bash

python --version
echo $PYTHON_VERSION

echo Generating requriements.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.txt \
    /requirements/requirements.in

echo Starting requirements.txt download
pip download -r /output/requirements.txt \
    --dest /vendor \
    --platform manylinux2014_x86_64 \
    --abi cp311 \
    --no-deps
echo Done with requirements.txt download

echo Generating requirements.dev.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.dev.txt \
    /requirements/requirements.dev.in

echo Starting requirements.dev.txt download
pip download -r /output/requirements.dev.txt \
    --dest /vendor \
    --platform manylinux2014_x86_64 \
    --abi cp311 \
    --no-deps
echo Done with requirements.dev.txt download
