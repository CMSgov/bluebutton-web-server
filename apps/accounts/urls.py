from django.conf import settings
from django.urls import path, re_path
from django.contrib.auth.views import (
    LogoutView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from waffle.decorators import waffle_switch
from .views.api_profile import my_profile
from .views.core import create_account, account_settings, activation_verify
from .views.login import LoginView, PasswordChangeView


urlpatterns = [
    path("api/profile", my_profile, name="my_profile"),
    path("logout", waffle_switch("login")(LogoutView.as_view()), name="logout"),
    path(
        "create",
        waffle_switch("signup")(create_account),
        name="accounts_create_account",
    ),
    path("settings", account_settings, name="account_settings"),
    re_path(
        r"^login$|^mfa/login$",
        waffle_switch("login")(LoginView.as_view()),
        name="login",
    ),
    path(
        "password-change",
        waffle_switch("login")(
            PasswordChangeView.as_view(
                template_name="registration/passwd_change_form.html",
                success_url="settings",
            )
        ),
        name="password_change",
    ),
    path(
        "expired-password-change",
        waffle_switch("login")(
            PasswordChangeView.as_view(
                template_name="registration/passwd_change_form.html",
                success_url="settings",
            )
        ),
        name="expired_password_change",
    ),
    path(
        "forgot-password",
        waffle_switch("login")(
            PasswordResetView.as_view(
                template_name="registration/password_forgot_form.html",
                email_template_name="email/email-password-forgot-link.txt",
                html_email_template_name="email/email-password-forgot-link.html",
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        ),
        name="forgot_password",
    ),
    path(
        "password-reset-done",
        waffle_switch("login")(
            PasswordResetDoneView.as_view(
                template_name="registration/password_forgot_reset_done.html"
            )
        ),
        name="password_reset_done",
    ),
    re_path(
        r"^password-reset-confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$",
        waffle_switch("login")(
            PasswordResetConfirmView.as_view(
                template_name="registration/password_forgot_reset_confirm_form.html"
            )
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete",
        waffle_switch("login")(
            PasswordResetCompleteView.as_view(
                template_name="registration/password_forgot_reset_complete.html"
            )
        ),
        name="password_reset_complete",
    ),
    path(
        "activation-verify/<str:activation_key>/",
        waffle_switch("login")(activation_verify),
        name="activation_verify",
    ),
]
