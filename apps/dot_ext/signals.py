import logging
from django.db.models.signals import post_save, pre_save
from oauth2_provider.models import get_application_model, get_access_token_model
from libs.mail import Mailer
from .models import ArchivedToken


Application = get_application_model()
Token = get_access_token_model()

logger = logging.getLogger('hhs_server.%s' % __name__)


def outreach_first_application(sender, instance=None, created=False, **kwargs):
    """
    On an application post_save signal, check to see if this is the first app created
    by the developer. If so, send an email.
    """
    if created:
        try:
            if Application.objects.filter(user=instance.user).count() == 1:
                mailer = Mailer(subject='Congrats on Registering Your First Application!',
                                template_text='email/email-success-first-app-template.txt',
                                template_html='email/email-success-first-app-template.html',
                                to=[instance.user.email, ],
                                context={"FIRST_NAME": instance.user.first_name})
                mailer.send()
                logger.info("Congrats on Registering Your First Application sent to %s (%s)" %
                            (instance.user.username, instance.user.email))
        except:  # noqa
            logger.error("Congrats on Registering Your First Application failed send to %s (%s)" %
                         (instance.user.username, instance.user.email))


def outreach_first_api_call(sender, instance=None, **kwargs):
    try:
        if instance.application.first_active is not None:
            return

        if Token.objects.filter(application=instance.application).exists():
            return

        if ArchivedToken.objects.filter(application=instance.application).exists():
            return

        if Application.objects.filter(user=instance.application.user).count() != 1:
            return

        mailer = Mailer(subject='Congrats on Making Your First API Call',
                        template_text='email/email-success-first-api-call-template.txt',
                        template_html='email/email-success-first-api-call-template.html',
                        to=[instance.application.user.email, ],
                        context={"FIRST_NAME": instance.application.user.first_name})
        mailer.send()
        logger.info("Congrats on Making Your First API Call sent to %s (%s)" %
                    (instance.application.user.username, instance.application.user.email))
    except:  # noqa
        logger.error("Making Your First API Call Application failed send to %s (%s)" %
                     (instance.application.user.username, instance.application.user.email))


post_save.connect(outreach_first_application, sender=Application)
pre_save.connect(outreach_first_api_call, sender=Token)
