from django.urls import path, re_path
from apps.health.views import (
    CheckBFD,
    CheckDB,
    CheckInternal,
    CheckExternal,
    CheckSLSX,
)


urlpatterns = [
    re_path(r"/external/?$", CheckExternal.as_view()),
    re_path(r"/external_v2/?$", CheckExternal.as_view()),
    re_path(r"/sls/?$", CheckSLSX.as_view()),
    re_path(r"/db/?$", CheckDB.as_view()),
    re_path(r"/bfd/?$", CheckBFD.as_view()),
    re_path(r"/bfd_v2/?$", CheckBFD.as_view()),
    re_path(r"^$", CheckInternal.as_view()),
    path("/", CheckInternal.as_view()),
]
