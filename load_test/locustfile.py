#!/usr/bin/python
"""
BlueButton (2.0!) Locust Test

A basic locust test for blue button.  This right now simply has stubs for the
oauth flow and tries to retrieve the access token from the
"LOCUST_BB_LOAD_TEST_ACCESS_TOKEN" environment variable.

Things to do:

- Somehow integrate oauth setup
- Actually load test oauth setup (comments below)
- Load test various resource endpoints rather than just profile, with test
  users/data
"""

from locust import HttpLocust, TaskSet, task, web
from requests_oauthlib import OAuth2Session
import os

# The global oauth2 metadata
#
# TODO: Make this work with multiple clients...  Each client may already get a
# different context, but if not a throwaway version could be just to number the
# clients and store the access tokens in a dict.
#
# It's important that the access token is correct on this side, so we can see if
# the load test reveals cases where an access token is returned but not
# authorized.
access_token = None
oauth2_state = None

# XXX: Setting this now explicitly because I haven't figured out how to
# integrate the oauth handshake fully into locust.
if "LOCUST_BB_LOAD_TEST_ACCESS_TOKEN" in os.environ:
    access_token = os.environ["LOCUST_BB_LOAD_TEST_ACCESS_TOKEN"]

# Get the client ID and secret for the oauth application from the environment
client_id = os.environ["LOCUST_BB_LOAD_TEST_CLIENT_ID"]
client_secret = os.environ["LOCUST_BB_LOAD_TEST_CLIENT_SECRET"]

# Authorization and token URLs.  Not important now because this load test does
# not load test oauth.
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'


# Resource being accessed.  This is currently the only thing the load test is
# testing.
resource_url = 'https://sandbox.bluebutton.cms.gov/v1/connect/userinfo'


# We need to specify this in the oauth handshake with bluebutton because of a
# bug where this is required:
# https://github.com/CMSgov/bluebutton-web-server/issues/507#issuecomment-365418905
redirect_uri = "http://localhost:5000/callback"


@web.app.route('/callback')
def callback():
    """
    Oauth 2.0: Step 2

    This is the callback used in the Oauth2 flow.  For now, we're just
    registering it with the locust flask server, which might be an issue when
    we're dealing with multiple clients.

    See https://docs.locust.io/en/latest/extending-locust.html#adding-web-routes
    for how to use this.
    """
    global access_token
    pass


class UserBehavior(TaskSet):
    def on_start(self):
        """
        Oauth 2.0: Step 1

        Handle initialization behavior.  Right now this doesn't actually load
        test the oauth part, just sets it up so that the actual load test tasks
        can run.

        It should be possible to test this by creating a "custom client" as
        described in
        https://docs.locust.io/en/latest/testing-other-systems.html, and
        treating "request failure" as a failure of the oauth handshake.
        """
        github = OAuth2Session(client_id, redirect_uri=redirect_uri)
        authorization_url, state = github.authorization_url(authorization_base_url)
        response = self.client.get(authorization_url)
        # This is the login page, because you need to log in to grant access...
        # The next page would be the authorization page, which would then
        # redirect you back to the callback.
        print(response.content)

    @task
    def get_resource(self):
        """
        Retrieve a resource using the global access token, currently set
        manually.
        """
        self.client.headers['Authorization'] = 'Bearer ' + access_token
        response = self.client.get(resource_url)
        print(response.content)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000
