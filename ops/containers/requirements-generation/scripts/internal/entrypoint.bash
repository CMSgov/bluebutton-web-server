#!/usr/bin/env bash

PATH="/venv/bin:$PATH"

echo Generating requirements.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.txt \
    /code/requirements/requirements.in
if [ "$?" -ne 0 ]; then
    echo "pip-compile prod requirements failed."
    exit
fi

echo Generating requirements.dev.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.dev.txt \
    /code/requirements/requirements.dev.in
if [ "$?" -ne 0 ]; then
    echo "pip-compile dev requirements failed."
    exit
fi