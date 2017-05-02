from django.conf import settings
from django.contrib.auth.models import User, Group
from django_python3_ldap import ldap
# import ldap3 as ldap
from .models import UserProfile
import sys


class LDAPBackend(object):
    """
    Authenticate against  LDAP.
    Uses acv/secret as test credentials
    """

    # ldap/ldaps
    protocol = getattr(settings, 'LDAP_PROTOCOL', "ldap")

    # host name
    host = getattr(settings, 'LDAP_HOST', "localhost")

    # testing w/ LDAP=10389 & LDAPS=10636
    port = getattr(settings, 'LDAP_PORT', "10389")

    # Server url:
    ldap_server = "%s://%s:%s" % (protocol, host, port)

    retrieveAttributes = getattr(settings, 'LDAP_RETRIEVE_ATTRIBUTES',
                                 ['cn', 'sn', 'gn', 'mail', 'uid'])

    # Could be something like" "dc=example,dc=com"
    base_dn = getattr(settings, 'LDAP_BASE_DN', "")

    user_dn_suffix = getattr(settings, 'LDAP_USER_DN_SUFFIX',
                             ",ou=users,ou=system")

    def authenticate(self, username=None, password=None):

        # Force lowercase username
        username = username.rstrip().lstrip().lower()

        # User's DN
        user_dn = "uid=" + username + self.user_dn_suffix

        # search filter
        search_filter = "uid=" + username

        # Initialize ldap
        connect = ldap.initialize(self.ldap_server)

        # Attempt to connect and bind
        try:
            # print('Attempt bind')
            # if authentication successful, get the full user data
            connect.bind_s(user_dn, password, ldap.AUTH_SIMPLE)
            # print('Bound')
            # return all user data results
            result = connect.search_s(
                self.base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                self.retrieveAttributes)
            # print(result)
            # Unbind
            connect.unbind_s()
            # Pull out what we want into variables.
            username = result[0][1]['uid'][0]
            last_name = result[0][1]['sn'][0]
            first_name = result[0][1]['givenName'][0]
            email = result[0][1]['mail'][0]

        except ldap.INVALID_CREDENTIALS:
            print("Invalid credentials for user", username)
            # print(sys.exc_info())
            connect.unbind_s()
            result = []

        except ldap.SERVER_DOWN:
            print("LDAP Server not reachable")
            # print(sys.exc_info())
            connect.unbind_s()
            result = []

        except ldap.LDAPError:
            print("LDAP Error", sys.exc_info())
            connect.unbind_s()
            result = []

        if result:

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. Note that we can set password
                # to anything, because it won't be checked; the password
                # from the external backend is checked (coming from LDAP).
                user = User(username=username.rstrip().lstrip().lower(),
                            password='flubbernubber',
                            first_name=first_name,
                            last_name=last_name,
                            email=email.rstrip().lstrip().lower())
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

    def can_connect_to_ldap(self):
        try:
            # Initialize ldap
            connect = ldap.initialize(self.ldap_server)
            connect.bind_s(
                "uid=foo,ou=users,ou=system",
                "bar",
                ldap.AUTH_SIMPLE)
            connect.unbind_s()
            return True
        except ldap.SERVER_DOWN:
            return False
        except ldap.INVALID_CREDENTIALS:
            return True
        except ldap.LDAPError:
            return True
