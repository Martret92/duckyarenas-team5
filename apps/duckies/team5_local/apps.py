from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

class Team5LocalConfig(AppConfig):
    name = 'apps.duckies'
    label = 'duckies'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        if not getattr(settings, 'TEAM5_LOCAL_ISOLATED', False):
            return
        # Exclusivo del proceso con settings_team5_local y su BD independiente.
        from apps.ecomotor import initialization_config
        from .seed import LOCAL_CODES
        initialization_config.INITIAL_CONFIGURATION = initialization_config.InitializationConfiguration(
            atk=10, def_stat=10, log_stat=10, spe=10, vel=10, int_stat=10,
            ordered_stage_codes=LOCAL_CODES,
        )
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save
        from apps.bank.models import Wallet
        def provision_local_wallet(sender, instance, created, **kwargs):
            if created:
                Wallet.objects.get_or_create(user=instance)
        post_save.connect(provision_local_wallet, sender=get_user_model(), weak=False, dispatch_uid='team5_local_wallet_provision')
        from django.apps import apps
        post_migrate.connect(self._seed_shop, sender=apps.get_app_config('shop'), weak=False, dispatch_uid='team5_local_shop_post_migrate')

    @staticmethod
    def _seed_shop(sender, using, **kwargs):
        if using != 'default':
            return
        from django.core.management import call_command
        call_command('seed_shop_catalog', verbosity=0)
