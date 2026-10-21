from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


STAT_ATTRIBUTES = ("atk", "def_stat", "log_stat", "spe", "vel", "int_stat")


class StatAllocationEvent(models.Model):
    # CASCADE provisional, conservación definitiva pendiente de Core.
    profile = models.ForeignKey("users.UserProfileEcomotor", on_delete=models.CASCADE)
    operation_key = models.CharField(max_length=255)
    attribute = models.CharField(max_length=16, choices=[(name, name) for name in STAT_ATTRIBUTES])
    points_spent = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    increase_applied = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    available_points_before = models.PositiveIntegerField()
    available_points_after = models.PositiveIntegerField()
    attribute_before = models.IntegerField()
    attribute_after = models.IntegerField()
    stage_code_at_allocation = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "operation_key"], name="ecomotor_allocation_profile_key"),
            models.CheckConstraint(condition=~models.Q(operation_key=""), name="ecomotor_allocation_key_nonempty"),
            models.CheckConstraint(condition=models.Q(attribute__in=STAT_ATTRIBUTES), name="ecomotor_allocation_attribute"),
            models.CheckConstraint(condition=models.Q(points_spent__gt=0), name="ecomotor_allocation_points_positive"),
            models.CheckConstraint(condition=models.Q(increase_applied__gt=0), name="ecomotor_allocation_increase_positive"),
            models.CheckConstraint(condition=models.Q(increase_applied=models.F("points_spent")), name="ecomotor_allocation_one_to_one"),
            models.CheckConstraint(condition=models.Q(available_points_before=models.F("available_points_after") + models.F("points_spent")), name="ecomotor_allocation_balance"),
            models.CheckConstraint(condition=models.Q(attribute_after=models.F("attribute_before") + models.F("increase_applied")), name="ecomotor_allocation_increment"),
            models.CheckConstraint(condition=~models.Q(stage_code_at_allocation=""), name="ecomotor_allocation_stage_nonempty"),
        ]


class LevelThreshold(models.Model):
    level = models.PositiveIntegerField(unique=True, validators=[MinValueValidator(1)])
    minimum_xp = models.PositiveBigIntegerField()
    stat_points_awarded = models.PositiveIntegerField()

    class Meta:
        ordering = ["level"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(level__gt=0), name="ecomotor_level_positive"
            ),
        ]

    def __str__(self):
        return f"Nivel {self.level}: {self.minimum_xp} XP"


class EvolutionStage(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    ordinal = models.PositiveSmallIntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    minimum_xp = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["ordinal"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ordinal__gte=1, ordinal__lte=7),
                name="ecomotor_stage_ordinal_range",
            ),
            models.CheckConstraint(
                condition=~models.Q(code=""), name="ecomotor_stage_code_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""), name="ecomotor_stage_name_not_empty"
            ),
        ]

    def __str__(self):
        return self.name


class Specialization(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(code=""), name="ecomotor_spec_code_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""), name="ecomotor_spec_name_not_empty"
            ),
        ]

    def __str__(self):
        return self.name


class CharacterStats(models.Model):
    # CASCADE provisional: conservación definitiva pendiente de Core.
    profile = models.OneToOneField("users.UserProfileEcomotor", on_delete=models.CASCADE)
    atk = models.IntegerField()
    def_stat = models.IntegerField()
    log_stat = models.IntegerField()
    spe = models.IntegerField()
    vel = models.IntegerField()
    int_stat = models.IntegerField()
    available_points = models.PositiveIntegerField()


class XPEvent(models.Model):
    # Clave local de XP histórica; no deduplica toda la recompensa de Rewards.
    profile = models.ForeignKey("users.UserProfileEcomotor", on_delete=models.CASCADE)
    amount = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    xp_before = models.PositiveBigIntegerField()
    xp_after = models.PositiveBigIntegerField()
    operation_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "operation_key"], name="ecomotor_xp_profile_key_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="ecomotor_xp_amount_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(xp_after=models.F("xp_before") + models.F("amount")),
                name="ecomotor_xp_snapshot_sum",
            ),
            models.CheckConstraint(
                condition=~models.Q(operation_key=""), name="ecomotor_xp_key_not_empty"
            ),
        ]


class EvolutionEvent(models.Model):
    # CASCADE provisional; conservación pendiente de Óscar/Core.
    profile = models.ForeignKey("users.UserProfileEcomotor", on_delete=models.CASCADE)
    stage = models.ForeignKey(EvolutionStage, on_delete=models.PROTECT)
    xp_event = models.ForeignKey(XPEvent, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "stage"], name="ecomotor_evolution_unique"
            ),
        ]

    # Igualdad profile/xp_event.profile e inmutabilidad: futuro servicio propietario.


class UserSpecializationProgress(models.Model):
    # Estructura mínima: concesión y trazabilidad de XP de dominio pendientes.
    profile = models.ForeignKey("users.UserProfileEcomotor", on_delete=models.CASCADE)
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT)
    domain_xp_total = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "specialization"],
                name="ecomotor_progress_profile_spec",
            ),
            models.CheckConstraint(
                condition=models.Q(domain_xp_total__gte=0),
                name="ecomotor_domain_xp_nonnegative",
            ),
        ]


class TargetCatalogVersion(models.Model):
    """Catalog identity with optional physical freeze, never publication."""

    id = models.BigAutoField(primary_key=True)
    catalog_id = models.CharField(max_length=64)
    version = models.CharField(max_length=64)

    frozen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["catalog_id", "version"], name="ecomotor_tcat_identity_unique"),
            models.CheckConstraint(condition=~models.Q(catalog_id=""), name="ecomotor_tcat_id_nonempty"),
            models.CheckConstraint(condition=~models.Q(version=""), name="ecomotor_tcat_ver_nonempty"),
        ]


class TargetLevelThreshold(models.Model):
    """Preparatory level only; target progression awards no level stat points."""

    id = models.BigAutoField(primary_key=True)
    catalog = models.ForeignKey(TargetCatalogVersion, on_delete=models.PROTECT)
    level = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    minimum_xp = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["catalog", "level"], name="ecomotor_tlevel_unique"),
            models.CheckConstraint(condition=models.Q(level__gt=0), name="ecomotor_tlevel_positive"),
            models.CheckConstraint(condition=models.Q(minimum_xp__gte=0), name="ecomotor_tlevel_xp_nonnegative"),
        ]


class TargetEpoch(models.Model):
    """Preparatory historical epoch, separate from EvolutionStage V1."""

    id = models.BigAutoField(primary_key=True)
    catalog = models.ForeignKey(TargetCatalogVersion, on_delete=models.PROTECT)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=100)
    ordinal = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    minimum_xp = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["catalog", "code"], name="ecomotor_tepoch_code_unique"),
            models.UniqueConstraint(fields=["catalog", "ordinal"], name="ecomotor_tepoch_ordinal_unique"),
            models.CheckConstraint(condition=models.Q(ordinal__gte=1, ordinal__lte=7),
                                   name="ecomotor_tepoch_ordinal_range"),
            models.CheckConstraint(condition=models.Q(minimum_xp__gte=0), name="ecomotor_tepoch_xp_nonnegative"),
            models.CheckConstraint(condition=~models.Q(code=""), name="ecomotor_tepoch_code_nonempty"),
            models.CheckConstraint(condition=~models.Q(name=""), name="ecomotor_tepoch_name_nonempty"),
        ]
