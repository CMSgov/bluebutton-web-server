from django.core.management.base import BaseCommand
from apps.authorization.models import DataAccessGrant
from apps.dot_ext.models import Application


class Command(BaseCommand):
    help = (
        'Update Access Grants Per Application.'
        'Pass in a list of application ids.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--applications', help="List of applications to update "
                                                    "id, comma separated: "
                                                    "eg. 1,2,3. Supersedes --all")
        parser.add_argument('--all', action='store_true', help="Update access grants for all applications")
        parser.set_defaults(all=False)

    def handle(self, *args, **options):
        if options['applications']:
            application_ids = options['applications'].split(',')
        elif options['all']:
            application_ids = Application.objects.values_list('id', flat=True)
        else:
            print("You must pass at least one application to update or use the --all option.")
            return False
        for app_id in application_ids:
            application = Application.objects.get(id=app_id)
            grants = DataAccessGrant.objects.filter(application=app_id)
            if not grants:
                continue
            if "ONE_TIME" in application.data_access_type:
                grants.delete()
            elif "THIRTEEN_MONTH" in application.data_access_type:
                for grant in grants:
                    if grant.expiration_date is None:
                        # only update if the expiration_date does not have a value yet (avoid potential over writing)
                        grant.update_expiration_date()
            else:
                continue
