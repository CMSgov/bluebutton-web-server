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

from apps.fhir.bluebutton.utils import get_fhir_now

import csv
import sys
from getenv import env

import logging

logger = logging.getLogger('hhs_server.%s' % __name__)

__author__ = "Mark Scrimshire @ekivemark"


def exportcsv(app_name, model_name, add_name):
    """

    :param app_name:
    :param model_name:
    :return:

    export the CSV for a model, with header line
    """
    model = apps.get_model(app_name, model_name)
    field_names = [f.name for f in model._meta.fields]
    if add_name:
        model_field_names = field_names + [app_name + '.' + model_name,
                                           "model2csv_time"]
        model2csv_time = get_fhir_now()

    else:
        model_field_names = field_names

    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    writer.writerow(model_field_names)

    for instance in model.objects.all():
        output = [str(getattr(instance, f)) for f in field_names]
        if add_name:
            output = output + [app_name + '.' + model_name,
                               model2csv_time]

        writer.writerow(output)

    return True


class Command(BaseCommand):
    help = ("Output the specified model as CSV. model2csv {app}.{modelname}. "
            "\n    export DJANGO_MODEL2CSV=add_table_name "
            "to add app.table name "
            "to output")
    args = '[appname.ModelName]'

    def handle(self, *app_labels, **options):
        if app_labels:

            app_name, model_name = app_labels[0].split('.')

            add_table_name = env("DJANGO_MODEL2CSV", "")
            add_table_name = add_table_name.lower()
            if add_table_name == "add_table_name":
                add_name = True
            else:
                add_name = False
            e = exportcsv(app_name, model_name, add_name)

            if e:
                logger.info('Model Content exported: %s.%s' % (app_name,
                                                               model_name))
        else:
            logger.info('Model Content: Problem with export')

            return False
