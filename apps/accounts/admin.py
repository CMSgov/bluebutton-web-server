from django.contrib import admin
from django.contrib.auth.models import User

from .models import (
    ValidPasswordResetKey,
    Invitation,
    RequestInvite,
    UserProfile,
    ActivationKey,
    MFACode,
    UserRegisterCode,
    EmailWebhook)


admin.site.register(ActivationKey)
admin.site.register(ValidPasswordResetKey)


class UserAdmin(admin.ModelAdmin):

    list_display = ('username',
                    'first_name',
                    'last_name',
                    'email',
                    'date_joined',
                    'is_staff',
                    'is_active',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class EmailWebhookAdmin(admin.ModelAdmin):
    list_display = (
        'status',
        'email',
        'added')
    search_fields = ('email', 'status')


admin.site.register(EmailWebhook, EmailWebhookAdmin)


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
    search_fields = ('first_name', 'last_name', 'user_type', 'organization', 'email')


admin.site.register(RequestInvite, RequestInviteAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'user_type', 'organization_name')
    search_fields = ('user__username', 'user__email', 'user__first_name',
                     'user__last_name', 'user_type', 'organization_name')
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
