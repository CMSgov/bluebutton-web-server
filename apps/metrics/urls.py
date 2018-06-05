from django.conf.urls import url
from django.contrib import admin
from .views import (total_user_count, active_user_count, staff_user_count,
                    super_user_count, total_user_profile_count, dev_user_profile_count,
                    ben_user_profile_count)

admin.autodiscover()

urlpatterns = [
    url(r'^total-user-count$', total_user_count, name='total-user-count'),
    url(r'^active-user-count$', active_user_count, name='active-user-count'),
    url(r'^staff-user-count$', staff_user_count, name='staff-user-count'),
    url(r'^super-user-count$', super_user_count, name='super-user-count'),
    url(r'^total-user-profile-count$', total_user_profile_count, name='total-user-profile-count'),
    url(r'^dev-user-profile-count$', dev_user_profile_count, name='dev-user-profile-count'),
    url(r'^ben-user-profile-count$', ben_user_profile_count, name='ben-user-profile-count'),
]
