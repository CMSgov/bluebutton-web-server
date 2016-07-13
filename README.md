OAuth Server - An OAuth Provider Project
========================================

[![Build Status](https://travis-ci.org/TransparentHealth/hhs_oauth_server.svg?branch=develop)](https://travis-ci.org/TransparentHealth/hhs_oauth_server)

The project is based in Python 3 and Django 1.9.5.

It consists of an OAuth2 server and a FHIR server that serves specific resources.
This application will handle the OAuth 2 handshaking and configuration with CMS Medicare
beneficiaries and Registered Developers.

The prototype application will be served from an AWS instance (https://dev.bbonfhir.com).
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

    # install the requirements
    pip install -r requirements/requirements.txt

    # prepare Django settings
    cp hhs_oauth_server/settings/local_sample.txt hhs_oauth_server/settings/local.py
    
Note that you will need to add valid AWS keys setup to use Simple Email Service (SES) in your local.py. If you do not,
the email functions will not work.  anything defined in local.py overrides items in base.py.  


    #Setup the database
    python manage.py migrate
    python manage.py loaddata apps/accounts/fixtures/BlueButtonGroup.json
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
