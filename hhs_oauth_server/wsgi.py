import os
import newrelic.agent
# from getenv import env
from django.core.wsgi import get_wsgi_application


# project root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DJANGO_CUSTOM_SETTINGS_DIR = os.path.join(BASE_DIR, '..')

print("CUSTOM_SETTINGS_DIR:%s" % DJANGO_CUSTOM_SETTINGS_DIR)

# custom-envvars.py should be in parent directory of the entire application
# ie. it should be in parent above manage.py so that the custom environment
# variables are NOT included in the repository.
# DJANGO_CUSTOM_SETTINGS_DIR = env("DJANGO_CUSTOM_SETTINGS_DIR", '..')
EXEC_FILE = os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'custom-envvars.py')

# check if custom-envvars.py exists
# If it does then run it
if os.path.isfile(EXEC_FILE):
    exec(open(EXEC_FILE).read())

else:
    print("no custom variables set:[%s] - Not Found" % EXEC_FILE)

# If the New Relic config file is present, load and configure the agent
if os.path.isfile(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'newrelic.ini')):
    newrelic.agent.initialize(os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'newrelic.ini'))

# If custom-envvars or web server didn't pre-set DJANGO_SETTINGS_MODULE
# then we set it to the default
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hhs_oauth_server.settings.base")

application = get_wsgi_application()
