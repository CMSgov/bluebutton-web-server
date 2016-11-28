from django.conf import settings
from django.contrib.auth.models import User, Group
import ldap
from .models import UserProfile
import sys


class LDAPBackend(object):
    """
    Authenticate against the settings LDAP.

    """

    def authenticate(self, username=None, password=None):
        # ldap/ldaps
        protocol = getattr(settings, 'LDAP_PROTOCOL', "ldap")
        # host name
        host = getattr(settings, 'LDAP_HOST', "localhost")
        # testing w/ LDAP=10389 & LDAPS=10636
        port = getattr(settings, 'LDAP_PORT', "10389")
        retrieveAttributes = getattr(settings, 'LDAP_RETRIEVE_ATTRIBUTES',
                                     ['cn', 'sn', 'gn', 'mail', 'uid'])
        # Could be something like" "dc=example,dc=com"
        base_dn = getattr(settings, 'LDAP_BASE_DN', "")

        # User's DN
        user_dn = "uid=" + username + ",ou=users,ou=system"

        # Server url:
        ldap_server = "%s://%s:%s" % (protocol, host, port)
        search_filter = "uid=" + username

        # Initialize ldap
        connect = ldap.initialize(ldap_server)
        # Attempt to connect and bind
        try:
            print('Attempt bind')
            # if authentication successful, get the full user data
            connect.bind_s(user_dn, password, ldap.AUTH_SIMPLE)
            print('Bound')
            result = connect.search_s(
                base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                retrieveAttributes)
            # return all user data results
            connect.unbind_s()
            print(result)
            username = result[0][1]['uid'][0]
            last_name = result[0][1]['sn'][0]
            first_name = result[0][1]['givenName'][0]
            email = result[0][1]['mail'][0]

        except ldap.LDAPError:
            print("Authentication error")
            print(sys.exc_info())
            connect.unbind_s()
            result = []

        if result:

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password
                # to anything, because it won't be checked; the password
                # from the external backend is checked (coming from settings).
                user = User(username=username, password='flubbernubber',
                            first_name=first_name,
                            last_name=last_name,
                            email=email)
                user.save()
                up, created = UserProfile.objects.get_or_create(
                    user=user, user_type='BEN')
                group = Group.objects.get(name='BlueButton')
                user.groups.add(group)

            return user
        # LDAP Authentication failed.
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
