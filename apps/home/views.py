from django.utils.translation import ugettext_lazy as _
from oauth2_provider.models import get_application_model
from django.views.generic.base import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.safestring import mark_safe

from ..accounts.models import UserProfile


Application = get_application_model()


class HomeView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/home')
        return super().get(request, *args, **kwargs)


class AuthenticatedHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'authenticated-home.html'

    def get_context_data(self, **kwargs):
        request = self.request
        name = _('Authenticated Home')
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = None

        # Implicit flow depreication warning message per BB2-554
        messages.warning(self.request, mark_safe("ANNOUNCEMENT: The Implicit Auth Flow is being deprecated and should"
                                                 " not be used for development. More information "
                                                 "<a href='https://groups.google.com/g/developer-group-"
                                                 "for-cms-blue-button-api/c/PFfVNymltfE/m/XsRMaQXXCAAJ'>here.</a>"))

        # this is a GET
        context = {
            'name': name,
            'profile': profile,
            'applications': Application.objects.filter(user=request.user),
        }
        return context
