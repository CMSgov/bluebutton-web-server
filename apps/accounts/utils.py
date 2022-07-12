import pytz

from datetime import datetime

from .models import ActivationKey


def validate_activation_key(activation_key):
    utc = pytz.UTC
    msg = ""
    is_valid = False

    try:
        vc = ActivationKey.objects.get(key=activation_key)
        now = datetime.now().replace(tzinfo=utc)
        expires = vc.expires.replace(tzinfo=utc)

        if vc.key_status and vc.key_status == "expired":
            msg = """The activation key is already expired.
            There may be an issue with your email verification.
            Continue to log in. If this issue persists, contact us at bluebuttonapi@cms.hhs.gov"""

        if vc.key_status == "created":
            if expires < now:
                # vc.delete() : BB2-1377 improve new user activation processing
                # The key has expired
                vc.key_status = "expired"
                vc.expired_at = now
                vc.save()
                msg = """The activation key is expired.
                There may be an issue with your email verification.
                Continue to log in. If this issue persists, contact us at bluebuttonapi@cms.hhs.gov"""
            else:
                # The key exists and has not expired.
                is_valid = True
                vc.user.is_active = True
                vc.key_status = "activated"
                vc.activated_at = now
                vc.user.save()
                vc.save()
                # vc.delete(): keep for audit and be stateful
        else:
            msg = """Invalid activation key.
            There may be an issue with your email verification.
            Continue to log in. If this issue persists, contact us at bluebuttonapi@cms.hhs.gov"""
    except(ActivationKey.DoesNotExist):
        # The key does not exist, corner case: a fabricated url with a fake activation key
        msg = """The activation key does not exist.
        There may be an issue with your email verification.
        Continue to log in. If this issue persists, contact us at bluebuttonapi@cms.hhs.gov"""

    # if is_valid and vc.key_status == "created":
    #     # The key exists and has not expired.
    #     vc.user.is_active = True
    #     vc.key_status = "activated"
    #     vc.activated_at = now
    #     vc.user.save()
    #     vc.save()
    #     # vc.delete(): keep for audit and be stateful
    return is_valid, msg
