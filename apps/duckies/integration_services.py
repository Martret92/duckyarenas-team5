"""Compatibilidad con las importaciones anteriores de integración.

La implementación principal reside en apps.integrations.services.
"""

from apps.integrations.services import (
    initialize_player_ducky,
    grant_xp_and_sync_outfit,
    select_initial_specialization_and_outfit,
    switch_specialization_and_outfit,
)

# Mantener estos nombres disponibles para las pruebas existentes.
from apps.integrations import services as _integration_services


def _database_alias(user):
    return _integration_services._database_alias(user)