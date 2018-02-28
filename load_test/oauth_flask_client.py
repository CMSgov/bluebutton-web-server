#!/bin/python
"""
Oauth Flask Client

Taken from
http://requests-oauthlib.readthedocs.io/en/latest/examples/real_world_example.html#real-example
almost directly, with a few small changes (like turning on insecure transport
for local testing, adding more logging, and configuring the variables and paths
to point to blue button).

This spins up a flask server listening on port 5000.  Navigating to
localhost:5000 will then walk you through the oauth flow.

This is not integrated with locust in any way, but maybe locust could be used by
pointing it to this server?  Haven't figured that out.

The locust test can take the access token as input, so to load test the non
oauth parts of the application, one flow could be to run this to get the token,
then plug that into the locust test.
"""

from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for
from flask.json import jsonify
import os

app = Flask(__name__)

# https://stackoverflow.com/questions/27785375/testing-flask-oauthlib-locally-without-https
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


###################################################
# Application Specific Settings
#
# This doesn't have any fancy setup/config files.  All the parameters specific
# to your application should go here.
# - client_id: ID of the application you registered with the resource provider
# - client_secret: The corresponding client secret
# - authorization_base_url: The URL to send the first step of the oauth flow
# - token_url: The URL to send the third step of the oauth flow to
# - redirect_uri: The URL to send the client to in step two of the oauth flow
# - resource_url: The URL of the resource to access after oauth  is complete
#
# client_id = os.environ["LOCUST_BB_LOAD_TEST_CLIENT_ID"]
# client_secret = os.environ["LOCUST_BB_LOAD_TEST_CLIENT_SECRET"]
# authorization_base_url = 'http://localhost:8000/v1/o/authorize/'
# token_url = 'http://localhost:8000/v1/o/token/'
# redirect_uri = "http://localhost:5000/callback"

client_id = os.environ["LOCUST_BB_LOAD_TEST_CLIENT_ID"]
client_secret = os.environ["LOCUST_BB_LOAD_TEST_CLIENT_SECRET"]
authorization_base_url = 'https://sandbox.bluebutton.cms.gov/v1/o/authorize/'
token_url = 'https://sandbox.bluebutton.cms.gov/v1/o/token/'
redirect_uri = "http://localhost:5000/callback"
resource_url = 'https://sandbox.bluebutton.cms.gov/v1/connect/userinfo'
###################################################


@app.route("/")
def demo():
    """Step 1: User Authorization.

    Redirect the user/resource owner to the OAuth provider (i.e. Github)
    using an URL with a few key OAuth parameters.
    """
    app.logger.debug("Step 1: User Authorization.")
    github = OAuth2Session(client_id, redirect_uri=redirect_uri)
    authorization_url, state = github.authorization_url(authorization_base_url)
    app.logger.debug("Authorization URL: %s", authorization_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    app.logger.debug("OAuth State: %s", session['oauth_state'])
    return redirect(authorization_url)


# Step 2: User authorization, this happens on the provider.

@app.route("/callback", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    app.logger.debug("Step 1: Retrieving Access Token.")
    github = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=redirect_uri)
    app.logger.debug("Authorization Response: %s", request.url)
    app.logger.debug("Token URL: %s", token_url)
    token = github.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /resource.
    session['oauth_token'] = token
    app.logger.debug("Token: %s", session['oauth_token'])

    return redirect(url_for('.resource'))


@app.route("/resource", methods=["GET"])
def resource():
    """Fetching a protected resource using an OAuth 2 token.
    """
    app.logger.debug("Fetching URL: %s with token %s", resource_url, session['oauth_token'])
    github = OAuth2Session(client_id, token=session['oauth_token'], redirect_uri=redirect_uri)
    res = github.get(resource_url)
    app.logger.debug("Resource response code: %s", res.status_code)

    app.logger.debug("### Access Token: %s ###", session['oauth_token']['access_token'])

    return jsonify(res.json())


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"

    app.secret_key = os.urandom(24)
    app.run(debug=True)
