from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET

from ..forms import EndorsementForm
from ..models import Endorsement, Application


@login_required
@require_GET
def endorsement_list(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)
    name = "Endorsement List for %s" % application.name
    endorsements = application.endorsements.all()

    return render(request, 'endorsements/endorsement_list.html', {
        'name': name,
        'application': application,
        'endorsements': endorsements
    })


@login_required
def add_endorsement(request, application_id):
    application = get_object_or_404(Application, id=application_id, user=request.user)

    name = 'Add Endorsement to %s' % (application.name)
    if request.method == 'POST':
        form = EndorsementForm(request.POST)
        if form.is_valid():
            e = form.save()
            application.endorsements.add(e)
            application.save()
            messages.success(request, _('The endorsement was added.'))
            return HttpResponseRedirect(reverse('endorsement_list', args=(application.id,)))
        else:
            return render(request, 'generic/bootstrapform.html', {'name': name, 'form': form})
    else:
        # this is an HTTP  GET
        return render(request, 'generic/bootstrapform.html',
                      {'name': name, 'form': EndorsementForm()})


@login_required
def edit_endorsement(request, application_id, endorsement_id):
    application = get_object_or_404(Application, id=application_id,
                                    user=request.user)
    e = get_object_or_404(Endorsement, id=endorsement_id)
    name = 'Add Endorsement %s to %s' % (e.title, application.name)
    if request.method == 'POST':
        form = EndorsementForm(request.POST, instance=e)
        if form.is_valid():
            e = form.save()
            messages.success(request, _("The endorsement was edited."))
            return HttpResponseRedirect(reverse('endorsement_list', args=(application.id,)))
        else:
            return render(request, 'generic/bootstrapform.html', {'name': name, 'form': form})
    else:
        # this is an HTTP  GET
        return render(request, 'generic/bootstrapform.html',
                      {'name': name, 'form': EndorsementForm(instance=e)})


@login_required
@require_GET
def delete_endorsement(request, application_id, endorsement_id):
    application = get_object_or_404(Application, id=application_id,
                                    user=request.user)
    e = get_object_or_404(Endorsement, id=endorsement_id)
    e.delete()
    messages.success(request, _('The endorsement was deleted.'))
    return HttpResponseRedirect(reverse('endorsement_list', args=(application.id,)))


def view_endorsement_payload(request, endorsement_id):
    e = get_object_or_404(Endorsement, id=endorsement_id)
    return JsonResponse(e.payload())
