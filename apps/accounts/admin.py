from django.contrib import admin
from models import ValidPasswordResetKey, Invitation, RequestInvite, UserProfile


admin.site.register(ValidPasswordResetKey)

class InvitationAdmin(admin.ModelAdmin):
    
    list_display =  ('email', 'code', 'valid', 'added')
    search_fields = ('code', 'valid', 'email')
    
admin.site.register(Invitation, InvitationAdmin)

class RequestInviteAdmin(admin.ModelAdmin):
    
    list_display =  ('first_name', 'last_name', 'organization', 'email', 'added')
    search_fields = ('first_name', 'last_name', 'organization', 'email')
    
admin.site.register(RequestInvite, RequestInviteAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    
    list_display =  ('user', 'organization_name', 'user_type', 'access_key_id')
    search_fields = ('user',)
    
admin.site.register(UserProfile, UserProfileAdmin)