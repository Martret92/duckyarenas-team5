
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ecomotor.models import EvolutionStage, Specialization
from apps.users.models import UserProfileEcomotor

from apps.duckies.models import (
    Ducky,
    Item,
    EvolutionItem,
    SpecializationItem,
    EquipmentSlot,
    InventoryItem,
)

from apps.duckies.services import (
    initialize_ducky,
    select_outfit,
    grant_item,
)


class DuckiesSpecializationTests(TestCase):

    def setUp(self):
        # 1. Crear usuario
        self.user = get_user_model().objects.create_user(
            username="test_specialization",
            password="test_password_123",
        )

        # 2. Crear las siete etapas históricas
        self.stages = []

        for ordinal, code in enumerate(
            [
                "PREHISTORICO",
                "GRIEGO",
                "ROMANO",
                "MEDIEVAL",
                "RENACENTISTA",
                "REVOLUCION_INDUSTRIAL",
                "SIGLO_XX",
            ],
            start=1,
        ):
            stage = EvolutionStage.objects.create(
                code=code,
                name=code.replace("_", " ").title(),
                ordinal=ordinal,
                minimum_xp=(ordinal - 1) * 100,
            )
            self.stages.append(stage)

        # 3. Crear el perfil Ecomotor
        self.profile = UserProfileEcomotor.objects.create(
            user=self.user,
            current_level=1,
            current_stage_code=self.stages[0].code,
            active_specialization_code=None,
        )

        # 4. Crear las siete vestimentas históricas
        self.historical_outfits = []

        for stage in self.stages:
            item = Item.objects.create(
                code=f"outfit_{stage.code.lower()}",
                name=f"Vestimenta {stage.name}",
                category=Item.HISTORICAL,
                consumable=False,
                is_active=True,
            )

            EvolutionItem.objects.create(
                stage=stage,
                item=item,
            )

            self.historical_outfits.append(item)

        # 5. Crear las cinco especializaciones y vestimentas
        self.specialization_outfits = {}

        for code, name in [
            ("DEVELOPER", "Developer"),
            ("GAMER", "Gamer"),
            ("CIBER", "Ciber"),
            ("SISTEMAS", "Sistemas"),
            ("DATA_IA", "Data IA"),
        ]:
            specialization = Specialization.objects.create(
                code=code,
                name=name,
            )

            item = Item.objects.create(
                code=f"outfit_spec_{code.lower()}",
                name=f"Vestimenta {name}",
                category=Item.SPECIALIZATION,
                consumable=False,
                is_active=True,
            )

            SpecializationItem.objects.create(
                specialization=specialization,
                item=item,
            )

            self.specialization_outfits[code] = item

        # 6. Crear el personaje
        self.ducky = initialize_ducky(
            self.user,
            "male",
        )

    def specialize(self, code):
        """
        Simula el estado que Ecomotor dejaría después
        de confirmar una especialización.

        No sustituye al servicio oficial de Ecomotor.
        """
        self.profile.current_stage_code = self.stages[-1].code
        self.profile.active_specialization_code = code

        self.profile.save(
            update_fields=[
                "current_stage_code",
                "active_specialization_code",
            ]
        )

    def test_developer_can_equip_developer(self):
        self.specialize("DEVELOPER")

        ducky = select_outfit(
            self.user,
            self.specialization_outfits["DEVELOPER"],
        )

        self.assertEqual(
            ducky.selected_outfit_id,
            self.specialization_outfits["DEVELOPER"].pk,
        )

    def test_developer_cannot_equip_gamer(self):
        self.specialize("DEVELOPER")

        with self.assertRaises(ValueError):
            select_outfit(
                self.user,
                self.specialization_outfits["GAMER"],
            )

    def test_gamer_can_equip_gamer(self):
        self.specialize("GAMER")

        ducky = select_outfit(
            self.user,
            self.specialization_outfits["GAMER"],
        )

        self.assertEqual(
            ducky.selected_outfit_id,
            self.specialization_outfits["GAMER"].pk,
        )

    def test_all_specializations_can_equip_own_outfit(self):
        for code, item in self.specialization_outfits.items():
            with self.subTest(specialization=code):
                self.specialize(code)

                ducky = select_outfit(
                    self.user,
                    item,
                )

                self.assertEqual(
                    ducky.selected_outfit_id,
                    item.pk,
                )

    def test_cannot_equip_specialization_before_choosing(self):
        with self.assertRaises(ValueError):
            select_outfit(
                self.user,
                self.specialization_outfits["DEVELOPER"],
            )

    def test_specialized_user_can_equip_old_historical_outfit(self):
        self.specialize("DEVELOPER")

        roman_outfit = self.historical_outfits[2]

        ducky = select_outfit(
            self.user,
            roman_outfit,
        )

        self.assertEqual(
            ducky.selected_outfit_id,
            roman_outfit.pk,
        )

    def test_cannot_equip_future_historical_outfit(self):
        # El jugador todavía está en la Prehistoria
        future_outfit = self.historical_outfits[3]

        with self.assertRaises(ValueError):
            select_outfit(
                self.user,
                future_outfit,
            )

    def test_cannot_equip_previous_stage_before_specialization(self):
        # El jugador está en la etapa romana,
        # pero todavía no se ha especializado.
        self.profile.current_stage_code = self.stages[2].code
        self.profile.save(update_fields=["current_stage_code"])

        with self.assertRaises(ValueError):
            select_outfit(
                self.user,
                self.historical_outfits[0],
            )

    def test_cannot_equip_tactical_item_as_outfit(self):
        slot = EquipmentSlot.objects.create(
            code="TACTICAL",
            name="Táctico",
        )

        tactical_item = Item.objects.create(
            code="test_firewall",
            name="Escudo Firewall",
            category=Item.DEFENSE,
            slot=slot,
            consumable=True,
        )

        self.specialize("DEVELOPER")

        with self.assertRaises(ValueError):
            select_outfit(
                self.user,
                tactical_item,
            )

    def test_cannot_grant_specialization_outfit(self):
        self.specialize("DEVELOPER")

        with self.assertRaises(ValueError):
            grant_item(
                self.user,
                self.specialization_outfits["DEVELOPER"],
                1,
                "grant_spec_001",
            )

        self.assertFalse(
            InventoryItem.objects.filter(
                ducky=self.ducky,
                item=self.specialization_outfits["DEVELOPER"],
            ).exists()
        )

    def test_rejected_selection_keeps_previous_outfit(self):
        self.specialize("DEVELOPER")

        select_outfit(
            self.user,
            self.specialization_outfits["DEVELOPER"],
        )

        with self.assertRaises(ValueError):
            select_outfit(
                self.user,
                self.specialization_outfits["GAMER"],
            )

        self.ducky.refresh_from_db()

        self.assertEqual(
            self.ducky.selected_outfit_id,
            self.specialization_outfits["DEVELOPER"].pk,
        )