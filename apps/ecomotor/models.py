from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
