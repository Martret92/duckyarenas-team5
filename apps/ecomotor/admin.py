from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import router, transaction

from apps.users.models import UserProfileEcomotor

from .models import (
    CharacterStats,
    EvolutionEvent,
    EvolutionStage,
    LevelThreshold,
    Specialization,
    UserSpecializationProgress,
    XPEvent,
)


class SuperuserOnlyAdmin(admin.ModelAdmin):
    """Permissions for Parte A only; never a restriction on model.save()."""

    actions = None

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        raise PermissionDenied

    def delete_queryset(self, request, queryset):
        raise PermissionDenied


class ReadOnlySuperuserAdmin(SuperuserOnlyAdmin):
    """Progress and histories are written by their owners, never by Admin."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.concrete_fields)

    def save_model(self, request, obj, form, change):
        raise PermissionDenied

    def save_related(self, request, form, formsets, change):
        raise PermissionDenied


class CatalogAdmin(SuperuserOnlyAdmin):
    """Allow gradual loading only before the first Ecomotor profile exists."""

    def has_add_permission(self, request):
        using = router.db_for_write(self.model)
        return self.has_module_permission(request) and not (
            UserProfileEcomotor.objects.using(using).exists()
        )

    def has_change_permission(self, request, obj=None):
        return self.has_add_permission(request)

    def save_model(self, request, obj, form, change):
        # Recheck at write time. Admin POSTs also have an outer atomic block;
        # SQLite IMMEDIATE (D-19) serializes writers on this connection.
        using = router.db_for_write(self.model)
        with transaction.atomic(using=using):
            if not self.has_add_permission(request):
                raise PermissionDenied
            super().save_model(request, obj, form, change)


@admin.register(LevelThreshold)
class LevelThresholdAdmin(CatalogAdmin):
    list_display = ("level", "minimum_xp", "stat_points_awarded")
    search_fields = ("=level",)
    list_filter = ("stat_points_awarded",)
    ordering = ("level",)


@admin.register(EvolutionStage)
class EvolutionStageAdmin(CatalogAdmin):
    list_display = ("ordinal", "code", "name", "minimum_xp")
    search_fields = ("code", "name")
    list_filter = ("ordinal",)
    ordering = ("ordinal",)


@admin.register(Specialization)
class SpecializationAdmin(CatalogAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
    ordering = ("code",)


@admin.register(CharacterStats)
class CharacterStatsAdmin(ReadOnlySuperuserAdmin):
    list_display = (
        "profile", "atk", "def_stat", "log_stat", "spe", "vel", "int_stat",
        "available_points",
    )
    search_fields = ("profile__user__username",)
    list_filter = ("profile__current_level",)
    list_select_related = ("profile__user",)
    ordering = ("profile_id",)


@admin.register(XPEvent)
class XPEventAdmin(ReadOnlySuperuserAdmin):
    list_display = (
        "profile", "amount", "xp_before", "xp_after", "operation_key", "created_at",
    )
    search_fields = ("profile__user__username", "operation_key")
    list_filter = ("created_at",)
    list_select_related = ("profile__user",)
    ordering = ("-created_at", "-pk")


@admin.register(EvolutionEvent)
class EvolutionEventAdmin(ReadOnlySuperuserAdmin):
    list_display = ("profile", "stage", "xp_event", "created_at")
    search_fields = ("profile__user__username", "stage__code", "xp_event__operation_key")
    list_filter = ("stage", "created_at")
    list_select_related = ("profile__user", "stage", "xp_event")
    ordering = ("-created_at", "-pk")


@admin.register(UserSpecializationProgress)
class UserSpecializationProgressAdmin(ReadOnlySuperuserAdmin):
    list_display = ("profile", "specialization", "domain_xp_total")
    search_fields = ("profile__user__username", "specialization__code", "specialization__name")
    list_filter = ("specialization",)
    list_select_related = ("profile__user", "specialization")
    ordering = ("profile_id", "specialization_id")
