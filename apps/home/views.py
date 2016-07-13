from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from ..accounts.models import UserProfile


def authenticated_home(request):
    if request.user.is_authenticated():
        name = _('Authenticated Home')
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = None

        # this is a GET
        context = {'name': name, 'profile': profile}
        template = 'authenticated-home.html'
    else:
        name = ('home')
        context = {'name': name}
        template = 'index.html'
    return render(request, template, context)
