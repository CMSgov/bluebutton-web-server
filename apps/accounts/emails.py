import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


def send_password_reset_url_via_email(user, reset_key):
    if settings.SEND_EMAIL:
        subject = '[%s]Your password ' \
                  'reset request' % (settings.ORGANIZATION_NAME)
        from_email = settings.EMAIL_HOST_USER
        to = user.email
        link = '%s%s' % (settings.HOSTNAME_URL,
                         reverse('password_reset_email_verify',
                                 args=(reset_key,)))
        html_content = """'
        <P>
        Click on the link to reset your password.<br>
        <a href='%s'> %s</a>
        </p>
        <p>
        Thank you,
        </p>
        <p>
        The Team

        </P>
        """ % (link, link)

        text_content = """
        Click on the link to reset your password.
        %s


        Thank you,

        The Team

        """ % (link)
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, 'text/html')
        msg.send()


def send_activation_key_via_email(user, signup_key):
    """Do not call this directly.  Instead use create_signup_key in utils."""
    subject = '[%s]Verify your email.' % (settings.ORGANIZATION_NAME)
    from_email = settings.EMAIL_HOST_USER
    to = user.email
    activation_link = '%s%s' % (settings.HOSTNAME_URL,
                                reverse('activation_verify',
                                        args=(signup_key,)))

    html_content = """
       <p>
       Hello %s. Please click the link to activate your account.<br>
       <a href=%s a> %s</a><br>

       Thank you,<br>

       The Team
       </p>
       """ % (user.first_name, activation_link, activation_link)

    text_content = """
       Hello %s. Please click the link to activate your account.

        %s

       Thank you,

       The Team

       """ % (user.first_name, activation_link)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def send_invite_request_notices(invite_request):
    subject = '[%s]Invitation Request Received' % (settings.ORGANIZATION_NAME)
    from_email = settings.EMAIL_HOST_USER
    to = invite_request.email

    html_content = """
    <p>
    Hello: %s %s,
    </p>
    <p>
    Your request for an invite to the OAuth2 Server (%s) has been received.
    </p>
    <p>
    Thank You,
    </p>
    <p>
    The Team
    </p>
    """ % (invite_request.first_name,
           invite_request.last_name,
           settings.HOSTNAME_URL, )

    text_content = """Hello: %s %s,
    Your request for an invite to OAuth2 Server (%s) has been received.
    """ % (invite_request.first_name,
           invite_request.last_name,
           settings.HOSTNAME_URL)
    msg = EmailMultiAlternatives(subject, text_content, from_email,
                                 [to, settings.INVITE_REQUEST_ADMIN])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()
