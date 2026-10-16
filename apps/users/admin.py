from django.contrib import admin

from apps.ecomotor.admin import ReadOnlySuperuserAdmin

from .models import UserProfileEcomotor


@admin.register(UserProfileEcomotor)
class UserProfileEcomotorAdmin(ReadOnlySuperuserAdmin):
    list_display = (
        "user", "historical_xp_total", "current_level", "current_stage_code",
        "active_specialization_code",
    )
    search_fields = ("user__username", "user__email")
    list_filter = ("current_level", "current_stage_code", "active_specialization_code")
    list_select_related = ("user",)
    ordering = ("user_id",)
