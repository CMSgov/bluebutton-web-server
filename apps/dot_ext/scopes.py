from django.conf import settings
from django.db.models import Q
from oauth2_provider.scopes import BaseScopes
from apps.capabilities.models import ProtectedCapability


class CapabilitiesScopes(BaseScopes):
    """
    A scope backend that uses ProtectedCapability model.
    """
    def get_all_scopes(self):
        """
        Returns a dict-like object that contains all the scopes
        in the ProtectedCapability model.
        """
        return dict(ProtectedCapability.objects.values_list('slug', 'title'))

    def get_available_scopes(self, application=None, request=None, *args, **kwargs):
        """
        Returns a list that contains all the capabilities related
        to the current application.
        """
        app_scopes_avail = list(
            ProtectedCapability.objects.filter(Q(default=True) | Q(application=application))
                                       .values_list('slug', flat=True).distinct())

        if getattr(application, 'require_demographic_scopes', True) is False:
            # Remove personal information scopes, if requested by application
            app_scopes = []
            for s in app_scopes_avail:
                if s not in settings.BENE_PERSONAL_INFO_SCOPES:
                    app_scopes.append(s)
            return app_scopes
        else:
            # Return all available scopes if True or None:
            return app_scopes_avail

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        """
        Returns a list that contains all the capabilities related
        to the current application.
        """
        # at the moment we assume that the default scopes are all those availables
        app_scopes_default = list(ProtectedCapability.objects.filter(default=True)
                                                             .values_list('slug', flat=True))

        if getattr(application, 'require_demographic_scopes', True) is False:
            # Remove personal information scopes, if requested by application
            app_scopes = []
            for s in app_scopes_default:
                if s not in settings.BENE_PERSONAL_INFO_SCOPES:
                    app_scopes.append(s)
            return app_scopes
        else:
            # Return all available scopes if True or None:
            return app_scopes_default
