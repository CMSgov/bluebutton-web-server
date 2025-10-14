from .dev import *

del LOGGING['loggers']


def truthy(value) -> bool:
    if value in [1, 'true', 'True', 'yes', 'Yes', 'y', 'Y', True]:
        return True
    else:
        return False


SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False

LOGIN_RATE = '100/m'

REQUEST_CALL_TIMEOUT = (5, 120)

if truthy(os.getenv("RUN_ONLINE_TESTS")):
    # We are offline. Skip tests that require us to be online.
    OFFLINE = False
else:
    # We are not offline. Go ahead and run the tests.
    OFFLINE = True

# Should be set to True in production and False in all other dev and test environments
# Replace with BLOCK_HTTP_REDIRECT_URIS per CBBP-845 to support mobile apps
# REQUIRE_HTTPS_REDIRECT_URIS = True
BLOCK_HTTP_REDIRECT_URIS = False

OAUTH2_PROVIDER = {
    'PKCE_REQUIRED': False,
    'OAUTH2_VALIDATOR_CLASS': 'apps.dot_ext.oauth2_validators.'
                              'SingleAccessTokenValidator',
    'OAUTH2_SERVER_CLASS': 'apps.dot_ext.oauth2_server.Server',
    'SCOPES_BACKEND_CLASS': 'apps.dot_ext.scopes.CapabilitiesScopes',
    'OAUTH2_BACKEND_CLASS': 'apps.dot_ext.oauth2_backends.OAuthLibSMARTonFHIR',
    'ALLOWED_REDIRECT_URI_SCHEMES': ['https', 'http']
}

CACHES = {
    'default': {
        'BACKEND': os.environ.get('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': os.environ.get('CACHE_LOCATION', 'unique-snowflake'),
    },
    'axes_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}
AXES_CACHE = 'axes_cache'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
                'NumericPasswordValidator',
    },
    {
        'NAME': 'apps.accounts.validators.'
                'PasswordReuseAndMinAgeValidator',
        'OPTIONS': {
                # password minimum age in seconds (60 sec)
                'password_min_age': 60,
                # password reuse interval in seconds (50 minutes)
                'password_reuse_interval': 3000,
                'password_expire': 0,
        }
    },
    {
        'NAME': 'apps.accounts.validators.'
                'PasswordComplexityValidator',
        'OPTIONS': {
                'min_length_digit': 1,
                'min_length_alpha': 1,
                'min_length_special': 1,
                'min_length_lower': 2,
                'min_length_upper': 2,
                'special_characters': "[~!@#$%^&*()_+{}\":;'[]"
        }
    }
]

# http required in ALLOWED_REDIRECT_URI_SCHEMES for tests to function correctly
APPLICATION_TITLE = "Blue Button 2.0 TEST"
