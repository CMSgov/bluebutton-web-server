from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    ValidPasswordResetKey,
    UserProfile,
    ActivationKey,
    UserIdentificationLabel)


admin.site.register(ActivationKey)
admin.site.register(ValidPasswordResetKey)


class UserTypeFilter(admin.SimpleListFilter):
    title = 'User type'
    parameter_name = 'userprofile__type'

    def lookups(self, request, model_admin):
        return [
            ('BEN', 'Beneficiary'),
            ('DEV', 'Developer'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(userprofile__user_type=self.value())
        return queryset


class UserAdmin(DjangoUserAdmin):

    list_display = ('username',
                    'get_type',
                    'email',
                    'first_name',
                    'last_name',
                    'is_staff',
                    'is_active',
                    'date_joined')

    list_filter = (UserTypeFilter, )

    def get_type(self, obj):
        return obj.userprofile.user_type

    get_type.short_description = 'Type'
    get_type.admin_order_field = 'userprofile__user_type'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class UserProfileAdmin(admin.ModelAdmin):

    def get_user_email(self, obj):
        return obj.user.email

    get_user_email.admin_order_field = "user__email"
    get_user_email.short_description = "Email Address"

    def get_user_joined(self, obj):
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


class UserIdentificationLabelAdmin(admin.ModelAdmin):
    model = UserIdentificationLabel
    filter_horizontal = ('users',)
    list_display = ("name", "slug", "weight")
    list_filter = ("name", "slug")
    ordering = ("weight", )


admin.site.register(UserIdentificationLabel, UserIdentificationLabelAdmin)
