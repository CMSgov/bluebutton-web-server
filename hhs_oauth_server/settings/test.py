from .dev import *

del LOGGING['loggers']

SEND_SMS = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
REQUIRE_AUTHOIRZE_APP_FLAG = False

LOGIN_RATE = '100/m'

REQUEST_CALL_TIMEOUT = (5, 120)

OFFLINE = True

# Should be set to True in production and False in all other dev and test environments
# Replace with BLOCK_HTTP_REDIRECT_URIS per CBBP-845 to support mobile apps
# REQUIRE_HTTPS_REDIRECT_URIS = True
BLOCK_HTTP_REDIRECT_URIS = False

OAUTH2_PROVIDER = {
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
    # {
    #     'NAME': 'apps.accounts.validators.'
    #             'UniqueAndMinAgedPasswordsValidator',
    #     'OPTIONS': {
    #             # password minimum age in seconds (1 day)
    #             'password_min_age': 60 * 60 * 24,
    #             # password reuse interval in seconds (120 day)
    #             'password_reuse_interval': 60 * 60 * 24 * 120,
    #             # password expire in seconds (30 day)
    #             'password_expire': 60 * 60 * 24 * 30,
    #     }
    # },
    # {
    #     'NAME': 'django_password_validators.password_character_requirements.password_validation.'
    #             'PasswordCharacterValidator',
    #     'OPTIONS': {
    #             'min_length_digit': 1,
    #             'min_length_alpha': 1,
    #             'min_length_special': 1,
    #             'min_length_lower': 2,
    #             'min_length_upper': 2,
    #             'special_characters': "[~!@#$%^&*()_+{}\":;'[]"
    #     }
    # }
]

# http required in ALLOWED_REDIRECT_URI_SCHEMES for tests to function correctly
APPLICATION_TITLE = "Blue Button 2.0 TEST"
