"""Catálogo sintético exclusivamente para tests: no son valores oficiales de Ecomotor."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.bank.models import Wallet
from apps.duckies.models import Ducky, EvolutionItem, Item, ItemLevel, SpecializationItem
from apps.ecomotor import initialization_config
from apps.ecomotor.models import EvolutionStage, LevelThreshold, Specialization
from apps.users.models import UserProfileEcomotor

from apps.duckies.integration_services import initialize_player_ducky

STAGE_CODES = (
    "PREHISTORICO", "GRIEGO", "ROMANO", "MEDIEVAL",
    "RENACENTISTA", "REVOLUCION_INDUSTRIAL", "SIGLO_XX",
)
SPEC_CODES = ("DEVELOPER", "GAMER", "CIBER", "SISTEMAS", "DATA_IA")


class IntegrationFixture(TestCase):
    """Construye catálogos consistentes sin editar ni activar Ecomotor permanentemente."""

    def setUp(self):
        super().setUp()
        self.config_patch = patch.object(
            initialization_config,
            "INITIAL_CONFIGURATION",
            initialization_config.InitializationConfiguration(
                atk=1, def_stat=1, log_stat=1, spe=1, vel=1, int_stat=1,
                ordered_stage_codes=STAGE_CODES,
            ),
        )
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

        self.stages = {}
        self.historical = {}
        for ordinal, code in enumerate(STAGE_CODES, start=1):
            stage = EvolutionStage.objects.create(
                code=code, name=code, ordinal=ordinal,
                minimum_xp=(ordinal - 1) * 100,
            )
            self.stages[code] = stage
            item = Item.objects.create(
                code=f"test-hist-{ordinal}", name=f"Historical {ordinal}",
                category=Item.HISTORICAL, consumable=False, is_active=True,
            )
            EvolutionItem.objects.create(stage=stage, item=item)
            self.historical[code] = item

        for level in range(1, 11):
            LevelThreshold.objects.create(
                level=level, minimum_xp=(level - 1) * 100,
                stat_points_awarded=2,
            )

        self.specializations = {}
        self.spec_outfits = {}
        for code in SPEC_CODES:
            specialization = Specialization.objects.create(code=code, name=code)
            outfit = Item.objects.create(
                code=f"test-spec-{code.lower()}", name=f"Spec {code}",
                category=Item.SPECIALIZATION, consumable=False, is_active=True,
            )
            SpecializationItem.objects.create(specialization=specialization, item=outfit)
            self.specializations[code] = specialization
            self.spec_outfits[code] = outfit

        self.user = get_user_model().objects.create_user(username="integracion-e5")
        self.ducky = initialize_player_ducky(self.user, "male")
        self.profile = UserProfileEcomotor.objects.get(user=self.user)
        self.wallet = Wallet.objects.create(user=self.user)

    def advance_to_final_stage(self):
        from apps.duckies.integration_services import grant_xp_and_sync_outfit
        result = grant_xp_and_sync_outfit(self.user, 700, "test-stage-final")
        self.profile.refresh_from_db()
        self.ducky.refresh_from_db()
        return result

    def make_offer(self, *, code="test-attack-offer", price=20, pack=3,
                   category=Item.ATTACK, consumable=True, level=2):
        from apps.shop.models import ShopItem
        item = Item.objects.create(
            code=f"item-{code}", name=code, category=category,
            consumable=consumable, is_active=True,
        )
        item_level = (
            ItemLevel.objects.create(item=item, level=level)
            if level is not None else None
        )
        offer = ShopItem.objects.create(
            code=code, item=item, item_level=item_level, name=code,
            price_coins=price, included_quantity=pack,
        )
        return offer, item, item_level
