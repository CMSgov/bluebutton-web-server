from ..models import UserProfile


def create_user_profile(strategy, details, backend, user=None, *args, **kwargs):
    up, created = UserProfile.objects.get_or_create(user=user)
    if created:
        up.create_applications = False
        up.authorize_applications = True
        up.user_type = "BEN"
        up.save()
    return {"userprofile": up}
