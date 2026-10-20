"""Etapas EXCLUSIVAMENTE de demostración para probar Duckies en una BD local.

No sustituye la configuración oficial de Ecomotor ni inicializa su motor de XP.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ecomotor.models import EvolutionStage, EvolutionEvent
from apps.users.models import UserProfileEcomotor
from apps.duckies.models import EvolutionItem


# Valores ficticios, NO aprobados como reglas de progresión del juego.
DEMO_STAGES = (
    ("DEMO_PREHISTORICO", "Prehistórico (DEMO)", 0),
    ("DEMO_GRIEGO", "Griego (DEMO)", 100),
    ("DEMO_ROMANO", "Romano (DEMO)", 200),
    ("DEMO_MEDIEVAL", "Medieval (DEMO)", 300),
    ("DEMO_RENACENTISTA", "Renacentista (DEMO)", 400),
    ("DEMO_INDUSTRIAL", "Revolución Industrial (DEMO)", 500),
    ("DEMO_SIGLO_XX", "Siglo XX (DEMO)", 600),
)


class Command(BaseCommand):
    help = "Crea las 7 etapas ficticias para probar Duckies localmente; --cleanup las retira solo si no están en uso."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Comprueba sin escribir en la BD.")
        parser.add_argument("--cleanup", action="store_true", help="Elimina únicamente las etapas DEMO si no tienen referencias.")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Comando de demostración bloqueado: DEBUG debe ser True.")

        with transaction.atomic():
            stages = list(EvolutionStage.objects.select_for_update().order_by("ordinal"))
            expected = [(i, *row) for i, row in enumerate(DEMO_STAGES, start=1)]
            expected_codes = {code for _, code, _, _ in expected}

            if options["cleanup"]:
                foreign = [stage for stage in stages if stage.code not in expected_codes]
                if foreign:
                    raise CommandError("Hay etapas ajenas a la demo; no se realiza limpieza.")
                for stage in stages:
                    _, code, name, xp = expected[stage.ordinal - 1]
                    if (stage.code, stage.name, stage.minimum_xp) != (code, name, xp):
                        raise CommandError("Una etapa DEMO ha cambiado: limpieza cancelada.")
                if (EvolutionItem.objects.filter(stage__in=stages).exists()
                        or EvolutionEvent.objects.filter(stage__in=stages).exists()
                        or UserProfileEcomotor.objects.filter(current_stage_code__in=expected_codes).exists()):
                    raise CommandError("Hay vestimentas, eventos o perfiles asociados. No se borrará nada."
                                       " Usa una BD local desechable para reiniciar la demo.")
                if not options["dry_run"]:
                    EvolutionStage.objects.filter(pk__in=[s.pk for s in stages]).delete()
                self.stdout.write(self.style.SUCCESS(
                    f"Limpieza {'simulada' if options['dry_run'] else 'completada'}: {len(stages)} etapa(s) DEMO."
                ))
                return

            if stages:
                if len(stages) != 7:
                    raise CommandError("Ya existen etapas en Ecomotor, pero no son exactamente siete."
                                       " No se añaden ni modifican etapas.")
                for stage, (ordinal, code, name, xp) in zip(stages, expected):
                    if (stage.ordinal, stage.code, stage.name, stage.minimum_xp) != (ordinal, code, name, xp):
                        raise CommandError("Ecomotor ya tiene una configuración distinta."
                                           " No se sobrescribe ningún dato.")
                self.stdout.write(self.style.SUCCESS("Las siete etapas DEMO ya existen; no se modificó nada."))
                return

            if options["dry_run"]:
                self.stdout.write("Simulación correcta: se crearían 7 etapas DEMO (XP ficticios 0, 100, ..., 600).")
                return
            EvolutionStage.objects.bulk_create([
                EvolutionStage(ordinal=ordinal, code=code, name=name, minimum_xp=xp)
                for ordinal, code, name, xp in expected
            ])
            self.stdout.write(self.style.SUCCESS("Creadas 7 etapas DEMO. Ejecuta ahora seed_duckies."))
