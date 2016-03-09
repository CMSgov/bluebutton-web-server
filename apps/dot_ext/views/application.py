from __future__ import absolute_import
from __future__ import unicode_literals

from oauth2_provider import views as oauth2_views

from ..forms import CustomRegisterApplicationForm


class ApplicationRegistration(oauth2_views.ApplicationRegistration):
    """
    View used to register a new Application for the request.user
    """
    def get_form_class(self):
        """
        Returns the form class for the application model
        """
        return CustomRegisterApplicationForm


class ApplicationUpdate(oauth2_views.ApplicationUpdate):
    """
    View used to update an application owned by the request.user
    """
    fields = None
    form_class = CustomRegisterApplicationForm

    def get_form_kwargs(self):
        """
        Add `user` to kwargs because it is required by the constructor of
        CustomRegisterApplicationForm class.
        """
        kwargs = super(ApplicationUpdate, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
