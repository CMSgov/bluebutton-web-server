OAuth Server - An OAuth Provider Project
========================================
The project is based in Python 3 and Django 1.9.5.

It consists of an OAuth2 server and a FHIR server that serves specific 
resources. This application will handle the OAuth 2 handshaking and 
configuration with CMS Medicare beneficiaries and Registered Developers.

The prototype application will be served from an AWS instance 
(https://dev.bbonfhir.com).
   


Quick Setup
-----------

These instructions provide a quick start for developers new to the project.
Follow these steps on the command line.

    unset DJANGO_SETTINGS_MODULE
    git clone https://github.com/transparenthealth.org/hhs_oauth_server.git
    cd hhs_oauth_server
    mkvirtualenv oauth_server --python=/path/to/python3-binary
    pip install -r requirements/requirements.txt
    python manage.py migrate
    python manage.py loaddata apps/accounts/fixtures/BlueButtonGroup.json
    python manage.py createsuperuser
    python manage.py runserver
    
    
Notes: 
    - You can find the path to your Python3 binary by typing `which python3`.
    - If you do not have virtualenv installed you can use pyvenv for python3.

Getting your Django Settings squared away
-------------------------------------------

Add this to `~/.bash_profile`  in macOS/OSX or `~/.bashrc` in Linux using 
your favorite text editor.


   export DJANGO_SETTINGS_MODULE='_start.settings.base'

Now activate the changes.

   source ~/.bash_profile

--or--

    source ~/.bashrc

Note that if you skip the previous step you will need to add 
`--settings=_start.settings.base` to any management command.

The launch script, manage.py, is configured to use "_start.settings.base" if
DJANGO_SETTINGS_MODULE is not set. If you override base.py by creating your
own custom settings use the example file: `_start/settings/examples/local.py`.
Copy the file to `_start/settings` and update DJANGO_SETTINGS_MODULE with the
command:

    export DJANGO_SETTINGS_MODULE=_start.settings.local
    
Settings are inside the the folder `_start/settings/`.  `local.py` extends 
`base.py`. Use `test.py` to test production and `test_local`to test locally in
a development environment.  Included in `_start/settings/` you will find a 
folder called `examples` that can help you get started with your own `local.py` 
file.

Passwords and other environment-dependent settings shall NOT be stored in the 
base settings file `base.py`. Instead security and environment settings 
should be set in `_start/settings/local.py`. Anything added to local.py will 
override the base settings.

Running Tests
-------------

To run test first load test data into your environment

    python manage.py load_test_data

And then run:

    python manage.py test

Requirements
------------

To manage requirements we use [pip-tools][0] package.

[0]: https://github.com/nvie/pip-tools

### Installation

You can install `pip-tools` with:

    pip install --upgrade pip  # pip-tools need pip>=6.1
    pip install pip-tools

### Usage

To add/update/remove requirements **always** change the 
`requirements/requirements.in` file. Then run:

    cd requirements/
    pip-compile requirements.in

This will produce a new `requirements.txt` with all dependencies pinned.
