from hhs_oauth_server.settings import base


def export_settings(request):
    # Expose only the settings you explicitly list
    exported_settings = {
        "DEBUG": base.DEBUG,
        "ALLOWED_HOSTS": base.ALLOWED_HOSTS,
        "APPLICATION_TITLE": base.APPLICATION_TITLE,
        "THEME": base.THEME,
        "STATIC_URL": base.STATIC_URL,
        "STATIC_ROOT": base.STATIC_ROOT,
        "MEDIA_URL": base.MEDIA_URL,
        "MEDIA_ROOT": base.MEDIA_ROOT,
        "DEVELOPER_DOCS_URI": base.DEVELOPER_DOCS_URI,
        "DEVELOPER_DOCS_TITLE": base.DEVELOPER_DOCS_TITLE,
        "ORGANIZATION_TITLE": base.ORGANIZATION_TITLE,
        "POLICY_URI": base.POLICY_URI,
        "POLICY_TITLE": base.POLICY_TITLE,
        "DISCLOSURE_TEXT": base.DISCLOSURE_TEXT,
        "TOS_URI": base.TOS_URI,
        "TOS_TITLE": base.TOS_TITLE,
        "TAG_LINE_1": base.TAG_LINE_1,
        "TAG_LINE_2": base.TAG_LINE_2,
        "EXPLAINATION_LINE": base.EXPLAINATION_LINE,
        "EXTERNAL_AUTH_NAME": base.EXTERNAL_AUTH_NAME,
        "ALLOW_END_USER_EXTERNAL_AUTH": base.ALLOW_END_USER_EXTERNAL_AUTH,
        "OPTIONAL_INSTALLED_APPS": base.OPTIONAL_INSTALLED_APPS,
        "INSTALLED_APPS": base.INSTALLED_APPS,
        # FIXME: This isn't set anywhere? Ah. In templates,
        # they assume it isn't set. This is just broken by design.
        "LANGUAGE_COOKIE_NAME": "en",
    }
    return {'export_settings': exported_settings}

    # 'DEBUG': settings.DEBUG,
    # 'GA_ID': getattr(settings, 'GA_ID', None),  # Use getattr for optional settings
    # # Add other settings here
