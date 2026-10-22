"""Fictitious local history only. These deletion choices are not Core policy."""

from django.db import models

from .data import MAX_XP


class DemoTargetProgress(models.Model):
    session_owner = models.CharField(max_length=64)  # SHA256 of a server session secret.
    catalog = models.ForeignKey("ecomotor.TargetCatalogVersion", on_delete=models.PROTECT)
    xp_total = models.PositiveBigIntegerField(default=0)
    current_level = models.PositiveIntegerField(default=1)
    current_epoch = models.ForeignKey("ecomotor.TargetEpoch", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(xp_total__gte=0, xp_total__lte=MAX_XP), name="demo_progress_xp_range"),
            models.CheckConstraint(condition=models.Q(current_level__gte=1, current_level__lte=2**31-1), name="demo_progress_level_range"),
            models.CheckConstraint(condition=~models.Q(session_owner=""), name="demo_progress_owner_present"),
        ]


class DemoTargetXPEvent(models.Model):
    progress = models.ForeignKey(DemoTargetProgress, on_delete=models.PROTECT)
    operation_key = models.CharField(max_length=32)
    amount = models.PositiveBigIntegerField()
    xp_before = models.PositiveBigIntegerField()
    xp_after = models.PositiveBigIntegerField()
    level_before = models.PositiveIntegerField()
    level_after = models.PositiveIntegerField()
    epoch_before = models.ForeignKey("ecomotor.TargetEpoch", on_delete=models.PROTECT, related_name="demo_xp_before")
    epoch_after = models.ForeignKey("ecomotor.TargetEpoch", on_delete=models.PROTECT, related_name="demo_xp_after")
    catalog = models.ForeignKey("ecomotor.TargetCatalogVersion", on_delete=models.PROTECT)
    crossed_levels = models.JSONField()
    crossed_epoch_codes = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["progress", "operation_key"], name="demo_xp_operation_unique"),
            models.CheckConstraint(condition=~models.Q(operation_key=""), name="demo_xp_key_present"),
            models.CheckConstraint(condition=models.Q(amount__gt=0, amount__lte=MAX_XP,
                xp_before__gte=0, xp_before__lte=MAX_XP, xp_after__gte=0, xp_after__lte=MAX_XP), name="demo_xp_range"),
            models.CheckConstraint(condition=models.Q(xp_after=models.F("xp_before") + models.F("amount")), name="demo_xp_arithmetic"),
            models.CheckConstraint(condition=models.Q(level_before__gte=1, level_after__gte=models.F("level_before"),
                level_after__lte=2**31-1), name="demo_xp_levels"),
        ]


class DemoTargetEvolutionEvent(models.Model):
    progress = models.ForeignKey(DemoTargetProgress, on_delete=models.PROTECT)
    xp_event = models.ForeignKey(DemoTargetXPEvent, on_delete=models.PROTECT)
    epoch = models.ForeignKey("ecomotor.TargetEpoch", on_delete=models.PROTECT)
    ordinal = models.PositiveSmallIntegerField()
    catalog = models.ForeignKey("ecomotor.TargetCatalogVersion", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["progress", "epoch"], name="demo_evolution_epoch_unique"),
            models.UniqueConstraint(fields=["progress", "ordinal"], name="demo_evolution_ordinal_unique"),
            models.CheckConstraint(condition=models.Q(ordinal__gte=1, ordinal__lte=7), name="demo_evolution_ordinal_range"),
        ]
