from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from .forms import POETJWTForm


@login_required
def generate_poet_jwt(request):

    name = "Create an Application Endorsement"
    if request.method == 'POST':
        form = POETJWTForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                _('Your signed JWT was created.'),
            )
            return render(request, 'jwt.html',
                          {'payload': form.create_payload_json(),
                           'jwt': form.create_jwt()})
        else:
            return render(request, 'generic/bootstrapform.html', {
                          'name': name,
                          'form': form})
    else:
        # this is an HTTP  GET
        return render(request, 'generic/bootstrapform.html', {
                      'name': name,
                      'form': POETJWTForm()})
