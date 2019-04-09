import logging
from django.db.models.signals import post_save
from oauth2_provider.models import get_application_model
from apps.accounts.emails import Mailer


Application = get_application_model()
logger = logging.getLogger('hhs_server.%s' % __name__)


def check_first_application(sender, instance=None, created=False, **kwargs):
    """
    On an application post_save signal, check to see if this is the first app created
    by the developer. If so, send an email.
    """
    if created:
        if Application.objects.filter(user=instance.user).count() == 1:
            mailer = Mailer(subject='Congrats on Registering Your First Application!',
                            template_text='email-success-first-app-template.txt',
                            template_html='email-success-first-app-template.html',
                            to=[instance.user.email, ],
                            context={
                                "FIRST_NAME": instance.user.first_name,
                                })
        mailer.send()
        logger.info("Congrats on Registering Your First Application sent to {} ({})".format(instance.user.username,
                                                                                            instance.user.email))


post_save.connect(check_first_application, sender='dot_ext.Application')
