from django.conf.urls import url

from .views.core import (simple_login, create_user,
                         create_developer, account_settings,
                         reissue_api_keys, request_developer_invite,
                         mylogout, forgot_password, request_user_invite,
                         password_reset_email_verify, display_api_keys,
                         activation_verify)

urlpatterns = [
    # login and Logout ------------------------------------
    url(r'login', simple_login, name='login'),
    url(r'logout$', mylogout, name='mylogout'),

    # create and update account info -----------------------
    url(r'create-user', create_user, name='accounts_create_user'),
    url(r'create-developer',
        create_developer,
        name='accounts_create_developer'),
    url(r'settings$', account_settings, name='account_settings'),

    # Request a Developer invite to signup ---------------------------
    url(r'request-developer-invite',
        request_developer_invite,
        name='request_developer_invite'),
    # Request an invite to signup ---------------------------
    url(r'request-user-invite', request_user_invite,
        name='request_user_invite'),

    # Forgot password? ---------------------------------------
    url(r'forgot-password$', forgot_password, name='forgot_password'),

    # Change password using reset token ------------------------
    url(r'password-reset-email-verify/(?P<reset_password_key>[^/]+)/',
        password_reset_email_verify,
        name='password_reset_email_verify'),

    # Verify the account
    url(r'activation-verify/(?P<activation_key>[^/]+)/', activation_verify,
        name='activation_verify'),

    url(r'display-api-keys$', display_api_keys, name='display_api_keys'),

    url(r'reissue-api-keys$', reissue_api_keys, name='reissue_api_keys'),
]
