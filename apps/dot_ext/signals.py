import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver
from oauth2_provider.models import get_access_token_model, get_application_model

from apps.constants import HHS_SERVER_LOGNAME_FMT
from apps.dot_ext.models import AccessTokenExtension, ArchivedToken
from libs.decorators import waffle_function_switch
from libs.mail import Mailer

Application = get_application_model()
AccessToken = get_access_token_model()

logger = logging.getLogger(HHS_SERVER_LOGNAME_FMT.format(__name__))


beneficiary_authorized_application = Signal()


@waffle_function_switch('outreach_email')
def outreach_first_application(sender, instance=None, created=False, **kwargs):
    """
    On an application post_save signal, check to see if this is the first app created
    by the developer. If so, send an email.
    """
    if created:
        try:
            if Application.objects.filter(user=instance.user).count() == 1:
                mailer = Mailer(
                    subject='Congrats on Registering Your First Application!',
                    template_text='email/email-success-first-app-template.txt',
                    template_html='email/email-success-first-app-template.html',
                    to=[
                        instance.user.email,
                    ],
                    context={'FIRST_NAME': instance.user.first_name},
                )
                mailer.send()
                logger.info(
                    'Congrats on Registering Your First Application sent to %s (%s)'
                    % (instance.user.username, instance.user.email)
                )
        except:  # noqa
            logger.error(
                'Congrats on Registering Your First Application failed send to %s (%s)'
                % (instance.user.username, instance.user.email)
            )


@waffle_function_switch('outreach_email')
def outreach_first_api_call(sender, instance=None, **kwargs):
    try:
        if instance.application.first_active is not None:
            return

        if AccessToken.objects.filter(application=instance.application).exists():
            return

        if ArchivedToken.objects.filter(application=instance.application).exists():
            return

        if Application.objects.filter(user=instance.application.user).count() != 1:
            return

        mailer = Mailer(
            subject='Congrats on Making Your First API Call',
            template_text='email/email-success-first-api-call-template.txt',
            template_html='email/email-success-first-api-call-template.html',
            to=[
                instance.application.user.email,
            ],
            context={'FIRST_NAME': instance.application.user.first_name},
        )
        mailer.send()
        logger.info(
            'Congrats on Making Your First API Call sent to %s (%s)'
            % (instance.application.user.username, instance.application.user.email)
        )
    except:  # noqa
        logger.error(
            'Making Your First API Call Application failed send to %s (%s)'
            % (instance.application.user.username, instance.application.user.email)
        )


post_save.connect(outreach_first_application, sender=Application)
pre_save.connect(outreach_first_api_call, sender=AccessToken)


@receiver(post_save, sender=AccessToken)
def create_access_token_extension(sender, instance, created, **kwargs):
    # TODO: Need to update to take into account what was passed for include_samhsa
    # Once the checkbox is in place on v3 permissions screen
    print('sender: ', sender.__dict__)
    print('instance: ', instance)
    print('created: ', created)
    print('kwargs: ', kwargs)
    if created:
        AccessTokenExtension.objects.create(
            access_token=instance,
            include_samhsa=True,
        )
