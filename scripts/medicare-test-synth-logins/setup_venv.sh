#!/usr/bin/bash
#
# Script to create a venv
#
PYTHON_VERSION=3.7

echo "- Removing /tmp/venv_python"
rm -rf /tmp/venv_python

echo "- Creating virtualenv for Python ${PYTHON_VERSION}"
python${PYTHON_VERSION} -m venv /tmp/venv_python

echo "- Sourcing /tmp/venv_python/bin"
source /tmp/venv_python/bin/activate

echo "- Installing Selenium"
pip install selenium
