# DuckyArena Equipo 5 — interfaz normal y demo opcional

## Modo normal (no depende de `apps/team5_demo`)

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`, iniciar sesión en `/accounts/login/` y crear el Ducky. Las pantallas usan modelos y servicios reales de Ecomotor, Duckies, Bank y Shop. Los catálogos deben cargarse con los procedimientos oficiales del proyecto. No se conceden XP ni monedas manualmente.

## Modo demo aislado

```powershell
python manage.py migrate --settings=config.settings_team5_demo
python manage.py setup_team5_demo --settings=config.settings_team5_demo
python manage.py createsuperuser --settings=config.settings_team5_demo
python manage.py runserver 127.0.0.1:8000 --settings=config.settings_team5_demo
```

La base `db_team5_demo.sqlite3` es independiente de `db.sqlite3`. El panel de operaciones se muestra únicamente a un usuario **staff** autenticado, con DEBUG activado y desde loopback. No publicar este servidor. El comando de demo genera datos sintéticos y no debe utilizarse con datos reales.

## Eliminar completamente la demo

1. Usar los settings normales (`config.settings`), no `settings_team5_demo`.
2. Borrar `apps/team5_demo/` y, opcionalmente, `config/settings_team5_demo.py` y `db_team5_demo.sqlite3`.
3. No borrar `apps/duckies/team5_ui/`, sus imágenes ni `sync_outfit_images.py`: son parte de la interfaz normal.
4. Ejecutar `python manage.py check` y `python manage.py runserver`.

`config/urls.py` solo incluye `apps.team5_demo.urls` cuando la app está explícitamente registrada y habilitada. Ningún servicio de dominio depende del módulo de demostración.

## Imágenes

Las imágenes de vestimentas se resuelven desde `Item.image_path` (BD real), sin dependencia del seed de demo. Para una variante por género, junto a `romano.webp` se puede colocar `romano_male.webp` o `romano_female.webp`: el resolver elegirá la variante cuando exista y, si falta, la imagen base. `sync_outfit_images` solo completa rutas vacías, no reemplaza imágenes oficiales.

## Alcance

Rewards y Arena pueden aparecer como secciones informativas si la integración productiva no está disponible. La demo no simula recompensas productivas. Se deben ejecutar las pruebas Django en el entorno del equipo antes de dar la integración por validada.
