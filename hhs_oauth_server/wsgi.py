import os
import newrelic.agent
import dotenv

from django.core.wsgi import get_wsgi_application


# project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DJANGO_CUSTOM_SETTINGS_DIR = os.path.join(BASE_DIR, '..')

# If the New Relic config file is present, load and configure the agent
if os.path.isfile(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'newrelic.ini')):
    newrelic.agent.initialize(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'newrelic.ini'))

# If the .env file is present, load it
if os.path.isfile(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, '.env')):
    dotenv.read_dotenv(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, '.env'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hhs_oauth_server.settings.base")

application = get_wsgi_application()
