import pytz

from datetime import datetime

from .models import ActivationKey

LINK_EXPIRED_MSG = """The activation key is expired.
                Contact us at bluebuttonapi@cms.hhs.gov for further assistance"""
ACCT_HAS_ISSUE_MSG = """There may be an issue with your account.
                Contact us at bluebuttonapi@cms.hhs.gov"""
ACCT_ACTIVATED_MSG = """Your account has been activated. You may now login."""


def validate_activation_key(activation_key):
    utc = pytz.UTC
    msg = ""
    is_valid = False

    try:
        vc = ActivationKey.objects.get(key=activation_key)
        now = datetime.now().replace(tzinfo=utc)
        expires = vc.expires.replace(tzinfo=utc)

        if vc.key_status == "created":
            if expires < now:
                # The key has expired
                vc.key_status = "expired"
                vc.expired_at = now
                vc.save()
                msg = LINK_EXPIRED_MSG
            else:
                # The key exists and has not expired.
                is_valid = True
                vc.user.is_active = True
                vc.key_status = "activated"
                vc.activated_at = now
                vc.user.save()
                vc.save()
                msg = ACCT_ACTIVATED_MSG
        else:
            # key_status is 'activated' or 'expired'
            if vc.key_status == 'activated':
                # already activated, just redirect to login page
                is_valid = True
                msg = ACCT_ACTIVATED_MSG
            elif vc.key_status == 'expired':
                # activate an expired account
                msg = LINK_EXPIRED_MSG
            else:
                msg = ACCT_HAS_ISSUE_MSG
    except(ActivationKey.DoesNotExist):
        # The key does not exist, corner case: a fabricated url with a fake activation key
        msg = ACCT_HAS_ISSUE_MSG

    return is_valid, msg
