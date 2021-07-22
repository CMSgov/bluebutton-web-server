from django.conf.urls import url
from .views import (
    CheckBFD,
    CheckDB,
    CheckInternal,
    CheckExternal,
    CheckSLSX,
)

urlpatterns = [
    url(r'external', CheckExternal.as_view()),
    url(r'external_v2', CheckExternal.as_view()),
    url(r'bfd', CheckBFD.as_view()),
    url(r'bfd_v2', CheckBFD.as_view()),
    url(r'sls', CheckSLSX.as_view()),
    url(r'db', CheckDB.as_view()),
    url(r'', CheckInternal.as_view()),
]
