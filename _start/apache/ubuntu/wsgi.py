"""
WSGI config for hhs_oauth_server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os,sys
from django.core.wsgi import get_wsgi_application

# Target for RHEL
sys.path.append('/var/www/pyapps/hhs_oauth_server')
# sys.path.append('/home/ubuntu/django-projects/hhs_oauth_server')

os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                      "hhs_oauth_server._start.settings.local")

application = get_wsgi_application()
