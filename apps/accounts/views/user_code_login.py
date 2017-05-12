import logging
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import CodeLoginForm
from ..models import UserProfile, UserRegisterCode

logger = logging.getLogger('hhs_server.%s' % __name__)


def user_code_login(request):
    if request.method == 'POST':
        form = CodeLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            code = form.cleaned_data['code']
            user = authenticate(username=username.lower(), password=password)

            # print(user)

            try:
                valid_user_code = UserRegisterCode.objects.get(
                    code=code, username=username)
            except UserRegisterCode.DoesNotExist:
                valid_user_code = None

            if user is not None and valid_user_code is not None:
                valid_user_code.used = True
                valid_user_code.save()
                up = UserProfile.objects.get(user=user)
                up.authorize_applications = True
                up.save()

                messages.info(
                    request, _('You have now registered and can connect applications.'))
                if user.is_active:
                    login(request, user)
                    next_param = request.GET.get('next', '')

                    if next_param:
                        # If a next is in the URL, then go there
                        return HttpResponseRedirect(next_param)
                    # otherwise just go to home.
                    return HttpResponseRedirect(reverse('home'))
                else:
                    # The user exists but is_active=False
                    messages.error(request,
                                   _('Please check your email for a link to '
                                     'activate your account.'))
                    return render(
                        request, 'user-code-login.html', {'form': form})
            else:
                messages.error(
                    request, _('Invalid username, password or signup code.'))
                return render(request, 'user-code-login.html', {'form': form})

        else:
            return render(request, 'user-code-login.html', {'form': form})
    # this is a GET
    initial = {"username": request.GET.get('username'),
               "code": request.GET.get('code')}
    return render(request, 'user-code-login.html',
                  {'form': CodeLoginForm(initial=initial)})
