from __future__ import absolute_import
from __future__ import unicode_literals
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

logger = logging.getLogger('hhs_server.%s' % __name__)

__author__ = "Alan Viars"




def send_access_token_notifcation(token):
    plaintext = get_template('email-access-token-granted.txt')
    htmly = get_template('email-access-token-granted.html')
    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "APP_NAME": token.application.name,
               "HOSTNAME": get_hostname()
               }
    subject = '[%s] You just granted access to %s' % (settings.APPLICATION_TITLE,
                                            token.application.name)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = token.user.email
    text_content = plaintext.render(context)
    html_content = htmly.render(context)
    msg = EmailMultiAlternatives(
        subject, text_content, from_email, [
            to_email, ])
    msg.attach_alternative(html_content, "text/html")
    msg.send()





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
