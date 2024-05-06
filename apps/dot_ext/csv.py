import csv

from django.http import HttpResponse


class ExportCsvMixin:
    """Django admin mixin class to allow the addition of an "export_as_csv" action.

    To use, add this class to a model that inherits a Django admin class (eg. admin.ModelAdmin)
    and add "export_as_csv" to the class action list.
    """
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"
