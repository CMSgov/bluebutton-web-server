from django.core.management import call_command

from apps.test import BaseApiTest


class ApplyDefaultScopesTest(BaseApiTest):
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
