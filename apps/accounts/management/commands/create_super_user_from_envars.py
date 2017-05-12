from __future__ import absolute_import
from __future__ import unicode_literals
from getenv import env
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


def create_superuser(username, password, email):
    # First we check if the superuser exists.
    # If  it does we will reset password.
    # If we don't test for a user first then the Save causes an Integrity Error
    try:
        u = User.objects.get(username=username)
        print("%s account exists. Resetting password" % username)
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
        super_username = env("DJANGO_SUPERUSER_USERNAME", "")
        super_password = env("DJANGO_SUPERUSER_PASSWORD", "")
        super_email = env("DJANGO_SUPERUSER_EMAIL", "")
        if super_username and super_password and super_email:
            # create a super user
            r = create_superuser(super_username, super_password, super_email)
            if r:
                print('Superuser created/updated.')
            else:
                print('Something went wrong')
        else:
            print(
                'Environment variables DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD,',
                'DJANGO_SUPERUSER_EMAIL must be set before using this command.')
