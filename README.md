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
