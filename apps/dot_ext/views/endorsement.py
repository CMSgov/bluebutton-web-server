#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import *
from ..models import Endorsement, Application

@login_required
@require_GET
def endorsement_list(request, application_id):
    print("here")
    application = get_object_or_404(Application, id=application_id)
    name = "Endorsement List for %s" % application.name
    endorsements = application.endorsements.all()

    return render(request,'endorsements/endorsement_list.html',
                    {'name': name, 'application': application,
                     'endorsements': endorsements})


def all_endorsements(request):
    pass


def add_endorsement(request, application_id):
    pass

def edit_endorsement(request, endorsement_id):
    pass

def delete_endorsement(request, endorsement_id):
    pass