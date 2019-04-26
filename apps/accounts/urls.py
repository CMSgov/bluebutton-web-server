from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from waffle.decorators import waffle_switch
from .views.api_profile import my_profile
from .views.core import (create_account,
                         account_settings,
                         activation_verify,
                         )
from .views.login import LoginView, PasswordChangeView
from .views.mfa import mfa_code_confirm
from .views.password_reset import (change_secret_questions,
                                   forgot_password,
                                   password_reset_email_verify,
                                   secret_question_challenge,
                                   secret_question_challenge_1,
                                   secret_question_challenge_2,
                                   secret_question_challenge_3)


urlpatterns = [

    url(r'^api/profile$', my_profile, name='my_profile'),

    url(r'^logout$', waffle_switch('login')(LogoutView.as_view()), name='logout'),

    url(r'^create$', waffle_switch('signup')(create_account),
        name='accounts_create_account'),

    url(r'^settings$', account_settings, name='account_settings'),

    url(r'mfa/confirm/(?P<uid>[^/]+)/', waffle_switch('login')(mfa_code_confirm),
        name='mfa_code_confirm'),

    # Handle mfa/login incase there are any extenal links to it.
    url(r'^login$|^mfa/login$', waffle_switch('login')(LoginView.as_view()), name='login'),

    url(r'^password-change$',
        waffle_switch('login')(PasswordChangeView.as_view(
                               template_name='generic/bootstrapform.html',
                               success_url='settings')),
        name='password_change'),








    url(r'^forgot-password$',
        waffle_switch('login')(PasswordResetView.as_view(
                               template_name='registration/password_forgot_form.html',
                               email_template_name='email/email-password-forgot-link.txt',
                               html_email_template_name='email/email-password-forgot-link.html',
                               from_email = settings.DEFAULT_FROM_EMAIL
                               )),
        name='forgot_password'),

    url(r'^password-reset-done$',
        waffle_switch('login')(PasswordResetDoneView.as_view(
                               template_name='registration/password_forgot_reset_done.html')),
        name='password_reset_done'),

    url(r'^password-reset-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        waffle_switch('login')(PasswordResetConfirmView.as_view(
                               template_name='registration/password_forgot_reset_confirm_form.html',
)),
        name='password_reset_confirm'),


    url(r'^password-reset-complete$',
        waffle_switch('login')(PasswordResetCompleteView.as_view()),
        name='password_reset_complete'),





    url(r'^forgot-password-old$', waffle_switch('login')(forgot_password),
        name='forgot_password-old'),

    url(r'^change-secret-questions$',
        change_secret_questions,
        name='change_secret_questions'),

    url(r'^password-reset-email-verify/(?P<reset_password_key>[^/]+)/$',
        waffle_switch('login')(password_reset_email_verify),
        name='password_reset_email_verify'),

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

    url(r'^activation-verify/(?P<activation_key>[^/]+)/$',
        waffle_switch('login')(activation_verify),
        name='activation_verify'),
]
