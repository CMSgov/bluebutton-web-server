import logging
from django.shortcuts import render
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..end_user_signup_forms import (SimpleUserSignupForm)
from .core import pick_reverse_login
from ratelimit.decorators import ratelimit
from django.views.decorators.cache import never_cache
logger = logging.getLogger('hhs_server.%s' % __name__)


@never_cache
@ratelimit(key='user_or_ip', rate='5/m', method=['POST'], block=True)
@ratelimit(key='post:username', rate='5/m', method=['POST'], block=True)
def create_end_user_account(request):

    name = "Let's get Started!"

    if request.method == 'POST':
        form = SimpleUserSignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,
                             _("Your account was created. Please "
                               "check your email to verify your account."))
            return pick_reverse_login()
        else:
            # return the bound form with errors
            return render(request,
                          'generic/bootstrapform.html',
                          {'name': name, 'form': form})
    else:
        # this is an HTTP  GET
        # Adding ability to pre-fill invitation_code and email
        # via GET parameters
        form_data = {'invitation_code': request.GET.get('invitation_code', ''),
                     'email': request.GET.get('email', '')}
        messages.info(request,
                      _("An invitation code is required to register."))
        return render(request,
                      'generic/bootstrapform.html',
                      {'name': name, 'form': SimpleUserSignupForm(initial=form_data)})
