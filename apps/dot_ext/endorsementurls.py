from django.conf.urls import url

from .views.endorsement import (endorsement_list, add_endorsement,
                                edit_endorsement, delete_endorsement,
                                view_endorsement_payload)


urlpatterns = [
    url(r'^list/(?P<application_id>\d+)$', endorsement_list, name='endorsement_list'),
    url(r'^add/(?P<application_id>\d+)$', add_endorsement, name='add_endorsement'),
    url(r'^edit/(?P<application_id>\d+)/(?P<endorsement_id>\d+)$', edit_endorsement, name='edit_endorsement'),
    url(r'^delete/(?P<application_id>\d+)/(?P<endorsement_id>\d+)$', delete_endorsement, name='delete_endorsement'),
    url(r'^view-payload/(?P<endorsement_id>\d+)$', view_endorsement_payload, name='view_endorsement_payload'),
]
