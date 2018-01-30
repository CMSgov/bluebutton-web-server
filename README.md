Blue Button Web Server
=====================================================

[![Build Status](https://travis-ci.org/CMSgov/bluebutton-web-server.svg?branch=develop)](https://travis-ci.org/CMSGov/hhs_oauth_server)
[![Coverage Status](https://coveralls.io/repos/github/CMSgov/bluebutton-web-server/badge.svg?branch=develop)](https://coveralls.io/github/CMSgov/bluebutton-web-server?branch=develop)

This server serves as a data provider for sharing Medicare claims data with third parties.
The server connects to MyMedicare.gov for authentication, and uses OAuth2 to confirm permission
grants to external app developers. The data itself comes from a back end FHIR server
(https://github.com/CMSgov/bluebutton-data-server), which in turn pulls data from the CMS
Chronic Conditions Warehouse (https://www.ccwdata.org)

For more information on how to connect to the API implemented here, check out our
developer documentation at https://cmsgov.github.io/bluebutton-developer-help/. Our most
recent deployment is at https://sandbox.bluebutton.cms.gov, and you can also
check out our Google Group at https://groups.google.com/forum/#!forum/developer-group-for-cms-blue-button-api
for more details.

The information below outlines setting up the server for development or your own environment.
For general information on deploying Django see https://docs.djangoproject.com/en/1.11/howto/deployment/.

Setup
-----

These instructions provide a quick start for developers new to the project.
Follow these steps on the command line.

    # prepare your repository folder
    git clone https://github.com/CMSGov/bluebutton-web-server.git
    cd bluebutton-web-server

    # create the virtualenv
    python3 -m venv venv

    # Install any prerequisites  (C headers, etc. This is OS specific)
    # Ubuntu example
    sudo apt-get install python3-dev libxml2-dev libxslt1-dev


    # install the requirements
    pip install --upgrade pip==9.0.1
    pip install pip-tools
    pip install -r requirements/requirements.txt

    # prepare Django settings
    cp hhs_oauth_server/settings/local_sample.txt hhs_oauth_server/settings/local.py

Note that most settings can be overridden by environment variables. See custom environment variables section below.
Please ensure to create and use your own keys and secrets.  See https://docs.djangoproject.com/en/1.11/topics/settings/
for more information. Continue the installation by issuing the following commands:


    python manage.py migrate
    python manage.py loaddata apps/accounts/fixtures/scopes_and_groups.json
    python manage.py createsuperuser
    python manage.py create_admin_groups
    python manage.py create_blue_button_scopes
    python manage.py setup_bluebutton
    python manage.py create_test_user_and_application

 The next step is optional:  If your backend HAPI FHIR server is configured to require x509
 certificates to access it then you need to obtain that keypair and place those files in
 certificate folder called `cerstore`.

    mkdir ../certstore
    (copy both x509 files, in PEM format, inside certstore)

If your backend FHIR server does not require certificate-based authorization
then the previous step can be omitted.

Making calls to a back-end FHIR server requires that you set a series of
variables before running tests or the server itself.

    #Run the development server
    python manage.py runserver

Note you can find the path to your Python3 binary by typing `which python3`.

### docker-compose setup

Instructions for running the development environment via `docker-compose` can be found [here](./docker-compose/readme.md)

Running Tests
-------------

Run the following:

    python runtests.py

You can run individual applications tests as well.
See https://docs.djangoproject.com/en/1.11/topics/testing/overview/#running-tests
for more information.


Custom Environment Variables
----------------------------

Sensitive values, such as the SECRET_KEY should NOT be stored in files that
are stored in to the repository. This project has created a structure that
enables sensitive values to be defined via Environment Variables. The convention
we have used is as follows:

    - A file `custom-envvars.py` is defined in the parent directory. ie. Where
    the project is git cloned from.
    - Custom-envvars.py is a python file that will set an environment variable
    if it has not already been defined.
    - If the custom-envvars file exists it is called from manage.py and  wsgi.py
    - the base.py settings will then define various settings using an
    environment variable, or a default if a variable is not found.

An example of a `custom-envvars.py` file is shown below:

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

Using this Project
------------------

This project is free and open source software under the Apache2 license. 
You may add additional applications, authentication backends, and styles/themes 
are not subject to the Apache2 license.

In other words, you or your organization are not in any way prevented from build closed source applications
on top of this tool. Applications that you create can be licensed in any way that suits you business or organizational needs.
Any 3rd party applications are subject to the license in which they are distributed
by their respective authors.


License
-------

This project is free and open source software under the Apache 2 license. See LICENSE for more information.
