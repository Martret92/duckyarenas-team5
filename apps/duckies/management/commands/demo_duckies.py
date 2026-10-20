"""Demo local explícita: no altera XP ni Bank; no ejecutar en producción."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from apps.ecomotor.models import EvolutionStage
from apps.users.models import UserProfileEcomotor
from apps.duckies.models import Ducky, Item, ItemLevel
from apps.duckies.services import grant_item, initialize_ducky

class Command(BaseCommand):
    help = "Crea usuario local y Ducky demo (solo DEBUG=True), sin tocar Bank ni XP."
    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo_duckies")
        parser.add_argument("--password", default="DuckyDemo2026!")
        parser.add_argument("--sex", choices=["male", "female"], default="male")
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Demo prohibida con DEBUG=False.")
        stage = EvolutionStage.objects.order_by("ordinal").first()
        if not stage:
            raise CommandError("Configura primero las etapas de Ecomotor y ejecuta seed_duckies.")
        User = get_user_model()
        user, created = User.objects.get_or_create(username=options["username"])
        if created:
            user.set_password(options["password"]);user.save(update_fields=["password"])
        profile, _ = UserProfileEcomotor.objects.get_or_create(user=user, defaults={"current_level": 1, "current_stage_code": stage.code})
        ducky = initialize_ducky(user, options["sex"])
        for item in Item.objects.filter(category__in=[Item.ATTACK, Item.DEFENSE, Item.HINT], is_active=True):
            level = ItemLevel.objects.filter(item=item, level=1).first()
            grant_item(user, item, 3, f"demo-duckies-{item.code}-v1", item_level=level, reference_type="LOCAL_DEMO", reference_id="seed")
        self.stdout.write(self.style.SUCCESS(f"Usuario demo: {user.username}; creado={created}; Ducky={ducky.pk}. Contraseña predeterminada solo para desarrollo."))
