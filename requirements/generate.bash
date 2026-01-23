#!/usr/bin/env bash

python --version
echo $PYTHON_VERSION

echo Generating requriements.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.txt \
    /requirements/requirements.in
if [ "$?" -ne 0 ]; then
    echo "pip-compile prod requirements failed."
    exit
fi

echo Generating requirements.dev.txt
pip-compile --generate-hashes \
    --output-file=/output/requirements.dev.txt \
    /requirements/requirements.dev.in
if [ "$?" -ne 0 ]; then
    echo "pip-compile dev requirements failed."
    exit
fi