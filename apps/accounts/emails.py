import random
import logging
from django.conf import settings
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

logger = logging.getLogger('hhs_server.%s' % __name__)


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


def notify_admin_of_invite_request(request_invite):
    plaintext = get_template('email-invite-request-received.txt')
    htmly = get_template('email-invite-request-received.html')
    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "EMAIL": request_invite.email,
               "FIRST_NAME": request_invite.first_name,
               "LAST_NAME": request_invite.last_name,
               "USER_TYPE": request_invite.user_type
               }
    subject = '[%s] Request for %s access from : %s %s' % (settings.APPLICATION_TITLE,
                                                           request_invite.user_type,
                                                           request_invite.first_name,
                                                           request_invite.last_name)
    from_email = settings.DEFAULT_FROM_EMAIL
    if settings.DEFAULT_FROM_EMAIL == settings.DEFAULT_ADMIN_EMAIL:
        to_email = [settings.DEFAULT_ADMIN_EMAIL]
    else:
        to_email = [settings.DEFAULT_ADMIN_EMAIL, settings.DEFAULT_FROM_EMAIL]
    text_content = plaintext.render(context)
    html_content = htmly.render(context)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_invite_to_create_account(invitation):
    plaintext = get_template('email-invite.txt')
    htmly = get_template('email-invite.html')
    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "CODE": invitation.code,
               "URL": invitation.url(),
               "EMAIL": invitation.email,
               }

    subject = '[%s] Invitation Code: %s' % (settings.APPLICATION_TITLE,
                                            invitation.code)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = invitation.email
    text_content = plaintext.render(context)
    html_content = htmly.render(context)
    msg = EmailMultiAlternatives(
        subject, text_content, from_email, [
            to_email, ])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_invitation_code_to_user(user_code_invitation):
    plaintext = get_template('email-user-code-by-email.txt')
    htmly = get_template('email-user-code-by-email.html')
    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "CODE": user_code_invitation.code,
               "URL": user_code_invitation.url(),
               "EMAIL": user_code_invitation.email}
    subject = '[%s] Invitation Code: %s' % (settings.APPLICATION_TITLE,
                                            user_code_invitation.code)
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user_code_invitation.email
    text_content = plaintext.render(context)
    html_content = htmly.render(context)
    msg = EmailMultiAlternatives(
        subject, text_content, from_email, [
            to_email, ])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


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


def send_invite_request_notices(invite_request):
    subject = '[%s] Invitation Request Received' % (settings.ORGANIZATION_NAME)
    from_email = settings.DEFAULT_FROM_EMAIL
    to = invite_request.email
    if invite_request.user_type == "DEV":
        u_type = "<p>Thank you for your application to join the %s " \
                 "Developer Community.</p>" % settings.ORGANIZATION_NAME
    else:
        u_type = "<p>Welcome to the %s " \
                 "Community. We are excited to help you connect " \
                 "your Medicare information with a growing library of " \
                 "health applications.</p>" % settings.ORGANIZATION_NAME

    html_content = """
    <p>
    Hello: %s %s,
    </p>
    <p>
    Your request for an invite to the %s (%s) has been received.
    </p>
    %s
    <p>
    We will email you when your invitation code is ready.
    Please be patient.
    </p>
    <p>
    Thank You,
    </p>
    <p>
    The %s Team
    </p>
    """ % (invite_request.first_name,
           invite_request.last_name,
           settings.ORGANIZATION_NAME,
           get_hostname(),
           u_type,
           settings.ORGANIZATION_NAME)

    text_content = """Hello: %s %s,
    Your request for an invite to %s (%s) has been received.
    """ % (invite_request.first_name,
           invite_request.last_name,
           settings.ORGANIZATION_NAME,
           get_hostname())
    msg = EmailMultiAlternatives(subject, text_content, from_email,
                                 [to, settings.INVITE_REQUEST_ADMIN])
    msg.attach_alternative(html_content, 'text/html')

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
