MyMedicare Callback
===================

Docs for the MyMedicare (SLS) authentication flow can be found in Confluence: https://confluence.cms.gov/display/BB/OpenID+Connect+%28OIDC%29+for+SLS

Adjust the following settings for environments.  Below the DEV defaults are given, but must be updated for production.


    SLS_TOKEN_ENDPOINT = 'https://dev.accounts.cms.gov/v1/oauth/token'
    MEDICARE_LOGIN_URI = 'https://dev2.account.mymedicare.gov/?scope=openid%20profile&client_id=bluebutton'
    MEDICARE_REDIRECT_URI = 'http://localhost:8000/mymedicare/sls-callback'
    SLS_VERIFY_SSL = False
