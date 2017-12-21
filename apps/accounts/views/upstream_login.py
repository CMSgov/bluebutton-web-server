from django.shortcuts import render
from django.conf import settings
import urllib.request as req

__author__ = "Alan Viars"


def upstream_oauth_login(request):
    mymedicare_login_url = 'https://dev2.account.mymedicare.gov/?scope=openid%20profile&client_id=bluebutton&state=54321'
    query = 'http://localhost:8000/mymedicare/sls-callback'
    query = req.pathname2url(query)
    mymedicare_login_url = "%s&redirect_uri=%s&next=%s" % (
        mymedicare_login_url, query, request.GET.get('next'))
    my_next = request.GET.get('next')
    template_name = getattr(
        settings, 'SOCIALAUTH_LOGIN_TEMPLATE_NAME', "design_system/login.html")
    if my_next:
        request.session['next'] = my_next
    return render(request, template_name, {'next': my_next,
                                           'mymedicare_login_url': mymedicare_login_url})
