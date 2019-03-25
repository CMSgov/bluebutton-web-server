from django.conf.urls import url
from .views.core import (create_account,
                         account_settings,
                         mylogout,
                         activation_verify,
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
from .views.api_profile import my_profile
from waffle.decorators import waffle_switch


urlpatterns = [
    # login and Logout ------------------------------------
    url(r'^api/profile$', my_profile, name='my_profile'),


    # login and Logout ------------------------------------
    url(r'^logout$', mylogout, name='mylogout'),

    # Simple login is deprecated. mfa_login will work like
    # simple_login when settings.MFA = False or user has
    # MFA disabled.
    url(r'^create$', waffle_switch('signup')(create_account),
        name='accounts_create_account'),

    url(r'^settings$', account_settings, name='account_settings'),

    # MFA URLs ------------------------------------------
    url(r'^mfa/login$', waffle_switch('login')(mfa_login), name='mfa_login'),

    # Confirm MFA ------------------------
    url(r'mfa/confirm/(?P<uid>[^/]+)/', waffle_switch('login')(mfa_code_confirm),
        name='mfa_code_confirm'),


    # Reset password? ---------------------------------------
    url(r'^reset-password$', waffle_switch('login')(reset_password),
        name='reset_password'),


    # Forgot password? ---------------------------------------
    url(r'^forgot-password$', waffle_switch('login')(forgot_password),
        name='forgot_password'),

    url(r'^change-secret-questions$', 
        change_secret_questions,
        name='change_secret_questions'),

    # Change password using reset token ------------------------
    url(r'^password-reset-email-verify/(?P<reset_password_key>[^/]+)/$',
        waffle_switch('login')(password_reset_email_verify),
        name='password_reset_email_verify'),

    # Secret Question Challenge
    url(r'^secret-question-challenge/(?P<username>[^/]+)/$',
        waffle_switch('login')(secret_question_challenge),
        name='secret_question_challenge'),

    url(r'^secret-question-challenge-1/(?P<username>[^/]+)/$',
        waffle_switch('login')(secret_question_challenge_1),
        name='secret_question_challenge_1'),

    url(r'^secret-question-challenge-2/(?P<username>[^/]+)/$',
        waffle_switch('login')(secret_question_challenge_2),
        name='secret_question_challenge_2'),

    url(r'^secret-question-challenge-3/(?P<username>[^/]+)/$',
        waffle_switch('login')(secret_question_challenge_3),
        name='secret_question_challenge_3'),

    # Verify the account
    url(r'^activation-verify/(?P<activation_key>[^/]+)/$', 
        waffle_switch('login')(activation_verify),
        name='activation_verify'),
]
