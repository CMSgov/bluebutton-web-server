import pytz

from datetime import datetime

from .models import ActivationKey


def validate_activation_key(activation_key):
    utc = pytz.UTC
    msg = ""
    is_valid = True

    try:
        vc = ActivationKey.objects.get(key=activation_key)
        now = datetime.now().replace(tzinfo=utc)
        expires = vc.expires.replace(tzinfo=utc)

        if vc.key_status and vc.key_status == "expired":
            is_valid = False
            msg = "The activation key is already expired."

        if vc.key_status == "created" and expires < now:
            # vc.delete() : BB2-1377 improve new user activation processing
            # The key has expired
            is_valid = False
            vc.key_status = "expired"
            vc.expired_at = now
            vc.save()
            msg = "The activation key is expired."
    except(ActivationKey.DoesNotExist):
        # The key does not exist, corner case: a fabricated url with a fake activation key
        is_valid = False
        msg = "The activation key does not exist."

    if is_valid and vc.key_status == "created":
        # The key exists and has not expired.
        vc.user.is_active = True
        vc.key_status = "activated"
        vc.activated_at = now
        vc.user.save()
        vc.save()
        # vc.delete(): keep for audit and be stateful
    return is_valid, msg
