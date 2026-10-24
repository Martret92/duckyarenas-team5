import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ecomotor_target_demo", "0004_rewards_bank_schema"),
        ("duckies", "0002_rename_selected_historical_item_ducky_selected_outfit_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="demotargetrewardevent",
            name="demo_reward_outcome_valid",
        ),
        migrations.AddField(
            model_name="demotargetrewardevent",
            name="item_grant",
            field=models.OneToOneField(blank=True, null=True,
                on_delete=django.db.models.deletion.PROTECT, to="duckies.itemgrant"),
        ),
        migrations.AddConstraint(
            model_name="demotargetrewardevent",
            constraint=models.CheckConstraint(
                condition=(models.Q(status="APPLIED", xp_amount__gt=0, xp_event__isnull=False,
                    coin_amount=0, bank_transaction__isnull=True, item_grant__isnull=True)
                    | models.Q(status="APPLIED", xp_amount=0, xp_event__isnull=True,
                        coin_amount__gt=0, bank_transaction__isnull=False, item_grant__isnull=True)
                    | models.Q(status="APPLIED", xp_amount=0, xp_event__isnull=True,
                        coin_amount=0, bank_transaction__isnull=True, item_grant__isnull=False)
                    | models.Q(status="NO_REWARD", xp_amount=0, xp_event__isnull=True,
                        coin_amount=0, bank_transaction__isnull=True, item_grant__isnull=True)),
                name="demo_reward_outcome_valid",
            ),
        ),
    ]
