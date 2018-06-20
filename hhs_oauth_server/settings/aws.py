from .base import *

STATICFILES_LOCATION = '/static/'
STATICFILES_STORAGE = 'hhs_oauth_server.s3_storage.StaticStorage'
STATIC_URL = "https://%s%s" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

MEDIAFILES_LOCATION = '/media/'
DEAFULT_FILE_STORAGE = 'hhs_oauth_server.s3_storage.MediaStorage'
MEDIA_URL = "https://%s%s" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)

# Stub for Custom Authentication Backend
SLS_USER = "ben"
# enclose value for DJANGO_SLS_PASSWORD in single quotes to preserve
# special characters eg. $
# eg. export DJANGO_SLS_PASSWORD='$pecial_CharacterPre$erved'
SLS_PASSWORD = 'pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aaTohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys='
SLS_FIRST_NAME = "Ben"
SLS_LAST_NAME = "Barker"
SLS_EMAIL = 'ben@example.com'

# Email config
SEND_EMAIL = True

# Fixed user and password for fake backend
SETTINGS_AUTH_USER = 'ben'
SETTINGS_AUTH_PASSWORD = 'pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aaTohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys='
