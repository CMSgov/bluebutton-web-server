from django.core.management.base import BaseCommand
from apps.dot_ext.models import Application

class Command(BaseCommand):
    help = (
        'Change all applications\' data access type to 13 month.' 
    )

    def handle(self, *args, **options):
        applications = Application.objects.all()
        for app in applications:
            if app.data_access_type != "THIRTEEN_MONTH":
                app.data_access_type = "THIRTEEN_MONTH"
                app.save() # logging in model will log the change
