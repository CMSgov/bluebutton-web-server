oAuth Server - An oAuth Provider Sample Project
===============================================

Quick Setup
-----------

    git clone https://github.com/videntity/hhs_oauth_server.git
    pip install -r requirements/requirements.txt
    python manage.py migrate
    python manage.py runserver

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

To add/update/remove requirements **always** change the `requirements/requirements.in`
file. Then run:

    cd requirements/
    pip-compile requirements.in

This will produce a new `requirements.txt` with all dependencies pinned.
