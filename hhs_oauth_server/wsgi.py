import os
from getenv import env
from django.core.wsgi import get_wsgi_application


DJANGO_CUSTOM_SETTINGS_DIR = env("DJANGO_CUSTOM_SETTINGS_DIR", '..')
EXEC_FILE = os.path.join(DJANGO_CUSTOM_SETTINGS_DIR, 'custom-envvars.py')

# check if custom-envvars.py exists
# If it does then run it
if os.path.isfile(EXEC_FILE):

    # Python2
    try:
        execfile(EXEC_FILE)
    except NameError:
        # Python3 - execfile call format changed
        exec(open(EXEC_FILE).read())

else:
    print("no custom variables set:[%s] - Not Found" % EXEC_FILE)
# If custom-envvars or web server didn't pre-set DJANGO_SETTINGS_MODULE
# then we set it to the default
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hhs_oauth_server.settings.base")

application = get_wsgi_application()
