import random
import logging
from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from libs.decorators import waffle_function_switch
from libs.mail import Mailer


logger = logging.getLogger('hhs_server.%s' % __name__)


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


@waffle_function_switch('outreach_email')
def send_activation_key_via_email(user, signup_key):
    """ Send an email with activation key and welcome message. """
    activation_link = '%s%s' % (get_hostname(),
                                reverse('activation_verify',
                                        args=(signup_key,)))
    mailer = Mailer(subject='Verify Your Blue Button 2.0 Developer Sandbox Account',
                    template_text='email/email-activate.txt',
                    template_html='email/email-activate.html',
                    to=[user.email, ],
                    context={"ACTIVATION_LINK": activation_link})
    mailer.send()
    logger.info("Activation link sent to {} ({})".format(user.username, user.email))


def get_hostname():
    hostname = getattr(settings, 'HOSTNAME_URL', 'http://localhost:8000')

    if "http://" in hostname.lower():
        pass
    elif "https://" in hostname.lower():
        pass
    else:
        logger.debug("HOSTNAME_URL [%s] "
                     "does not contain http or https prefix. "
                     "Issuer:%s" % (settings.HOSTNAME_URL, hostname))
        # no http/https prefix in HOST_NAME_URL so we add it
        hostname = "https://%s" % (hostname)
    return hostname
