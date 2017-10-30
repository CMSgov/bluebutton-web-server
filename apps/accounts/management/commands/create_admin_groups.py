from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

__author__ = "Alan Viars"


def create_groups():
    groups = ["HelpDesk", "InviteBeneficiary", "InviteDeveloper", "ModifyUser"]
    created_groups = []
    for group in groups:
        g, created = Group.objects.get_or_create(name=group)
        created_groups.append(created)
        if created:
            print("%s group created" % (group))
        else:
            print("%s group pre-existing. Create skipped." % (group))
    return dict(zip(groups, created_groups))


def create_permissions(created_groups):

    if created_groups["HelpDesk"]:
        g = Group.objects.get(name="HelpDesk")
        p = Permission.objects.get(name='Can add user profile')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can change user profile')
        g.permissions.add(p)

    if created_groups["InviteBeneficiary"]:
        g = Group.objects.get(name="InviteBeneficiary")
        p = Permission.objects.get(name='Can add Invite Request')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can change Invite Request')
        g.permissions.add(p)

    if created_groups["InviteDeveloper"]:
        g = Group.objects.get(name="InviteDeveloper")
        p = Permission.objects.get(name='Can add Developer Invitation')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can change Developer Invitation')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can add user register code')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can change user register code')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can delete user register code')
        g.permissions.add(p)

    if created_groups["ModifyUser"]:
        g = Group.objects.get(name="ModifyUser")
        p = Permission.objects.get(name='Can add user')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can change user')
        g.permissions.add(p)
        p = Permission.objects.get(name='Can delete user')
        g.permissions.add(p)


class Command(BaseCommand):
    help = 'Create BlueButton Administrative Groups and Permissions. Run only 1x at initial setup.'

    def handle(self, *args, **options):
        cg = create_groups()
        create_permissions(cg)
        print("Done. Stay classy, San Diego.")
