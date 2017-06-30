from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ratelimit.decorators import ratelimit
from ..forms import BulkUserCodeForm
from ..models import UserRegisterCode, UserProfile
import csv
from django.views.decorators.cache import never_cache


@never_cache
@login_required
@ratelimit(key='user_or_ip', rate='2/m', method=['POST'], block=True)
def bulk_user_codes(request):

    # id,first_name,last_name,email,username,code
    # 999999999,Mark,Scrimshire,ekivemark@gmail.com,marks,code1234
    # 888888888,Alan,Viars,alan.viars@videntity.com,acv,code2345

    if request.method == 'POST':
        form = BulkUserCodeForm(request.POST)
        if form.is_valid():
            csv_text = form.cleaned_data['csv_text']
            dreader = csv.DictReader(str.splitlines(str(csv_text)))
            for row in dreader:
                urc = UserRegisterCode(sender=request.user, **row)
                urc.save()
            messages.success(request, _('User signup codes created.'))
            return HttpResponseRedirect(reverse('bulk_user_codes'))

        else:
            return render(request, 'generic/bootstrapform.html',
                          {'form': form})

    up = UserProfile.objects.get(user=request.user)
    messages.info(
        request, _(
            'You have %s remaining user invites.' %
            (up.remaining_user_invites)))
    # this is a GET
    return render(request, 'generic/bootstrapform.html',
                  {'form': BulkUserCodeForm()})
