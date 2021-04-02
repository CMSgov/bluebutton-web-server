from django.utils.translation import ugettext_lazy as _
from ..accounts.models import UserProfile
from oauth2_provider.models import get_application_model
from django.views.generic.base import TemplateView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

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

        # this is a GET
        context = {
            'name': name,
            'profile': profile,
            'applications': Application.objects.filter(user=request.user),
        }
        return context
