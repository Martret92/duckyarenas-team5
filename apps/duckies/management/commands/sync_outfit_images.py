"""Sincroniza imágenes provisionales en registros reales; no concede objetos ni altera evolución."""
from django.core.management.base import BaseCommand
from apps.duckies.models import EvolutionItem, SpecializationItem

ERA_IMAGES = {'PREHISTORIA': 'team5_ui/img/outfits/prehistoria.webp', 'GRECIA': 'team5_ui/img/outfits/grecia.webp', 'ROMA': 'team5_ui/img/outfits/roma.webp', 'MEDIEVAL': 'team5_ui/img/outfits/medieval.webp', 'RENACIMIENTO': 'team5_ui/img/outfits/renacimiento.webp', 'REVOLUCION_INDUSTRIAL': 'team5_ui/img/outfits/revolucion_industrial.webp', 'SIGLO_XX': 'team5_ui/img/outfits/siglo_xx.webp', 'ACTUAL': 'team5_ui/img/outfits/actual.webp'}

class Command(BaseCommand):
    help = "Asocia imágenes a vestimentas reales de cada época, sin depender de la demo."
    def handle(self, *args, **options):
        associations = list(EvolutionItem.objects.select_related('stage','item'))
        missing = sorted(set(ERA_IMAGES) - {a.stage.code for a in associations})
        if missing:
            self.stderr.write('Faltan asociaciones EvolutionItem para: ' + ', '.join(missing))
        for association in associations:
            path = ERA_IMAGES.get(association.stage.code)
            if path and not association.item.image_path:
                association.item.image_path = path
                association.item.save(update_fields=['image_path'])
                self.stdout.write('Imagen vinculada: ' + association.stage.name)
        # Las cinco especializaciones usan un recurso genérico por género
        # cuando su Item.image_path está vacío; no se altera el catálogo.
        for association in SpecializationItem.objects.select_related('specialization', 'item'):
            self.stdout.write('Especialización disponible para ilustración: ' + association.specialization.name)
        self.stdout.write('Sincronización terminada. No se reemplazaron imágenes oficiales existentes.')
