from .base import *

# security enforcement
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = env('DJANGO_SESSION_COOKIE_SECURE', True)

# AWS
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')

# emails
EMAIL_BACKEND_DEFAULT = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', EMAIL_BACKEND_DEFAULT)
EMAIL_HOST = env('DJANGO_EMAIL_HOST')
EMAIL_PORT = env('DJANGO_EMAIL_HOST_PORT')
EMAIL_HOST_USER = env('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('DJANGO_EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env('DJANGO_EMAIL_USE_TLS', True)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    # Add Check for SLS Authentication
    'apps.accounts.auth.SettingsBackend',
    # Add check for MyMedicare Login Hack
    'apps.accounts.mymedicare_auth.MyMedicareBackend',
)
