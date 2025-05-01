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

        # process scopes for subsumption
        app_scopes_avail = self.normalize_scopes(app_scopes_avail)
        # Set scopes based on application choice. Default behavior is True, if it hasn't been set yet.
        if application.require_demographic_scopes in [True, None]:
            # Return all scopes
            return app_scopes_avail
        else:
            # Remove personal information scopes
            return list(set(app_scopes_avail).difference(set(settings.BENE_PERSONAL_INFO_SCOPES)))

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
            return list(set(app_scopes_default).difference(set(settings.BENE_PERSONAL_INFO_SCOPES)))

    def normalize_scopes(self, scopes):
        #
        # legacy & v2 scopes integration:
        #
        # scopes: array of scope permissions in legacy and / or v2 syntax
        # rules for normalization:
        #
        # 1. if there is v2 permission <resource>.rs, add <resource>.r and <resource>.s
        #    to the scopes.
        # 2. if there is no v2 permission (policy admin did not select any v2 permission) found in step 1,
        #    expand legacy fhir permission as below:
        #    <resource>.read -> <resource>.rs <resource>.r <resource>.s

        v2_selected = False
        out_scopes = set(scopes)

        for p in scopes:
            if p in settings.V2_SCOPE_PERMISSIONS:
                v2_selected = True
                out_scopes = out_scopes.union(settings.AUTH_SCOPE_V2_SUBSUMPTION.get(p))

        if not v2_selected:
            # no explicitly selected v2 permission, do legacy -> v2 expand
            for p in scopes:
                if settings.LEGACY_SCOPE_TO_V2_MAP.get(p):
                    out_scopes = out_scopes.union(settings.LEGACY_SCOPE_TO_V2_MAP.get(p))

        return list(out_scopes)
