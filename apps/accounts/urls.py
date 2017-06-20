from django.conf.urls import url
# from axes.decorators import watch_login
from .views.core import (create_account,
                         account_settings,
                         reissue_api_keys,
                         request_invite,
                         mylogout,
                         display_api_keys,
                         activation_verify,
                         # simple_login,
                         )

from .views.password_reset import (change_secret_questions,
                                   forgot_password,
                                   reset_password,
                                   password_reset_email_verify,
                                   secret_question_challenge,
                                   secret_question_challenge_1,
                                   secret_question_challenge_2,
                                   secret_question_challenge_3)

from .views.mfa import mfa_code_confirm, mfa_login
from .views.user_code_login import user_code_register
from .views.invites import bulk_user_codes
from .views.email_bounce_webhook import record_email_bounce
from .views.api_profile import my_profile
from .views.end_user_account_create import create_end_user_account

urlpatterns = [
    # login and Logout ------------------------------------
    url(r'^api/profile$', my_profile, name='my_profile'),


    # login and Logout ------------------------------------
    url(r'^logout$', mylogout, name='mylogout'),

    # Simple login is deprecated. mfa_login will work like
    # simple_login when settings.MFA = False or user has
    # MFA disabled.
    # url(r'^login$', watch_login(simple_login), name='login'),
    # create and update account info -----------------------
    # login and Logout ------------------------------------
    # Disabled for now.
    url(r'^register$', create_end_user_account, name='create_end_user_account'),


    url(r'^create$',
        create_account,
        name='accounts_create_account'),

    url(r'^settings$', account_settings, name='account_settings'),

    # MFA URLs ------------------------------------------
    # url(r'^mfa/login$', watch_login(mfa_login), name='mfa_login'),
    url(r'^mfa/login$', mfa_login, name='mfa_login'),

    url(r'^user-code/register$', user_code_register, name='user_code_register'),


    # Confirm MFA ------------------------
    url(r'mfa/confirm/(?P<uid>[^/]+)/',
        mfa_code_confirm, name='mfa_code_confirm'),


    url(r'^bulk-user-codes$', bulk_user_codes, name='bulk_user_codes'),

    # Request a Developer invite to signup ---------------------------
    url(r'^request-invite$',
        request_invite,
        name='request_invite'),

    # Reset password? ---------------------------------------
    url(r'^reset-password$', reset_password, name='reset_password'),

    # Forgot password? ---------------------------------------
    url(r'^forgot-password$', forgot_password, name='forgot_password'),

    url(r'^change-secret-questions$', change_secret_questions,
        name='change_secret_questions'),

    # Change password using reset token ------------------------
    url(r'^password-reset-email-verify/(?P<reset_password_key>[^/]+)/$',
        password_reset_email_verify,
        name='password_reset_email_verify'),

    # Secret Question Challenge
    url(r'^secret-question-challenge/(?P<username>[^/]+)/$', secret_question_challenge,
        name='secret_question_challenge'),

    url(r'^secret-question-challenge-1/(?P<username>[^/]+)/$', secret_question_challenge_1,
        name='secret_question_challenge_1'),

    url(r'^secret-question-challenge-2/(?P<username>[^/]+)/$', secret_question_challenge_2,
        name='secret_question_challenge_2'),

    url(r'^secret-question-challenge-3/(?P<username>[^/]+)/$', secret_question_challenge_3,
        name='secret_question_challenge_3'),

    # Verify the account
    url(r'^activation-verify/(?P<activation_key>[^/]+)/$', activation_verify,
        name='activation_verify'),

    # Email Bounce Webhook

    url(r'^email-bounce$', record_email_bounce, name='record_email_bounce'),

    url(r'^display-api-keys$', display_api_keys, name='display_api_keys'),

    url(r'^reissue-api-keys$', reissue_api_keys, name='reissue_api_keys'),
]
