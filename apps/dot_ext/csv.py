import csv

from django.http import HttpResponse


class ExportCsvMixin:
    """Django admin mixin class to allow the addition of an "export_as_csv" action.

    To use, add this class to a model that inherits a Django admin class (eg. admin.ModelAdmin)
    and add "export_as_csv" to the class action list.
    """
    def export_as_csv(self, request, queryset):

        def get_value(obj, key):
            if key == "internal_application_labels":
                return getattr(obj, key).all()
            return getattr(obj, key)

        export_fields = self.get_export_fields(None)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(self.model._meta)
        writer = csv.writer(response)

        writer.writerow(export_fields)
        for obj in queryset:
            writer.writerow([get_value(obj, field) for field in export_fields])

        return response

    export_as_csv.short_description = "Export Selected"
