"""
Decorator to check for that the user's profile has
authorize_applications == True
"""

from django.shortcuts import get_object_or_404
from .models import UserProfile
from functools import update_wrapper


def authorize_app_flag_required(func):
    """
    Put this decorator before your view to check if
    user's profile has  authorize_applications==True
    """

    def wrapper(request, *args, **kwargs):
        get_object_or_404(
            UserProfile,
            user=request.user,
            authorize_applications=True)
        return func(request, *args, **kwargs)

    return update_wrapper(wrapper, func)
