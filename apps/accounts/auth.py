from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User, Group

from .models import UserProfile, create_activation_key


class SettingsBackend(object):
    """
    Authenticate against the settings SETTINGS_AUTH_USER and SETTINGS_AUTH_PASSWORD.

    Use the login name, and a hash of the password. For example:

    SETTINGS_AUTH_USER = 'ben'
    SETTINGS_AUTH_PASSWORD = 'pbkdf2_sha256$24000$V6XjGqYYNGY7$13tFC13aa'
                   'TohxBgP2W3glTBz6PSbQN4l6HmUtxQrUys='

    """

    def authenticate(self, username=None, password=None):

        username = username.rstrip().lstrip().lower()
        login_valid = (getattr(settings, 'SETTINGS_AUTH_USER', "") == username)
        pwd_valid = check_password(password, settings.SETTINGS_AUTH_PASSWORD)
        # pwd_valid = check_password(password, pwd_to_compare)
        if login_valid and pwd_valid:
            # print("VALID SLS USER AND PASSWORD")
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password
                # to anything, because it won't be checked; the password
                # from the external backend is checked (coming from settings).
                user = User(
                    username=username, password='flubbernubber', first_name=getattr(
                        settings, 'SETTINGS_AUTH_FIRST_NAME', ""), last_name=getattr(
                        settings, 'SETTINGS_AUTH_LAST_NAME', ""), email=getattr(
                        settings, 'SETTINGS_AUTH_EMAIL', ""), is_active=False)
                user.save()
                up, created = UserProfile.objects.get_or_create(
                    user=user, user_type='BEN')
                group = Group.objects.get(name='BlueButton')
                user.groups.add(group)
                # Send verification email
                create_activation_key(user)

            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
