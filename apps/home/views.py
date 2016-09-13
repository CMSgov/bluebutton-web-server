from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from ..accounts.models import UserProfile
from ..fhir.bluebutton.models import Crosswalk


def authenticated_home(request):
    if request.user.is_authenticated():
        name = _('Authenticated Home')
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = None
        try:
            crosswalk = Crosswalk.objects.get(user=request.user)
        except Crosswalk.DoesNotExist:
            crosswalk = None

        # this is a GET
        context = {'name': name, 'profile': profile,
                   'crosswalk': crosswalk}
        template = 'authenticated-home.html'
    else:
        name = ('home')
        context = {'name': name}
        template = 'index.html'
    return render(request, template, context)
