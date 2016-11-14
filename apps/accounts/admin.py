from django.contrib import admin

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
        'added')
    search_fields = ('first_name', 'last_name', 'organization', 'email')


admin.site.register(RequestInvite, RequestInviteAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'user_type', 'access_key_id')
    search_fields = ('user',)


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
