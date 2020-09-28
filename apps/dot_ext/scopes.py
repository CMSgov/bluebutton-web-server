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
        # Return empty scopes list, if application is none
        if application is None:
            return []

        # Get list of all available scopes
        app_scopes_avail = list(
            ProtectedCapability.objects.filter(Q(default=True) | Q(application=application))
                                       .values_list('slug', flat=True).distinct())

        # Set scopes based on application choice. Default behavior is True, if it hasn't been set yet.
        if application.require_demographic_scopes in [True, None]:
            # Return all scopes
            return app_scopes_avail
        else:
            # Remove personal information scopes
            app_scopes = []
            for s in app_scopes_avail:
                if s not in settings.BENE_PERSONAL_INFO_SCOPES:
                    app_scopes.append(s)
            return app_scopes

    def get_default_scopes(self, application=None, request=None, *args, **kwargs):
        """
        Returns a list that contains all the capabilities related
        to the current application.
        """
        # Return empty scopes list, if application is none
        if application is None:
            return []

        # at the moment we assume that the default scopes are all those availables
        app_scopes_default = list(ProtectedCapability.objects.filter(default=True)
                                                             .values_list('slug', flat=True))

        # Set scopes based on application choice. Default behavior is True, if it hasn't been set yet.
        if application.require_demographic_scopes in [True, None]:
            # Return all scopes
            return app_scopes_default
        else:
            # Remove personal information scopes
            app_scopes = []
            for s in app_scopes_default:
                if s not in settings.BENE_PERSONAL_INFO_SCOPES:
                    app_scopes.append(s)
            return app_scopes
