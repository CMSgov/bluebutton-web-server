import os
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError

from apps.capabilities.models import ProtectedCapability
from apps.dot_ext.constants import BENE_PERSONAL_INFO_SCOPES
from apps.test import BaseApiTest


class ApplyDefaultScopesTest(BaseApiTest):
    maxDiff = 2000

    @patch.dict(os.environ, {'TARGET_ENV': 'prod'})
    def test_will_not_run_with_target_env_prod(self):
        """
        Assert that the command fails when running with TARGET_ENV==prod.
        """
        with self.assertRaisesMessage(CommandError, 'Target environment not in ["local", "test", "sbx"].'):
            call_command('apply_default_scopes')

    def test_app_no_scopes(self):
        """
        Test with an app that has no scopes.
        """
        app = self._create_application('an app')
        capability_a = self._create_capability('Capability A', [], default=True)
        capability_b = self._create_capability('Capability B', [], default=True)

        self.assertQuerySetEqual(app.scope.all(), [], ordered=False)

        call_command('apply_default_scopes')

        self.assertQuerySetEqual(app.scope.all(), [capability_a, capability_b], ordered=False)

    def test_app_some_scopes(self):
        """
        Test with an app that has some but not all default scopes.
        """
        app = self._create_application('an app')
        capability_a = self._create_capability('Capability A', [], default=True)
        capability_b = self._create_capability('Capability B', [], default=True)
        capability_c = self._create_capability('Capability C', [], default=True)
        app.scope.add(capability_a, capability_b)

        self.assertQuerySetEqual(app.scope.all(), [capability_a, capability_b], ordered=False)

        call_command('apply_default_scopes')

        self.assertQuerySetEqual(app.scope.all(), [capability_a, capability_b, capability_c], ordered=False)

    def test_does_not_change_extra_scopes(self):
        """
        Assert that the command does not change non-default scopes on an app.
        """
        app = self._create_application('an app')
        capability_a = self._create_capability('Capability A', [], default=True)
        capability_b = self._create_capability('Capability B', [], default=False)
        capability_c = self._create_capability('Capability C', [], default=False)
        app.scope.add(capability_b, capability_c)

        self.assertQuerySetEqual(app.scope.all(), [capability_b, capability_c], ordered=False)

        call_command('apply_default_scopes')

        self.assertQuerySetEqual(app.scope.all(), [capability_a, capability_b, capability_c], ordered=False)

    def test_assigns_demographic_scopes_required_true(self):
        """
        Assert that the command assigns demographic scopes when app has
        require_demographic_scopes==True
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = True
        app.save()

        self.assertQuerySetEqual(app.scope.all(), [], ordered=False)

        call_command('apply_default_scopes')

        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(app.scope.all(), default_scopes, ordered=False)

    def test_does_not_assign_demographic_scopes_required_none(self):
        """
        Assert that the command does not assign demographic scopes when app has
        require_demographic_scopes==None
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = None
        app.save()

        self.assertQuerySetEqual(app.scope.all(), [], ordered=False)

        call_command('apply_default_scopes')

        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(
            app.scope.all(), default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES), ordered=False
        )

    def test_does_not_assign_demographic_scopes_required_false(self):
        """
        Assert that the command does not assign demographic scopes when app has
        require_demographic_scopes==False
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = False
        app.save()

        self.assertQuerySetEqual(app.scope.all(), [], ordered=False)

        call_command('apply_default_scopes')

        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(
            app.scope.all(), default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES), ordered=False
        )

    def test_deletes_when_some_demographic_scopes_required_false(self):
        """
        If the app has require_demographic_scopes==False, but has some demographic
        scopes in the database, assert that the command deletes the demographic scopes
        for that app from the database.
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = False
        app.save()
        profile_scope = ProtectedCapability.objects.get(slug='profile')
        app.scope.add(profile_scope)

        self.assertQuerySetEqual(app.scope.all(), [profile_scope], ordered=False)

        call_command('apply_default_scopes')

        self.assertFalse(app.scope.contains(profile_scope))
        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(
            app.scope.all(), default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES), ordered=False
        )

    def test_deletes_when_all_demographic_scopes_required_false(self):
        """
        If the app has require_demographic_scopes==False, but has all demographic
        scopes in the database, assert that the command deletes the demographic scopes
        for that app from the database.
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = False
        app.save()
        demographic_scopes = [ProtectedCapability.objects.get(slug=slug) for slug in BENE_PERSONAL_INFO_SCOPES]
        app.scope.add(*demographic_scopes)

        self.assertQuerySetEqual(app.scope.all(), demographic_scopes, ordered=False)

        call_command('apply_default_scopes')

        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(
            app.scope.all(), default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES), ordered=False
        )

    def test_deletes_when_some_demographic_scopes_required_none(self):
        """
        If the app has require_demographic_scopes==None, but has some demographic
        scopes in the database, assert that the command deletes the demographic scopes
        for that app from the database.
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = None
        app.save()
        profile_scope = ProtectedCapability.objects.get(slug='profile')
        app.scope.add(profile_scope)

        self.assertQuerySetEqual(app.scope.all(), [profile_scope], ordered=False)

        call_command('apply_default_scopes')

        self.assertFalse(app.scope.contains(profile_scope))
        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(
            app.scope.all(), default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES), ordered=False
        )

    def test_deletes_when_all_demographic_scopes_required_none(self):
        """
        If the app has require_demographic_scopes==None, but has all demographic
        scopes in the database, assert that the command deletes the demographic scopes
        for that app from the database.
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = None
        app.save()
        demographic_scopes = [ProtectedCapability.objects.get(slug=slug) for slug in BENE_PERSONAL_INFO_SCOPES]
        app.scope.add(*demographic_scopes)

        self.assertQuerySetEqual(app.scope.all(), demographic_scopes, ordered=False)

        call_command('apply_default_scopes')

        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(
            app.scope.all(), default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES), ordered=False
        )

    def test_assigns_when_missing_some_demographic_scopes(self):
        """
        If the app has require_demographic_scopes==True, but is missing some
        demographic scopes in the database, assert that the command adds them for that
        app.
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = True
        app.save()
        scopes = [
            ProtectedCapability.objects.get(slug='patient/Patient.r'),
            ProtectedCapability.objects.get(slug='patient/Patient.s'),
        ]
        app.scope.add(*scopes)

        self.assertQuerySetEqual(app.scope.all(), scopes, ordered=False)

        call_command('apply_default_scopes')

        default_scopes = ProtectedCapability.objects.filter(default=True)
        self.assertQuerySetEqual(app.scope.all(), default_scopes, ordered=False)

    def test_assigns_when_missing_all_demographic_scopes(self):
        """
        If the app has require_demographic_scopes==True, but is missing all
        demographic scopes in the database, assert that the command adds them for that
        app.
        """
        call_command('create_blue_button_scopes')
        app = self._create_application('an app')
        app.require_demographic_scopes = True
        app.save()
        default_scopes = ProtectedCapability.objects.filter(default=True)
        default_non_demographic_scopes = default_scopes.exclude(slug__in=BENE_PERSONAL_INFO_SCOPES)
        app.scope.add(*default_non_demographic_scopes)

        self.assertQuerySetEqual(app.scope.all(), default_non_demographic_scopes, ordered=False)

        call_command('apply_default_scopes')

        self.assertQuerySetEqual(app.scope.all(), default_scopes, ordered=False)
