import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template


logger = logging.getLogger('hhs_server.%s' % __name__)


class Mailer(EmailMultiAlternatives):
    """ Custom mailer class """
    from_email = settings.DEFAULT_FROM_EMAIL

    def __init__(self, subject='', template_text='', template_html='',
                 from_email=None, to=None, bcc=None, connection=None,
                 attachments=None, headers=None, alternatives=None,
                 cc=None, reply_to=None, context=None):

        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        text_content = get_template(template_text).render(context)
        html_content = get_template(template_html).render(context)

        super().__init__(subject=subject, body=text_content, from_email=from_email, to=to, bcc=bcc,
                         connection=connection, attachments=attachments, headers=headers,
                         alternatives=alternatives, cc=cc, reply_to=reply_to)
        super().attach_alternative(html_content, "text/html")
