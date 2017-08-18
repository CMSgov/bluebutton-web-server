from django.contrib import admin

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
        'organization',
        'email',
        'issue_invite',
        'invite_sent',
        'added')
    search_fields = ('first_name', 'last_name', 'organization', 'email')


admin.site.register(RequestInvite, RequestInviteAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'user_type')
    search_fields = ('user', 'user_type')


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


admin.site.register(MFACode, MFACodeAdmin)
