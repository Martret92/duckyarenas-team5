from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class UserProfileEcomotor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    historical_xp_total = models.PositiveBigIntegerField(default=0)
    current_level = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    current_stage_code = models.CharField(max_length=32)
    active_specialization_code = models.CharField(
        max_length=32, null=True, blank=True, default=None
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(current_level__gt=0),
                name="users_ecomotor_level_positive",
            ),
            models.CheckConstraint(
                condition=~models.Q(current_stage_code=""),
                name="users_ecomotor_stage_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(historical_xp_total__gte=0),
                name="users_ecomotor_xp_nonnegative",
            ),
        ]


class UserProfileBank(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
