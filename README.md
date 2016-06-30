OAuth Server - An OAuth Provider Project
========================================

[![Build Status](https://travis-ci.org/TransparentHealth/hhs_oauth_server.svg?branch=develop)](https://travis-ci.org/TransparentHealth/hhs_oauth_server)

The project is based in Python 3 and Django 1.9.5.

It consists of an OAuth2 server and a FHIR server that serves specific resources.
This application will handle the OAuth 2 handshaking and configuration with CMS Medicare
beneficiaries and Registered Developers.

The prototype application will be served from an AWS instance (https://dev.bbonfhir.com).

Quick Setup
-----------

These instructions provide a quick start for developers new to the project.
Follow these steps on the command line.

    # prepare your repository folder
    git clone https://github.com/transparenthealth.org/hhs_oauth_server.git
    cd hhs_oauth_server

    # create the virtualenv
    mkvirtualenv oauth_server --python=/path/to/python3-binary

    # install the requirements
    pip install -r requirements/requirements.txt

    # prepare Django settings
    cp hhs_oauth_server/settings/local_example.py hhs_oauth_server/settings/local.py
    
Note that you will need to add valid AWS keys setup to use Simple Email Service (SES) in your local.py. If you do not,
the email functions will not work.  anything defined in local.py overrides items in base.py.  


    #Setup the database
    python manage.py migrate
    python manage.py loaddata apps/accounts/fixtures/BlueButtonGroup.json
    

    #Run the development server
    python manage.py runserver

Note you can find the path to your Python3 binary by typing `which python3`.

Running Tests
-------------

Simply:

    python runtests.py

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
