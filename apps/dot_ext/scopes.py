from django.db.models import Q
from oauth2_provider.scopes import BaseScopes
from typing import List
from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.constants import BENE_PERSONAL_INFO_SCOPES
from waffle import switch_is_active


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

        if switch_is_active("enable_coverage_only"):
            if "coverage-eligibility" in application.get_internal_application_labels():
                app_scopes_avail = self.remove_eob_scopes(app_scopes_avail)

        # Set scopes based on application choice. Default behavior is True, if it hasn't been set yet.
        if application.require_demographic_scopes in [True, None]:
            # Return all scopes
            return app_scopes_avail
        else:
            return self.remove_demographic_scopes(app_scopes_avail)

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

        if switch_is_active("enable_coverage_only"):
            if "coverage-eligibility" in application.get_internal_application_labels():
                app_scopes_default = self.remove_eob_scopes(app_scopes_default)

        # Set scopes based on application choice. Default behavior is True, if it hasn't been set yet.
        if application.require_demographic_scopes in [True, None]:
            # Return all scopes
            return app_scopes_default
        else:
            return self.remove_demographic_scopes(app_scopes_default)

    def condense_scopes(self, scopes):
        """
        Returns a list based on the provided list of scopes with redundant scopes consolidated
        """
        out_scopes = set(scopes)

        # Consolidate v2 resource scopes
        if "patient/Patient.rs" in scopes or ("patient/Patient.r" in scopes and "patient/Patient.s" in scopes):
            out_scopes.add("patient/Patient.rs")
            out_scopes.discard("patient/Patient.r")
            out_scopes.discard("patient/Patient.s")
        if "patient/Coverage.rs" in scopes or ("patient/Coverage.r" in scopes and "patient/Coverage.s" in scopes):
            out_scopes.add("patient/Coverage.rs")
            out_scopes.discard("patient/Coverage.r")
            out_scopes.discard("patient/Coverage.s")
        if "patient/ExplanationOfBenefit.rs" in scopes or \
                ("patient/ExplanationOfBenefit.r" in scopes and "patient/ExplanationOfBenefit.s" in scopes):
            out_scopes.add("patient/ExplanationOfBenefit.rs")
            out_scopes.discard("patient/ExplanationOfBenefit.r")
            out_scopes.discard("patient/ExplanationOfBenefit.s")

        return list(out_scopes)

    def remove_demographic_scopes(self, scopes):
        """
        Returns a list of all of the provided list except with personal info scopes removed
        """
        # Remove personal information scopes
        out_scopes = []
        for s in scopes:
            if s not in BENE_PERSONAL_INFO_SCOPES:
                out_scopes.append(s)
        return out_scopes

    def remove_eob_scopes(self, scopes):
        """
        Returns a list based on the provided list of scopes with eob scopes removed
        """
        out_scopes = set(scopes)
        out_scopes.discard("patient/ExplanationOfBenefit.r")
        out_scopes.discard("patient/ExplanationOfBenefit.s")
        out_scopes.discard("patient/ExplanationOfBenefit.rs")
        out_scopes.discard("patient/ExplanationOfBenefit.read")
        return out_scopes

    def is_smart_subscope(
        self,
        requested: str,
        original_list: List[str],
    ) -> bool:
        """Determine if the requested scope is a valid SMART v2 subscope of any scope in the original scope list.

        Args:
            requested (str): Part of the scope being requested in the current refresh token request
            original_list (List[str]): The list of scopes originally granted for the access token being refreshed
        Returns:
            bool: Whether or not the requested scope is a valid SMART v2 subscope of any scope in the original scope list
        """
        # First try exact match
        if requested in original_list:
            return True

        # For each scope in the original scope list, check if the requested scope is a valid subscope of it
        # If the requested scope does not match any scope in the original scope list, and is not a subscope either
        # we will fail the refresh token request
        for orig in original_list:
            if self._smart_scope_contains(orig, requested):
                return True
        return False

    def _smart_scope_contains(
        self,
        original: str,
        requested: str,
    ) -> bool:
        """Determine if the requested scope is a valid SMART v2 subscope of the original scope.

        Args:
            original (str): Part of the scope originally granted for the access token being refreshed
            requested (str): Part of the scope being requested in the current refresh token request
        Returns:
            bool: Whether or not the requested scope is a valid SMART v2 subscope of the original
        """

        # Split into context/resource and permissions
        # Example: original = patient/Patient.rs, requested = patient/Patient.r
        # That would result in the following splits:
        # orig_resource = patient/Patient, orig_perms = rs
        # req_resource = patient/Patient, req_perms = r
        try:
            orig_resource, orig_perms = original.rsplit('.', 1)
            req_resource, req_perms = requested.rsplit('.', 1)
        except ValueError:
            return False

        # Resource part must match exactly
        if orig_resource != req_resource:
            return False

        # All requested permission chars must be present in original
        # valid_chars is used to ignore any invalid chars that may be present in the scopes,
        # such as 'patient/Patient.rw' which has an invalid 'w' char
        orig_perm_set = set(orig_perms)
        req_perm_set = set(req_perms)

        return req_perm_set.issubset(orig_perm_set)
