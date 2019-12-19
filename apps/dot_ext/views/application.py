from django.urls import reverse_lazy
from oauth2_provider import views as oauth2_views

from ..forms import CustomRegisterApplicationForm


class CustomFormMixin(object):
    def get_form_kwargs(self):
        """
        Add `user` to kwargs because it is required by the constructor of
        CustomRegisterApplicationForm class.
        """
        kwargs = super(CustomFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ApplicationRegistration(CustomFormMixin, oauth2_views.ApplicationRegistration):
    """
    View used to register a new Application for the request.user
    """
    def get_form_class(self):
        """
        Returns the form class for the application model
        """
        return CustomRegisterApplicationForm


class ApplicationUpdate(CustomFormMixin, oauth2_views.ApplicationUpdate):
    """
    View used to update an application owned by the request.user
    """
    fields = None

    def get_form_class(self):
        """
        Returns the form class for the application model
        """
        return CustomRegisterApplicationForm


class ApplicationDelete(oauth2_views.ApplicationDelete):

    success_url = reverse_lazy("home")
