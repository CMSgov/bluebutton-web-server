from django.conf.urls import url
from axes.decorators import watch_login
from .views.core import (create_developer,
                         create_user,
                         account_settings,
                         reissue_api_keys,
                         request_developer_invite,
                         mylogout,
                         request_user_invite,
                         display_api_keys,
                         activation_verify,
                         # simple_login,
                         )

from .views.password_reset import (change_secret_questions,
                                   forgot_password,
                                   password_reset_email_verify,
                                   secret_question_challenge,
                                   secret_question_challenge_1,
                                   secret_question_challenge_2,
                                   secret_question_challenge_3)

from .views.mfa import mfa_code_confirm, mfa_login

urlpatterns = [
    # login and Logout ------------------------------------
    url(r'^logout$', mylogout, name='mylogout'),
    
    # Simple login is deprecated. mfa_login will work like
    # simple_login when settings.MFA = False or user has
    # MFA disabled.
    # url(r'^login$', watch_login(simple_login), name='login'),
    # create and update account info -----------------------
    url(r'^create-developer$',
        create_developer,
        name='accounts_create_developer'),
    url(r'^create-user$',
        create_user,
        name='accounts_create_user'),
    url(r'^settings$', account_settings, name='account_settings'),

    # MFA URLs ------------------------------------------
    url(r'^mfa/login$', watch_login(mfa_login), name='mfa_login'),
    # Confirm MFA ------------------------
    url(r'mfa/confirm/(?P<uid>[^/]+)/',
        mfa_code_confirm, name='mfa_code_confirm'),


    # Request a Developer invite to signup ---------------------------
    url(r'^request-developer-invite$',
        request_developer_invite,
        name='request_developer_invite'),
    # Request an invite to signup ---------------------------
    url(r'^request-user-invite$', request_user_invite,
        name='request_user_invite'),

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

    url(r'^display-api-keys$', display_api_keys, name='display_api_keys'),

    url(r'^reissue-api-keys$', reissue_api_keys, name='reissue_api_keys'),
]
