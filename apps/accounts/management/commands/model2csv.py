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

import logging

logger = logging.getLogger('hhs_server.%s' % __name__)


def exportcsv(app_name, model_name, add_name, field_export):
    """

    :param app_name:
    :param model_name:
    :param add_name:
    :return:

    export the CSV for a model, with header line
    """
    model = apps.get_model(app_name, model_name)
    field_list = [f.name for f in model._meta.fields]
    if field_export:
        field_names = []
        for fe in field_export:
            if fe in field_list:
                field_names.append(fe)
    else:
        field_names = field_list

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

    help = ("Output the specified application.model as CSV")

    def add_arguments(self, parser):
        parser.add_argument('--application', help="application name")

        parser.add_argument('--model', help="model name")

        parser.add_argument('--add_table_name', help="include table name"
                                                     " and export time as "
                                                     "columns: True | False")

        parser.add_argument('--filter_fields', help="filter fields by column "
                                                    "name, comma separated: "
                                                    "eg. id,name,description ")

    def handle(self, *app_labels, **options):

        if options['application']:
            app_name = options['application']
        else:
            logger.info('model2csv: No application defined')
            return False

        if options['model']:
            model_name = options['model']
        else:
            logger.info('model2csv: No model defined')
            return False

        if options['add_table_name']:
            if options['add_table_name'].lower() == "true":
                add_name = True
            else:
                add_name = False
        else:
            add_name = False

        if options['filter_fields']:
            field_export = options['filter_fields'].split(',')
        else:
            field_export = []

        e = exportcsv(app_name, model_name, add_name, field_export)

        if e:
            logger.info('model2csv: Content exported: %s.%s' % (app_name,
                                                                model_name))
            return
        else:
            logger.info('model2csv: Problem with export')

        return False
