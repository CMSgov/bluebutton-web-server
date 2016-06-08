from django.conf.urls import include, url

from . import views
from .views.endorsement import endorsement_list, add_endorsement, edit_endorsement, delete_endorsement, all_endorsements


urlpatterns = [

    url(r'^all$', all_endorsements, name="all_endorsements_per_user"),
    url(r'^(?P<application_id>\d+)$', endorsement_list, name="endorsement_list"),
    url(r'^(?P<application_id>\d+)$', add_endorsement, name="add_endorsement"),
    url(r'^(?P<endorsement_id>\d+)$', edit_endorsement, name="edit_endorsement"),
    url(r'^(?P<endorsement_id>\d+)$', delete_endorsement, name="delete_endorsement"),

]
