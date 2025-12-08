#!/usr/bin/env bash

python --version
echo $PYTHON_VERSION

pip-compile --generate-hashes --output-file=/output/requirements.txt /requirements/requirements.in
pip-compile --generate-hashes --output-file=/output/requirements.dev.txt /requirements/requirements.dev.in
