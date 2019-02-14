import logging
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import EndUserRegisterForm

logger = logging.getLogger('hhs_server.%s' % __name__)


def user_code_register(request):
    if request.method == 'POST':
        form = EndUserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.info(
                request, _('Please check your email for a link to complete registration.'))
            return HttpResponseRedirect(reverse('home'))

        else:
            return render(request, 'user-code-login.html', {'form': form})
    # this is a GET
    initial = {"username": request.GET.get('username'),
               "code": request.GET.get('code')}
    return render(request, 'user-code-login.html',
                  {'form': EndUserRegisterForm(initial=initial)})
