# Duckies: capa HTTP real

Estos archivos amplían la app original sin sustituir `models.py`, `services.py`, `integration_services.py`, migraciones ni `team5_ui`.

## Instalación
1. Copiar el directorio `apps/duckies/` sobre el del repositorio, revisando el diff antes de confirmar.
2. Conservar la ruta existente `path('team5/', include('apps.duckies.team5_ui.urls'))`.
3. Añadir **solo cuando se quiera activar** `path('duckies/', include('apps.duckies.urls'))` a `config/urls.py`.
4. Mantener la app `apps.duckies` en `INSTALLED_APPS`, `django.contrib.staticfiles` y la configuración de templates del proyecto.
5. Ejecutar `python manage.py check` y las pruebas existentes. Para pruebas URL nuevas, la ruta `/duckies/` debe estar montada.

## Rutas
GET `/duckies/`, `/duckies/inventory/`, `/duckies/outfits/`, `/duckies/museum/`.
POST `/duckies/outfits/select/`, `/duckies/inventory/equip/` (CSRF + login obligatorios).

## Contratos
- Identidad desde `request.user`, nunca usuarios de demo ni IDs de usuario del formulario.
- No se inicializa automáticamente un Ducky en una petición GET; si falta, 404. Alta real coordinada con Core/Ecomotor.
- Vestimentas y equipamiento pasan por `services.select_outfit` y `services.equip_item`.
- Shop entrega objetos, Bank administra Wallet, Ecomotor XP/especialización; Duckies no reproduce esos flujos.
- `Item.image_path` se interpreta como ruta relativa a static; no se cambian datos existentes.
- El museo muestra disponibilidad para vestir, no garantiza por sí mismo un historial de desbloqueo persistido.
- Las rutas y el CSS son provisionales. Las carpetas de imágenes definitivas pueden crearse al recibir assets.

## Verificación
`python manage.py check`; `python manage.py test apps.duckies.tests`.
**Pendiente**: pruebas de integración HTTP con fixtures reales de usuario + perfil Ecomotor + Ducky y despliegue conjunto con Core. No asumir que el paquete está validado en producción.
