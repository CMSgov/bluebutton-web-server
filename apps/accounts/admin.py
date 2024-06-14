from datetime import datetime
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    ValidPasswordResetKey,
    UserProfile,
    ActivationKey,
    UserIdentificationLabel,
)

admin.site.register(ActivationKey)
admin.site.register(ValidPasswordResetKey)


class UserTypeFilter(admin.SimpleListFilter):
    title = "User type"
    parameter_name = "userprofile__type"

    def lookups(self, request, model_admin):
        return [
            ("BEN", "Beneficiary"),
            ("DEV", "Developer"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(userprofile__user_type=self.value())
        return queryset


class ActiveAccountFilter(admin.SimpleListFilter):
    title = "User activation status"
    parameter_name = "is_active"

    def lookups(self, request, model_admin):
        return [
            ("active", "Active"),
            ("inactive_all", "Inactive"),
            ("inactive_expired", "Inactive (expired activation key)")
        ]

    def queryset(self, request, queryset):
        if self.value() == "inactive_expired":
            return queryset.filter(
                is_active=False,
                activationkey__key_status="expired",
            ) | queryset.filter(
                # Since the activation keys only reach "expired" status when they are
                # used post-expiration, we need to check the "created" status as well
                is_active=False,
                activationkey__key_status="created",
                activationkey__expires__lt=(datetime.today()),
            )
        elif self.value() == "inactive_all":
            return queryset.filter(is_active=False)
        elif self.value() == "active":
            return queryset.filter(is_active=True)


class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "get_type",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (UserTypeFilter, ActiveAccountFilter,)

    @admin.display(
        description="Type",
        ordering="userprofile__user_type",
    )
    def get_type(self, obj):
        return obj.userprofile.user_type


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    @admin.display(
        description="Email Address",
        ordering="user__email",
    )
    def get_user_email(self, obj):
        return obj.user.email

    @admin.display(
        description="Date Joined",
        ordering="user__date_joined",
    )
    def get_user_joined(self, obj):
        return obj.user.date_joined

    list_display = (
        "user",
        "name",
        "user_type",
        "organization_name",
        "get_user_email",
        "get_user_joined",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "user_type",
        "organization_name",
        "user__date_joined",
    )
    raw_id_fields = ("user",)


@admin.register(UserIdentificationLabel)
class UserIdentificationLabelAdmin(admin.ModelAdmin):
    model = UserIdentificationLabel
    filter_horizontal = ("users",)
    list_display = ("name", "slug", "weight")
    list_filter = ("name", "slug")
    ordering = ("weight",)
