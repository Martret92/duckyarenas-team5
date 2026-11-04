# DuckyArena Equipo 5 — integración local aislada

## Alcance

Esta rama parte del ZIP `develop (10)` y reutiliza los servicios de Duckies, Ecomotor, Bank y Shop. Se incorpora la interfaz de `feature/team5-interfaz-integrada`. La configuración oficial `apps/ecomotor/initialization_config.py` **no se modifica**. La configuración sintética existe solo cuando se usa `config.settings_team5_local` y la BD separada `db_team5_local.sqlite3`.

## Primer arranque (PowerShell, desde la raíz del repositorio)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate --settings=config.settings_team5_local
python manage.py team5_setup_local --settings=config.settings_team5_local
python manage.py runserver --settings=config.settings_team5_local
```

Al ejecutar `migrate` en este entorno local, el catálogo Shop se carga automáticamente por la señal `post_migrate` de Shop mediante su comando oficial `seed_shop_catalog`, sin ejecución manual. Si el comando detecta un catálogo incompatible, falla explícitamente; no lo sobrescribe. **No se hace seeding al entrar en una página ni en cada petición.**

Abre `http://127.0.0.1:8000/accounts/register/`, registra un usuario y selecciona masculino o femenino en la pantalla inicial. El usuario nuevo recibe una Wallet vacía por aprovisionamiento exclusivo de este entorno aislado. La creación del Ducky usa `initialize_player_ducky`.

## Pruebas administrativas (otra terminal, mismo entorno)

```powershell
python manage.py team5_grant_coins --username USUARIO --amount 500 --settings=config.settings_team5_local
python manage.py team5_grant_xp --username USUARIO --amount 350 --settings=config.settings_team5_local
```

Las operaciones utilizan los servicios `adjust_wallet` y `grant_xp_and_sync_outfit`, no escrituras directas del saldo o XP. Las compras usan `purchase_item`; equipar y vestir usan servicios oficiales de Duckies. La interfaz no incluye botones para regalar XP ni monedas.

## Variantes visuales

`apps/duckies/item_visual_variants.json` contiene un registro extensible por código real de Item y clave `stage:<código>` o `specialization:<código>`. La vista calcula la clave desde `Ducky.selected_outfit` y usa el mismo resolvedor en Shop e inventario. **Las imágenes entregadas solo incluyen seis diseños genéricos tácticos y las vestimentas disponibles; no se recibieron imágenes tácticas específicas para todas las épocas/especializaciones.** Hasta incorporar esos archivos y las claves correspondientes, se muestra la imagen genérica del objeto, sin cambiar la propiedad ni las estadísticas.

## Límites de la entrega

- La configuración y catálogos locales son **sintéticos** y no autorizan valores oficiales. No usar en producción ni mezclar con otras bases de datos.
- El flujo de combate/Arena y las recompensas de Core no se implementan aquí.
- Las pruebas Django no pudieron ejecutarse en el entorno de preparación por ausencia de Django instalable; se realizó verificación de sintaxis Python. **Antes de dar el visto bueno**, ejecutar `python manage.py check --settings=config.settings_team5_local` y `python manage.py test --settings=config.settings_team5_local` y hacer una prueba manual completa.
- Los recursos y las plantillas demo de Ecomotor no se alteran.
