# Locust.io Load Testing

This is a first pass at load testing, with many rough edges and things not done
yet.

## Quick Start

Install dependencies:

```
pipenv install
pipenv shell
```

Run Oauth 2.0 flow and get access code:

```
export LOCUST_BB_LOAD_TEST_CLIENT_ID=<client_id>
export LOCUST_BB_LOAD_TEST_CLIENT_SECRET=<client_secret>
python oauth_flask_client.py
# Navigate to localhost:5000 and follow the oauth flow
# Copy the auth token from the logs, should be last debug line
```

The client ID and secret should be from when you registered your oauth
application.

Finally, run the load test using that access code:

```
export LOCUST_BB_LOAD_TEST_ACCESS_TOKEN="<auth_token>"
locust --host https://sandbox.bluebutton.cms.gov
# Navigate to localhost:8089 and run some locusts
```

## Files

- `oauth_flask_client.py`: The flask application that can run the Oauth 2.0 flow
  and get the access token.  It should use it to request the "userinfo"
  resource.  See https://bluebutton.cms.gov/developers/#core-resources.
- `locustfile.py`: The file run by locust.io, with the default name.  This
  doesn't yet have Oauth 2.0 support, instead it depends on you to explicitly
  set the access token.
- `Pipfile`: Dependencies, as specified by pipenv:
  https://github.com/pypa/pipenv
