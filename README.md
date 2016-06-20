OAuth Server - An OAuth Provider Project
========================================

The project is based in Python 3 and Django 1.9.5.

It consists of an OAuth2 server and a FHIR server that serves specific resources.
This application will handle the OAuth 2 handshaking and configuration with CMS Medicare
beneficiaries and Registered Developers.

The prototype application will be served from an AWS instance (https://dev.bbonfhir.com).

Quick Setup
-----------

These instructions provide a quick start for developers new to the project.
Follow these steps on the command line.

    git clone https://github.com/transparenthealth.org/hhs_oauth_server.git
    cd hhs_oauth_server
    mkvirtualenv oauth_server --python=/path/to/python3-binary
    pip install -r requirements/requirements.txt
    python manage.py migrate
    python manage.py loaddata apps/accounts/fixtures/BlueButtonGroup.json
    python manage.py runserver

Note you can find the path to your Python3 binary by typing `which python3`.

Running Tests
-------------

To run test first load test data into your environment

    python manage.py load_test_data

And then run:

    python manage.py test

Requirements
------------

To manage requirements we use [pip-tools][0] package.

### Installation

You can install `pip-tools` with:

    pip install --upgrade pip==8.1.1  # pip-tools needs pip>=6.1 and pip<=8.1.1
    pip install pip-tools

### Usage

To add/update/remove requirements **always** change the `requirements/requirements.in`
file. Then run:

    cd requirements/
    pip-compile --output-file requirements.txt requirements.in

This will produce a new `requirements.txt` with all pinned dependencies.

[0]: https://github.com/nvie/pip-tools
