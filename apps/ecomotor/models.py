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
