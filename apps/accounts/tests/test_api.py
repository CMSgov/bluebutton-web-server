import json
from http import HTTPStatus

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse

# class TestUserSelfEndpoint(BaseApiTest):
#     """
#     Tests for the /user/self/ api endpoint.
#     """
pytestmark = pytest.mark.django_db


def test_user_self_post_method_forbidden(basic_user, create_capability, get_access_token, client):
    """
    Tests that POST requests to /user/self/ endpoint are forbidden.
    """
    create_capability('userinfo', [['GET', reverse('openid_connect_userinfo')]])

    # Get an access token for the user 'john'
    access_token = get_access_token(basic_user.username)
    # Authenticate the request with the bearer access token
    auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}

    response = client.post(reverse('openid_connect_userinfo'), **auth_headers)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_user_self_get_fails_without_credentials(client):
    """
    Tests that GET requests to /connect/userinfo endpoint fail without
    a valid access_token.
    """
    response = client.get(reverse('openid_connect_userinfo'))
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.get('WWW-Authenticate') == 'Bearer realm="api"'


def test_user_self_get_access_token_query_param(basic_user, get_access_token, client):
    """
    Tests that GET requests to /connect/userinfo endpoint fail when
    the access token is given in the query params
    """
    access_token = get_access_token(basic_user.username)
    url = reverse('openid_connect_userinfo')
    url += '?access_token=%s' % (access_token)
    auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}

    response = client.get(url, **auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    content = json.loads(response.content.decode('utf-8'))
    assert content['detail'] == (
        'Using the access token in the query parameters is not supported. Use the Authorization header instead'
    )


def test_user_self_get(basic_user, create_capability, get_access_token, client):
    """
    Tests that GET request to /connect/userinfo returns user details for
    the authenticated user.
    """
    create_capability('userinfo', [['GET', reverse('openid_connect_userinfo')]])

    # Get an access token for the user 'john'
    access_token = get_access_token(basic_user.username)

    # Authenticate the request with the bearer access token
    auth_headers = {'HTTP_AUTHORIZATION': 'Bearer %s' % access_token}
    response = client.get(reverse('openid_connect_userinfo'), **auth_headers)
    assert response.status_code == HTTPStatus.OK

    # Check if the content of the response corresponds to the expected json
    expected_json = {
        'sub': basic_user.crosswalk.fhir_id(2),
        'patient': basic_user.crosswalk.fhir_id(2),
        'name': '%s %s' % (basic_user.first_name, basic_user.last_name),
        'given_name': basic_user.first_name,
        'family_name': basic_user.last_name,
        'email': basic_user.email,
        'iat': DjangoJSONEncoder().default(basic_user.date_joined),
    }

    assert json.loads(response.content) == expected_json


# class TestSingleAccessTokenValidator(BaseApiTest):
def test_single_access_token_issued(basic_user, create_application, get_access_token):
    # create the user
    # self._create_user('john', '123456', first_name='John', last_name='Smith', email='john@smith.net')
    # create a oauth2 application
    # application = self._create_application('test')
    app = create_application('test')
    # get the first access token for the user 'john'
    first_access_token = get_access_token(basic_user.username, app)
    # request another access token for the same user/application
    second_access_token = get_access_token(basic_user.username, app)
    assert first_access_token != second_access_token


def test_new_access_token_issued_when_scope_changed(
    basic_user, create_capability, create_application, get_access_token
):
    """
    Test that a new access token is issued when a scope is changed.

    e.g. old_token_scope = 'read'
            new_token_scope = 'read write'
    """
    # create the user
    # self._create_user('john', '123456', first_name='John', last_name='Smith', email='john@smith.net')
    # create read and write capabilities
    # read_capability = self._create_capability('Read', [])
    read_capability = create_capability('Read', [])
    write_capability = create_capability('Write', [])
    # write_capability = self._create_capability('Write', [])
    # create a oauth2 application and add capabilities
    # application = self._create_application('test')
    app = create_application('test')
    # application.scope.add(read_capability, write_capability)
    app.scope.add(read_capability, write_capability)
    # get the first access token for the user 'john'
    # first_access_token = self._get_access_token('john', application)
    # request another access token for the same user/application
    # second_access_token = self._get_access_token('john', application)
    first_access_token = get_access_token(basic_user.username, app)
    second_access_token = get_access_token(basic_user.username, app)
    assert first_access_token != second_access_token
    # self.assertNotEqual(first_access_token, second_access_token)
