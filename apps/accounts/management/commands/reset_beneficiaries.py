import sys
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

logger = logging.getLogger('hhs_server.%s' % __name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Reset all beneficiary accounts in the system."

    def handle(self, *args, **options):
        bene_records_query = User.objects.filter(userprofile__user_type='BEN')
        sys.stdout.write(
            '{} beneficiary accounts to remove\n'.format(bene_records_query.count()))
        if not boolean_input("Continue? (this will delete records) "):
            sys.stdout.write("bye")
            return

        successes = 0
        failures = 0

        for bene in bene_records_query.all():
            try:
                bene.delete()
                successes += 1
                sys.stdout.write("bene {} removed\n".format(bene.username))
                logger.info({
                    "msg": "removed bene records",
                    "beneficiary": {
                        "username": bene.username,
                    },
                })
            except Exception as e:
                failures += 1
                logger.info({
                    "msg": "failed to remove bene records",
                    "beneficiary": {
                        "id": bene.username,
                    },
                    "exception": str(e),
                })
                sys.stdout.write(str(e))
                sys.stdout.write("\n")

        sys.stdout.write(
            '{} beneficiary accounts removed. {} failed.'.format(successes, failures))


def boolean_input(question, default=None):
    result = input("%s [y\\n]\n" % question)
    if not result and default is not None:
        return default
    while len(result) < 1 or result[0].lower() not in "yn":
        result = input("Please answer yes or no: ")
    return result[0].lower() == "y"
