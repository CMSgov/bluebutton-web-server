
WAFFLE_FEATURE_FLAGS = ()

WAFFLE_FEATURE_SWITCHES = (
    ('enable_coverage_only', True, 'This enables the coverage-only use case.'),
    ('enable_swaggerui', True, 'This enables a page for the openapi docs and a link to the page from the main page.'),
    ('enable_testclient', True, 'This enables the test client.'),
    ('expire_grant_endpoint', True, 'This enables the /v<1/2>/o/expire_authenticated_user/<patient_id>/ endpoint.'),
    ('login', True, 'This enables login related URLs and code. See apps/accounts/urls.py file for more info.'),
    ('logout', True, 'This enables logout related URLs and code. See apps/accounts/urls.py file for more info.'),
    ('outreach_email', True, 'This enables developer outreach emails. Not active in prod.'),
    ('require-scopes', True, 'Thie enables enforcement of permission checking of scopes.'),
    (
        'show_django_message_sdk',
        True,
        'This controls whether or not the \'what\'s new\' message is shown in developer sandbox home.'
    ),
    ('show_testclient_link', True, 'This controls the display of the test client link from the main page.'),
    ('signup', True, 'This enables signup related URLs and code paths. Not active in prod.'),
    ('splunk_monitor', False, 'This is used in other environments to ensure splunk forwarder is running.'),
    ('v3_endpoints', True, 'This enables v3 endpoints.'),
    ('v3_testclient', True, 'Enables v3 pathways in the testclient.'),
    (
        'wellknown_applications',
        True,
        'This enables the /.well-known/applications end-point. Active in prod, but not in sbx/test.'
    ),
    ('one_hour_token_expiry', False, 'This makes OAuth2 access tokens expire in one hour.')
)
