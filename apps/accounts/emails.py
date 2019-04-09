import random
import logging
from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

logger = logging.getLogger('hhs_server.%s' % __name__)


#  New mailer class???
class Mailer(EmailMultiAlternatives):
    """ Custom mailer class """
    template_top_html = "mailer-top.html"
    template_top_text = "mailer-top.txt"
    template_bottom_html = "mailer-bottom.html"
    template_bottom_text = "mailer-bottom.txt"
    # NOTE: top/bottom templates not implemented yet!
    from_email = settings.DEFAULT_FROM_EMAIL

    def __init__(self, subject='', template_text='', template_html='',
                 template_top_html=None, template_top_text=None,
                 template_bottom_html=None, template_bottom_text=None,
                 from_email=None, to=None, bcc=None, connection=None,
                 attachments=None, headers=None, alternatives=None,
                 cc=None, reply_to=None, context=None):

        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        text_content = get_template(template_text).render(context)
        html_content = get_template(template_html).render(context)

        super().__init__(subject, text_content, from_email, to, bcc,
                         connection, attachments, headers, alternatives,
                         cc, reply_to)
        super().attach_alternative(html_content, "text/html")


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


def mfa_via_email(user, code):

    subject = '[%s] Your code for access to' % (settings.APPLICATION_TITLE)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = user.email

    html_content = """'
    <P>
    Provide this code on the authentication screen in your browser:<br>
     %s
    </p>
    <p>
    Thank you,
    </p>
    <p>
    The %s Team

    </P>
    """ % (code, settings.APPLICATION_TITLE)

    text_content = """
    Provide this code on the authentication screen in your browser:
    %s

    Thank you,

    The %s Team

    """ % (code, settings.APPLICATION_TITLE)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def send_password_reset_url_via_email(user, reset_key):
    plaintext = get_template('email-password-reset-link.txt')
    htmly = get_template('email-password-reset-link.html')
    subject = '[%s] Link to reset your password' % (settings.APPLICATION_TITLE)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    password_reset_link = '%s%s' % (get_hostname(),
                                    reverse('password_reset_email_verify',
                                            args=(reset_key,)))

    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "FIRST_NAME": user.first_name,
               "LAST_NAME": user.last_name,
               "PASSWORD_RESET_LINK": password_reset_link}
    text_content = plaintext.render(context)
    html_content = htmly.render(context)
    msg = EmailMultiAlternatives(
        subject, text_content, from_email, [
            to_email, ])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_activation_key_via_email(user, signup_key):
    """Do not call this directly.  Instead use create_signup_key in utils."""
    plaintext = get_template('email-activate.txt')
    htmly = get_template('email-activate.html')
    subject = '[%s] Verify your email to complete account signup' % (
        settings.APPLICATION_TITLE)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    activation_link = '%s%s' % (get_hostname(),
                                reverse('activation_verify',
                                        args=(signup_key,)))
    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "FIRST_NAME": user.first_name,
               "LAST_NAME": user.last_name,
               "ACTIVATION_LINK": activation_link}
    subject = '[%s] Verify your email to complete your account setup.' % (
        settings.APPLICATION_TITLE)
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
