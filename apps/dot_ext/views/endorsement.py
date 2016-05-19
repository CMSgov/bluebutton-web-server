#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from ..forms import *
from ..models import Endorsement, Application

@require_GET
def endorsement_list(request, appliction_id):
    
    application = get_object_or_404(Application, id=appliction_id)
    name = "Endorsement List for %s" % application.title
    endorsements = application.endorsements.all()

    return render(request,'endorsement_list.html',
                    {'name': name, 'endorsements': endorsements})
