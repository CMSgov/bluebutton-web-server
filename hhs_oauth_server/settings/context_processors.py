from hhs_oauth_server.settings import base

# This context processor replaces the use of
# django-settings-export, which seems to only work with
# setuptools less than v40. We are on setuptools v80. To implement
# this, all the bindings that were called out in `base.py` were
# added here, and bound to their values from base.
#
# This file gets pulled in for every template. As a result, we can reference
# {{ export_settings.VARIABLE }}
# in any template, and use the values bound here.


def export_settings(request):
    # Expose only the settings you explicitly list
    exported_settings = {
        "ALLOW_END_USER_EXTERNAL_AUTH": base.ALLOW_END_USER_EXTERNAL_AUTH,
        "ALLOWED_HOSTS": base.ALLOWED_HOSTS,
        "APPLICATION_TITLE": base.APPLICATION_TITLE,
        "DEBUG": base.DEBUG,
        "DEVELOPER_DOCS_TITLE": base.DEVELOPER_DOCS_TITLE,
        "DEVELOPER_DOCS_URI": base.DEVELOPER_DOCS_URI,
        "DISCLOSURE_TEXT": base.DISCLOSURE_TEXT,
        "EXPLAINATION_LINE": base.EXPLAINATION_LINE,
        "EXTERNAL_AUTH_NAME": base.EXTERNAL_AUTH_NAME,
        "INSTALLED_APPS": base.INSTALLED_APPS,
        "LANGUAGE_COOKIE_NAME": "en",
        "MEDIA_ROOT": base.MEDIA_ROOT,
        "MEDIA_URL": base.MEDIA_URL,
        "OPTIONAL_INSTALLED_APPS": base.OPTIONAL_INSTALLED_APPS,
        "ORGANIZATION_TITLE": base.ORGANIZATION_TITLE,
        "POLICY_TITLE": base.POLICY_TITLE,
        "POLICY_URI": base.POLICY_URI,
        "STATIC_ROOT": base.STATIC_ROOT,
        "STATIC_URL": base.STATIC_URL,
        "TAG_LINE_1": base.TAG_LINE_1,
        "TAG_LINE_2": base.TAG_LINE_2,
        "THEME": base.THEME,
        "TOS_TITLE": base.TOS_TITLE,
        "TOS_URI": base.TOS_URI,
    }
    return {'export_settings': exported_settings}
