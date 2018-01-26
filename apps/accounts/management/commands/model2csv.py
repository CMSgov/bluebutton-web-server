#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

"""
Project: bluebutton-web-server
App: hhs_oauth_server/management
FILE: model2csv
Created: 1/26/18 12:39 AM

Created by: '@ekivemark'

Prints CSV of all fields of a model.
"""
from django.core.management.base import BaseCommand
from django.apps import apps

import csv
import sys

import logging

logger = logging.getLogger('hhs_server.%s' % __name__)

__author__ = "Mark Scrimshire @ekivemark"


def exportcsv(app_name, model_name):
    """

    :param app_name:
    :param model_name:
    :return:

    export the CSV for a model, with header line
    """
    model = apps.get_model(app_name, model_name)
    field_names = [f.name for f in model._meta.fields]

    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    writer.writerow(field_names)

    for instance in model.objects.all():
        writer.writerow([str(getattr(instance, f)).encode('utf-8') for f in field_names])

    return True


class Command(BaseCommand):
    help = ("Output the specified model as CSV. model2csv {app}.{modelname}")
    args = '[appname.ModelName]'

    def handle(self, *app_labels, **options):
        if app_labels:

            app_name, model_name = app_labels[0].split('.')
            e = exportcsv(app_name, model_name)

            if e:
                logger.info('Model Content exported: %s.%s' % (app_name,
                                                               model_name))
        else:
            logger.info('Model Content: Problem with export')

            return False
