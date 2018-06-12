from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import (
    ValidPasswordResetKey,
    Invitation,
    RequestInvite,
    UserProfile,
    ActivationKey,
    MFACode,
    UserRegisterCode)


admin.site.register(ActivationKey)
admin.site.register(ValidPasswordResetKey)


ua = UserAdmin
ua.list_display = ('username', 'email', 'first_name',
                   'last_name', 'is_staff', 'is_active', 'date_joined')


admin.site.unregister(User)
admin.site.register(User, ua)


class UserRegisterCodeAdmin(admin.ModelAdmin):
    list_display = ('email',
                    'sender',
                    'code',
                    'name',
                    'sent',
                    'added',
                    'username',
                    'used')
    search_fields = ('username', 'first_name', 'last_name',
                     'code', 'email')


admin.site.register(UserRegisterCode, UserRegisterCodeAdmin)


class RequestInviteAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'user_type',
        'organization',
        'email',
        'issue_invite',
        'invite_sent',
        'added')
    search_fields = ('first_name', 'last_name',
                     'user_type', 'organization', 'email')


admin.site.register(RequestInvite, RequestInviteAdmin)


class UserProfileAdmin(admin.ModelAdmin):

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.admin_order_field = "user__email"
    get_user_email.short_description = "Email Address"

    def get_user_joined(selfself, obj):
        return obj.user.date_joined

    get_user_joined.admin_order_field = "user__date_joined"
    get_user_joined.short_description = "Date Joined"

    list_display = ('user', 'name', 'user_type',
                    'organization_name', 'get_user_email',
                    'get_user_joined')
    search_fields = ('user__username', 'user__email', 'user__first_name',
                     'user__last_name', 'user_type', 'organization_name',
                     'user__date_joined')
    raw_id_fields = ("user", )


admin.site.register(UserProfile, UserProfileAdmin)


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'code', 'valid', 'added')
    search_fields = ('code', 'valid', 'email')


admin.site.register(Invitation, InvitationAdmin)


class MFACodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code',
                    'tries_counter',
                    'mode',
                    'endpoint',
                    'expires')
    search_fields = ('mode', 'endpoint')
    raw_id_fields = ("user", )


admin.site.register(MFACode, MFACodeAdmin)
