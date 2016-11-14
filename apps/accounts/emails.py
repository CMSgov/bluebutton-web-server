import random
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


""" Found a bug in EmailMultiAlternatives
    A spurious "None" / None was being added in the __init__
    I copied the message.py code to hhs_oauth_server
    and added a patch to check for "None" or None
    and remove it from the list.

"""


def random_secret(y=40):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz'
                                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                                 '0123456789') for x in range(y))


def send_invite_to_create_account(invitation):
    plaintext = get_template('email-invite.txt')
    htmly = get_template('email-invite.html')
    context = {"APPLICATION_TITLE": settings.APPLICATION_TITLE,
               "CODE": invitation.code,
               "URL": invitation.url(),
               }

    subject = '[%s] Invitation Code: %s' % (settings.ORGANIZATION_NAME,
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
               "URL": user_code_invitation.url()}
    subject = '[%s] Invitation Code: %s' % (settings.ORGANIZATION_NAME,
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
    The Team

    </P>
    """ % (code)

    text_content = """
    Provide this code on the authentication screen in your browser:
    %s

    Thank you,

    The Team

    """ % (code)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def send_password_reset_url_via_email(user, reset_key):
    if settings.SEND_EMAIL:
        subject = '[%s]Your password ' \
                  'reset request' % (settings.ORGANIZATION_NAME)
        from_email = settings.DEFAULT_FROM_EMAIL
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
    from_email = settings.DEFAULT_FROM_EMAIL
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
    Please be patient. We will email you  when your invitation coe is ready.  Please be patient.
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
           settings.HOSTNAME_URL,
           u_type,
           settings.ORGANIZATION_NAME)

    text_content = """Hello: %s %s,
    Your request for an invite to %s (%s) has been received.
    """ % (invite_request.first_name,
           invite_request.last_name,
           settings.ORGANIZATION_NAME,
           settings.HOSTNAME_URL)
    msg = EmailMultiAlternatives(subject, text_content, from_email,
                                 [to, settings.INVITE_REQUEST_ADMIN])
    msg.attach_alternative(html_content, 'text/html')

    # print("\n\nMESSAGE EMAIL - INVITE REQUEST: %s / %s" % (to, msg.to))

    msg.send()
