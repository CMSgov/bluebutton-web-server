import logging
import os
import apps.logging.request_logger as bb2logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


logger = logging.getLogger(bb2logging.HHS_SERVER_LOGNAME_FMT.format(__name__))


def create_superuser(username, password, email):
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        # Otherwise we instantiate the super user
        u = User(username=username, first_name="Super", last_name="User",
                 email=email)
    u.set_password(password)
    u.is_superuser = True
    u.is_staff = True
    u.save()
    return True


class Command(BaseCommand):
    help = 'Create a super user'

    def handle(self, *args, **options):

        # get variables
        super_username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")
        super_password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        super_email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if super_username and super_password and super_email:
            # create a super user
            r = create_superuser(super_username, super_password, super_email)
            if r:
                logger.info('Superuser created/updated.')
            else:
                logger.info('Something went wrong creating/updating superuser')
        else:
            logger.debug(
                'Environment variables DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD,',
                'DJANGO_SUPERUSER_EMAIL must be set before using this command.')
