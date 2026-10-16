from django.core.validators import MinValueValidator
from django.db import migrations, models


def reject_legacy_profiles(apps, schema_editor):
    profile = apps.get_model("users", "UserProfileEcomotor")
    if profile.objects.using(schema_editor.connection.alias).exists():
        raise RuntimeError(
            "M-01: existen perfiles UserProfileEcomotor legacy. "
            "Migración abortada; se requiere una estrategia de conservación con Core."
        )


class Migration(migrations.Migration):
    atomic = True
    dependencies = [("users", "0001_initial")]

    operations = [
        # Primera operación: ningún cambio de esquema precede a M-01.
        migrations.RunPython(reject_legacy_profiles, migrations.RunPython.noop),
        migrations.AddField(
            model_name="userprofileecomotor",
            name="historical_xp_total",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userprofileecomotor",
            name="current_level",
            field=models.PositiveIntegerField(null=True, validators=[MinValueValidator(1)]),
        ),
        migrations.AddField(
            model_name="userprofileecomotor",
            name="current_stage_code",
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="userprofileecomotor",
            name="active_specialization_code",
            field=models.CharField(max_length=32, null=True, blank=True, default=None),
        ),
        migrations.AlterField(
            model_name="userprofileecomotor",
            name="current_level",
            field=models.PositiveIntegerField(validators=[MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name="userprofileecomotor",
            name="current_stage_code",
            field=models.CharField(max_length=32),
        ),
        migrations.AddConstraint(
            model_name="userprofileecomotor",
            constraint=models.CheckConstraint(
                condition=models.Q(current_level__gt=0),
                name="users_ecomotor_level_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="userprofileecomotor",
            constraint=models.CheckConstraint(
                condition=~models.Q(current_stage_code=""),
                name="users_ecomotor_stage_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="userprofileecomotor",
            constraint=models.CheckConstraint(
                condition=models.Q(historical_xp_total__gte=0),
                name="users_ecomotor_xp_nonnegative",
            ),
        ),
        # Sin reverse_code: Django rechaza la reversión antes de quitar campos.
        migrations.RunPython(migrations.RunPython.noop),
    ]
