# DuckyArena Equipo 5 — interfaz normal y demo aislada

## Interfaz normal (usuarios reales)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py sync_outfit_images
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`, inicia sesión y crea el Ducky desde la interfaz. El panel muestra datos del **usuario autenticado**, nunca los de un usuario fijo. La base de datos y los servicios de XP, Bank, Shop y Duckies son los reales. Para que funcione la progresión se requieren los catálogos Ecomotor oficiales y los datos iniciales del entorno; `sync_outfit_images` no los inventa.

## Herramientas de demostración (solo entorno aislado y staff)

```powershell
python manage.py migrate --settings=config.settings_team5_demo
python manage.py setup_team5_demo --settings=config.settings_team5_demo
python manage.py createsuperuser --settings=config.settings_team5_demo
python manage.py runserver 127.0.0.1:8000 --settings=config.settings_team5_demo
```

Accede con el superusuario que acabas de crear. Para disponer de un Ducky propio, créalo desde la interfaz. Solo con `settings_team5_demo`, BD `db_team5_demo.sqlite3`, acceso local y cuenta `is_staff` se muestran/aceptan los controles de XP, monedas y HINT. No se habilitan en `config.settings`. El comando de demo prepara catálogos sintéticos **solo para esa BD**; no configura imágenes ni concede objetos al usuario autenticado.

## Imágenes de vestimentas

`python manage.py sync_outfit_images` vincula las ilustraciones genéricas a `EvolutionItem.item.image_path` en los **registros reales**. No depende de la demo, no crea etapas y no sobrescribe imágenes oficiales existentes. Cada imagen está en `apps/duckies/static/team5_ui/img/outfits/`. Al cambiar `Item.image_path` por la imagen oficial, el dashboard, vestuario y catálogo usan la nueva referencia. Hay recursos para Prehistoria, Grecia, Roma, Medieval, Renacimiento, Revolución Industrial, Siglo XX y Actual.

**Incompatibilidad funcional a resolver con Ecomotor:** el catálogo de demostración existente tiene siete etapas (`PREHISTORIA`, `GRECIA`, `ROMA`, `MEDIEVAL`, `RENACIMIENTO`, `SIGLO_XX`, `ACTUAL`), no siete épocas históricas más Actual. Ecomotor exige exactamente siete etapas en su inicialización. Por tanto, la imagen de Revolución Industrial está preparada, pero **no tendrá un `EvolutionItem` asociado** hasta que el equipo apruebe y adapte el catálogo/contrato de etapas. No se ha modificado esa regla de dominio.

## Verificación pendiente

Ejecutar `python manage.py check`, migraciones y tests del proyecto en un entorno con Django instalado. En el entorno de preparación del ZIP no está instalada esa dependencia.
