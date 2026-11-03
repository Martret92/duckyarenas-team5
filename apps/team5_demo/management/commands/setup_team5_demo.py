
"""Prepara datos sintéticos para la demo local del Equipo 5.

No modifica catálogos existentes incompatibles.
No utiliza la base de datos normal del proyecto.
"""

from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.bank.models import Wallet
from apps.duckies.models import (
    Item,
    EvolutionItem,
    SpecializationItem,
)
from apps.ecomotor.models import (
    EvolutionStage,
    LevelThreshold,
    Specialization,
)
from apps.ecomotor.initialization import ensure_ecomotor_initialized
from apps.shop.management.commands.seed_shop_catalog import (
    Command as ShopSeed,
)


# Códigos y umbrales utilizados por Ecomotor.
STAGES = (
    ("PREHISTORICO", "Prehistoria", 0),
    ("GRIEGO", "Grecia", 500),
    ("ROMANO", "Roma", 1000),
    ("MEDIEVAL", "Medieval", 1500),
    ("RENACENTISTA", "Renacimiento", 2000),
    ("REVOLUCION_INDUSTRIAL", "Revolución Industrial", 2500),
    ("SIGLO_XX", "Siglo XX", 3000),
)

# 50 niveles: nivel 1 = 0 XP; nivel 50 = 4900 XP.
LEVELS = tuple(range(0, 5000, 100))

SPECS = (
    ("GAMER", "Gamer"),
    ("DEVELOPER", "Developer"),
    ("CIBER", "Ciberseguridad"),
    ("SISTEMAS", "Sistemas"),
    ("DATA_IA", "Datos e IA"),
)


class Command(BaseCommand):
    help = (
        "Prepara los catálogos y datos sintéticos de la demo "
        "local del Equipo 5 sin borrar información existente."
    )

    def handle(self, *args, **options):
        database_name = Path(
            str(settings.DATABASES["default"]["NAME"])
        ).name

        if (
            not settings.DEBUG
            or not getattr(settings, "TEAM5_DEMO_ENABLED", False)
            or database_name != "db_team5_demo.sqlite3"
        ):
            raise CommandError(
                "Este comando solo puede ejecutarse en el "
                "entorno local de demostración con "
                "config.settings_team5_demo."
            )

        with transaction.atomic():
            self._prepare_catalogs()
            self._prepare_outfits()
            self._prepare_demo_user()

        # Conservamos el comando original de Shop.
        ShopSeed().handle()

        self.stdout.write(
            self.style.SUCCESS(
                "Demo local preparada correctamente. "
                "Visita /team5/ para probar el juego."
            )
        )

    def _prepare_catalogs(self):
        expected_stages = [
            (ordinal, code, xp)
            for ordinal, (code, _name, xp) in enumerate(
                STAGES, start=1
            )
        ]

        existing_stages = list(
            EvolutionStage.objects.order_by("ordinal")
            .values_list("ordinal", "code", "minimum_xp")
        )

        existing_levels = list(
            LevelThreshold.objects.order_by("level")
            .values_list("level", "minimum_xp")
        )

        expected_levels = list(
            enumerate(LEVELS, start=1)
        )

        existing_specs = list(
            Specialization.objects.order_by("code")
            .values_list("code", flat=True)
        )

        expected_specs = sorted(
            code for code, _name in SPECS
        )

        # Etapas: crear únicamente si el catálogo está vacío.
        if existing_stages:
            if existing_stages != expected_stages:
                raise CommandError(
                    "Catálogo de etapas incompatible. "
                    "No se sobrescriben los datos existentes. "
                    f"Actual: {existing_stages}"
                )
        else:
            for ordinal, (code, name, xp) in enumerate(
                STAGES, start=1
            ):
                EvolutionStage.objects.create(
                    code=code,
                    name=name,
                    ordinal=ordinal,
                    minimum_xp=xp,
                )

        # Niveles: crear únicamente si el catálogo está vacío.
        if existing_levels:
            if existing_levels != expected_levels:
                raise CommandError(
                    "Catálogo de niveles incompatible. "
                    "No se sobrescriben los datos existentes."
                )
        else:
            for level, xp in enumerate(LEVELS, start=1):
                LevelThreshold.objects.create(
                    level=level,
                    minimum_xp=xp,
                    stat_points_awarded=(
                        0 if level == 1 else 3
                    ),
                )

        # Especializaciones: conservar el catálogo existente
        # cuando sus códigos coincidan con los esperados.
        if existing_specs:
            if existing_specs != expected_specs:
                raise CommandError(
                    "Catálogo de especializaciones incompatible. "
                    "No se sobrescriben los datos existentes. "
                    f"Actual: {existing_specs}"
                )
        else:
            for code, name in SPECS:
                Specialization.objects.create(
                    code=code,
                    name=name,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Catálogos de Ecomotor comprobados."
            )
        )

    def _prepare_outfits(self):
        # Vestimentas históricas asociadas a etapas reales.
        for stage in EvolutionStage.objects.order_by(
            "ordinal"
        ):
            item, _created = Item.objects.get_or_create(
                code=f"outfit_{stage.code.lower()}",
                defaults={
                    "name": f"Vestimenta {stage.name}",
                    "category": Item.HISTORICAL,
                    "is_active": True,
                },
            )

            association, created = (
                EvolutionItem.objects.get_or_create(
                    stage=stage,
                    defaults={"item": item},
                )
            )

            if not created and association.item_id != item.pk:
                raise CommandError(
                    "La etapa "
                    f"{stage.code} ya tiene otra vestimenta "
                    "asociada. No se sobrescribe."
                )

        # Vestimentas de especialización.
        for spec in Specialization.objects.order_by(
            "code"
        ):
            item, _created = Item.objects.get_or_create(
                code=f"outfit_{spec.code.lower()}",
                defaults={
                    "name": f"Vestimenta {spec.name}",
                    "category": Item.SPECIALIZATION,
                    "is_active": True,
                },
            )

            association, created = (
                SpecializationItem.objects.get_or_create(
                    specialization=spec,
                    defaults={"item": item},
                )
            )

            if not created and association.item_id != item.pk:
                raise CommandError(
                    "La especialización "
                    f"{spec.code} ya tiene otra vestimenta "
                    "asociada. No se sobrescribe."
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Vestimentas históricas y de "
                "especialización comprobadas."
            )
        )

    def _prepare_demo_user(self):
        User = get_user_model()

        # Usuario técnico, inactivo y exclusivo de la demo.
        user, _created = User.objects.get_or_create(
            username="team5_demo_local",
            defaults={"is_active": False},
        )

        ensure_ecomotor_initialized(user)

        # Bank sigue siendo la única fuente de saldo.
        # No se conceden monedas ni se reinician saldos.
        Wallet.objects.get_or_create(user=user)

        self.stdout.write(
            self.style.SUCCESS(
                "Usuario técnico de demostración preparado."
            )
        )
