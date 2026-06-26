import os

# import dotenv
from dotenv import load_dotenv
from django.core.wsgi import get_wsgi_application

# project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DJANGO_CUSTOM_SETTINGS_DIR = os.path.join(BASE_DIR, '..')

# If the .env file is present, load it
if os.path.isfile(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, '.env')):
    load_dotenv(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, '.env'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hhs_oauth_server.settings.base')

application = get_wsgi_application()
