from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import BulkUserCodeForm
from ..models import UserRegisterCode
import csv


@login_required
def bulk_user_codes(request):

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
    # this is a GET
    return render(request, 'generic/bootstrapform.html',
                  {'form': BulkUserCodeForm()})
