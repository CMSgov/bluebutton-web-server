OAuth Server - An OAuth Provider Project
========================================

[![Build Status](https://travis-ci.org/TransparentHealth/hhs_oauth_server.svg?branch=develop)](https://travis-ci.org/TransparentHealth/hhs_oauth_server)

The project is based in Python 3 and Django 1.9.5. It will operate on Python 2.7, 3.4, and 3.5.

It consists of an OAuth2 server and a FHIR server that serves specific resources.
This application will handle the OAuth 2 handshaking and configuration with CMS Medicare
beneficiaries and Registered Developers.

The prototype application will be served from an AWS instance (https://cms.oauth2.io).
The service will be known as the CMS Blue Button API.

Quick Setup
-----------

These instructions provide a quick start for developers new to the project.
Follow these steps on the command line.

    # prepare your repository folder
    git clone https://github.com/transparenthealth/hhs_oauth_server.git
    cd hhs_oauth_server

    # create the virtualenv
    mkvirtualenv oauth_server --python=/path/to/python3-binary

    # Install any pre-requisites  (C headers, etc. This is OS specific)
    # Ubuntu example
    sudo apt-get install python3-dev libxml2-dev libxslt1-dev
    

    # install the requirements
    pip install -r requirements/requirements.txt

    # prepare Django settings
    cp hhs_oauth_server/settings/local_sample.txt hhs_oauth_server/settings/local.py
    
Note that you will need to add valid AWS keys setup to use Simple Email Service (SES) in your
local.py. If you do not, the email functions will not work.  anything defined in local.py overrides
items in base.py.  


    #Setup the database
    python manage.py migrate
    python manage.py loaddata apps/accounts/fixtures/scopes_and_groups.json
    python manage.py createsuperuser
    

Making calls to a back-end FHIR server requires that you set a series of 
variables before running tests or the server itself.


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


Connecting to a FHIR Server
---------------------------

This server is designed to act as a front-end to any FHIR Server. In order
to use the FHIR functionality there are three steps:

    1. Define the settings to access the FHIR Server of your choice and set 
    them up as environment variables.
    
    2. Go to the Django Admin and Setup the FHIR Resources you want to 
    publish in the Server app in the table Supported Resource Types. For each
    resource determine which access modes you want to support.
    
    3. Go to the BlueButton section in the Admin and add the Resource Type 
    Control records to match each FHIR Resource Type entered in step 2. The
    Resource Type Control determines how the API is adapted to prevent user
    access. An example is the "Search Add" field. Enter "Patient=%PATIENT%" 
    here to force the Patient ID to be added to every search.
    
  
## 1. Define Environment Variables

You can add these to an executable shell script. The variables to define
are:

    THS_FHIR_SERVER
    THS_FHIR_PATH
    THS_FHIR_RELEASE
    THS_FHIR_REWRITE_FROM
    THS_FHIR_REWRITE_TO
    
Here is an example using a public FHIR Server:

    http://fhirtest.uhn.ca/baseDstu2
    
This would be entered on a linux server as:
    
    export THS_FHIR_SERVER="http://fhirtest.uhn.ca"
    export THS_FHIR_PATH=""
    export THS_FHIR_RELEASE="/baseDstu2"
    export THS_REWRITE_FROM="['$THS_FHIR_SERVER$THS_FHIR_PATH$THS_FHIR_RELEASE',]
    export THS_FHIR_REWRITE_TO="http://localhost:8000/bluebutton/fhir/v1"
     
NOTE: THS_REWRITE_FROM must be expressed as a list inside the quotes. 
NOTE: THS_REWRITE_TO is the address of the server, with path, that you are 
using. For a local default install this is example shown is correct.

## 2. Supported Resource Types

Login as an administrator and using Django Admin enter the FHIR Resources that
you want to make available through this platform. eg. Patient.

For each record you can specify the FHIR transactions you want to enable. 
eg. search, read, vread, _history

NOTE: Capitalization is important when referencing FHIR resources.

## 3. Resource Type Controls

Login as administrator and using Django Admin enter the Resource Type Controls
you want to apply. These records should match the Resources you created in 
step 2. eg. Patient.

The Control record defines the overrides that are made for a standard FHIR 
transaction. For example: 
- To always change the ID in the URL to the User's own ID set the 
  "override url id" flag.
- To prevent search from exposing another person's data set the "override
  search' flag.
- In the "search block" field enter the parameters to remove.
- in the "search add" field enter "Patient=%PATIENT%" to always apply
  a filter using the user's Patient ID.

NOTE: Capitalization is important when referencing FHIR resources.

# Isolating Configuration Information

This project creates a default setup that will run locally after a standard setup for a 
Python application. ie:

    - git clone
    - pip install -r requirements/requirements.txt
    - python manage.py makemigrations
    - python manage.py migrate
    - python manage.py createsuperuser
    - python manage.py runserver
    
Configuration settings are defined in: 

    - hhs_oauth_server.settings.base.

Installation specific configurations can be defined in other settings files
stored in hhs_oauth_server.settings.

Sensitive values, such as the SECRET_KEY should NOT be stored in files that
are stored in to the repository. This project has created a structure that
enables sensitive values to be defined via Environment Variables. The convention
we have used is as follows:

    - A file "custom-envvars.py" is defined in the parent directory. ie. Where
    the project is git cloned from.
    - Custom-envvars.py is a python file that will set an environment variable
    if it has not already been defined.
    - If the custom-envvars file exists it is called from manage.py and  wsgi.py
    - the base.py settings will then define various settings using an 
    environment variable, or a default if a variable is not found.
    
An example of a custom-envvars.py file is shown below:

    import os

    def no_overwrite(env_var, env_val):
        """ Do not overwrite ENV VAR if it exists """
        check_for = os.environ.get(env_var)
        if check_for:
            # print("%s already set" % env_var)
            return
        else:
            # Not set
            os.environ.setdefault(env_var, env_val)
            # print("%s set to %s" % (env_var, env_val))
        return


    no_overwrite('DJANGO_SECRET_KEY', 'YOUR_LOCAL_SECRET_KEY')
    no_overwrite('DJANGO_SETTINGS_MODULE', 'hhs_oauth_server.settings.base')
    no_overwrite('DJANGO_APP_ADMINS', "('Mark A Scrimshire', 'mark@healthca.mp')")
    no_overwrite('HOSTNAME_URL', 'http://127.0.0.1:8000')
    
    # PostgreSQL
    # postgres://USER:PASSWORD@HOST:PORT/NAME

    # MySQL
    # mysql://USER:PASSWORD@HOST:PORT/NAME

    # SQLite
    # sqlite:///PATH
    DEFAULT_DB_SET="sqlite:///" 

    DJANGO_BASE_DIR="Project_Directory"
    DEFAULT_DB_SET += DJANGO_BASE_DIR
    DEFAULT_DB_SET += "db.sqlite3"

    # Using dj_database_url in settings
    no_overwrite('DATABASES_CUSTOM', DEFAULT_DB_SET )

    # Uncomment the next line if you want to prove that this file is being run as part of wsgi.py
    # print("Variables set for server:%s" % os.environ.get('HOSTNAME_URL'))
