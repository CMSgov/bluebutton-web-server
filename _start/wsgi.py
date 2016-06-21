"""
WSGI config for hhs_oauth_server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os
import sys

from django.core.wsgi import get_wsgi_application

# print('We are launching in folder:',
#       os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Generic append path:
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Target for RHEL
# sys.path.append('/var/www/pyapps/hhs_oauth_server')

# Target for Ubuntu
# sys.path.append('/home/ubuntu/django-projects/hhs_oauth_server')

os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'hhs_oauth_server._start.settings.base')

application = get_wsgi_application()

__author__ = 'Mark Scrimshire:@ekivemark'
