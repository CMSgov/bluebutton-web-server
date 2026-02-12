from django.conf import settings


# Enrollment and Identity Proofing. NIST SP 800-63-33 B
# Authenticator Assurance Level
AAL_CHOICES = (
    ('', 'Undefined'),
    ('0', 'AAL0'),
    ('1', 'AAL1'),
    ('2', 'AAL2'),
    ('3', 'AAL3'),
)
ADDITION = 1
ACCT_ACTIVATED_MSG = '''Your account has been activated. You may now login.'''
ACCT_HAS_ISSUE_MSG = '''There may be an issue with your account.
                Contact us at bluebuttonapi@cms.hhs.gov'''
ACCT_MAIL_LOGGER_NAME = 'hhs_server.apps.accounts.emails'
CHANGE = 2
DELETION = 3
DOT_EXT_SIGNAL_LOGGER_NAME = 'hhs_server.apps.dot_ext.signals'
ENCODED = settings.ENCODING

# Enrollment and Identity Proofing. NIST SP 800-63-3 A
# Identity assurance level
IAL_CHOICES = (
    ('', 'Undefined'),
    ('0', 'IAL0'),
    ('1', 'IAL1'),
    ('2', 'IAL2'),
    ('3', 'IAL3'),
)

LINK_EXPIRED_MSG = '''The activation key is expired.
                Contact us at bluebuttonapi@cms.hhs.gov for further assistance'''

# Enrollment and Identity Proofing. NIST SP 800-63-A
# Level of Assurance - Legacy/Deprecated  See NIST SP 800-63-2
LOA_CHOICES = (
    ('', 'Undefined'),
    ('1', 'LOA-1'),
    ('2', 'LOA-2'),
    ('3', 'LOA-3'),
    ('4', 'LOA-4'),
)

LOGIN_MSG_ACTIVATED = 'Your account has been activated. You may now login'

MAIL_SENT_EVENT = 'Activation link sent to testactivation@example.com (testactivation@example.com)'
MAILER_EVENT_LOGGERS = [ACCT_MAIL_LOGGER_NAME, DOT_EXT_SIGNAL_LOGGER_NAME]

QUESTION_1_CHOICES = (
    ('1', 'What is your favorite color?'),
    ('2', 'What is your favorite vegetable?'),
    ('3', 'What is your favorite movie?'),
)

QUESTION_2_CHOICES = (
    ('1', 'What was the name of your best friend from childhood?'),
    ('2', 'What was the name of your elementary school?'),
    ('3', 'What was the name of your favorite pet?'),
)

QUESTION_3_CHOICES = (
    ('1', 'What was the make of your first automobile?'),
    ('2', 'What was your maternal grandmother\'s maiden name?'),
    ('3', 'What was your paternal grandmother\'s maiden name?'),
)

USER_CHOICES = (
    ('BEN', 'Beneficiary'),
    ('DEV', 'Developer'),
)
