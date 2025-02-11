MyMedicare Callback
===================


Docs for the Medicare.gov (SLSx) authentication flow can be found in Confluence: https://confluence.cms.gov/display/BB2/BB2+SLSx+Integration+and+Implementation?src=contextnavpagetreemode

In 1/2021 we will be migrating from using SLS to the new SLSx endpoints!

Docs for the Medicare.gov (SLS) authentication flow can be found in Confluence: https://confluence.cms.gov/display/BB/OpenID+Connect+%28OIDC%29+for+SLS

Adjust the following settings for environments.  Below the DEV defaults are given, but must be updated for production.

    SLSX_TOKEN_ENDPOINT = 'https://test.medicare.gov/sso/session'
    MEDICARE_SLSX_LOGIN_URI = 'https://test.medicare.gov/sso/authorize?client_id=bb2api'
    MEDICARE_SLSX_REDIRECT_URI = 'http://localhost:8000/mymedicare/sls-callback/'
    SLSX_VERIFY_SSL = False
