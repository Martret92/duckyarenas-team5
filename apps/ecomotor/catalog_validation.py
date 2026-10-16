"""Validación explícita de catálogos completos, nunca ejecutada desde save().

Estas comprobaciones entre filas no son constraints ni bloquean la carga gradual.
El llamador debe validar una configuración coherente antes de utilizarla; estas
funciones no bloquean modificaciones concurrentes ni publican el catálogo.
"""

from django.core.exceptions import ValidationError

from .models import EvolutionStage, LevelThreshold


def validate_level_catalog(levels=None):
    """Comprueba la configuración completa de niveles, sin fijar su cantidad."""
    levels = list(LevelThreshold.objects.all() if levels is None else levels)
    if not levels:
        raise ValidationError("El catálogo de niveles está vacío.")
    for level in levels:
        level.full_clean(validate_unique=False, validate_constraints=False)
    levels.sort(key=lambda level: level.level)
    if [level.level for level in levels] != list(range(1, len(levels) + 1)):
        raise ValidationError("Los niveles deben ser consecutivos y empezar en 1.")
    if levels[0].minimum_xp != 0:
        raise ValidationError("El nivel 1 debe empezar en 0 XP.")
    if any(left.minimum_xp >= right.minimum_xp for left, right in zip(levels, levels[1:])):
        raise ValidationError("Los umbrales de nivel deben crecer estrictamente.")


def validate_evolution_stage_catalog(stages=None, *, ordered_stage_codes):
    """Valida siete etapas contra una correspondencia explícita de códigos.

    ordered_stage_codes debe contener los códigos configurados para Prehistoria,
    Griega, Romana, Renacentista, Contemporánea, Siglo XX y Actual, en ese orden.
    No se define aquí ningún código oficial ni se usa name como identidad técnica.
    La correspondencia deberá acordarse antes de utilizar un catálogo real.
    El orden de entrada de las filas es indiferente: manda su ordinal.
    """
    codes = list(ordered_stage_codes)
    if len(codes) != 7 or any(not isinstance(code, str) or not code for code in codes):
        raise ValidationError("Se requieren siete códigos de etapa no vacíos.")
    if len(set(codes)) != 7:
        raise ValidationError("La correspondencia de etapas requiere códigos únicos.")
    stages = list(EvolutionStage.objects.all() if stages is None else stages)
    if len(stages) != 7:
        raise ValidationError("El catálogo debe contener exactamente siete etapas.")
    for stage in stages:
        stage.full_clean(validate_unique=False, validate_constraints=False)
    stages.sort(key=lambda stage: stage.ordinal)
    if [stage.ordinal for stage in stages] != list(range(1, 8)):
        raise ValidationError("Los ordinales de las etapas deben ser del 1 al 7.")
    if [stage.code for stage in stages] != codes:
        raise ValidationError("Los códigos no siguen el orden funcional configurado.")
    if stages[0].minimum_xp != 0:
        raise ValidationError("Prehistoria debe empezar en 0 XP.")
    if any(left.minimum_xp >= right.minimum_xp for left, right in zip(stages, stages[1:])):
        raise ValidationError("Los umbrales de etapa deben crecer estrictamente.")
