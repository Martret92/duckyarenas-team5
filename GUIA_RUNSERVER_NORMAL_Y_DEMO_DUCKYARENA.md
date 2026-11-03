# DuckyArena Equipo 5 — Guía de ejecución normal y demo

**Base revisada:** `DuckyArena_Equipo5_Entrega_Interfaz_V1.zip` (Django 5.2.17). Esta guía distingue lo que funciona con los datos sintéticos de la demo de lo que necesita configuración real del Core/Ecomotor. Comandos para PowerShell desde la carpeta que contiene `manage.py`, con `.venv` activado.

## 0. Preparación común

```powershell
# Desde la raíz del proyecto
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py check
```

> Los dos modos usan **bases de datos diferentes**: `db.sqlite3` (normal) y `db_team5_demo.sqlite3` (demo). Ejecuta `migrate`, `createsuperuser`, `shell` y cualquier comando de datos con los **mismos settings** que el servidor al que quieres acceder. Nunca copies la base demo sobre la normal.

## 1. Servidor NORMAL — interfaz real, sin botones de concesión

### 1.1 Preparar y arrancar

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Abre <http://127.0.0.1:8000/> (redirige a `/team5/`) e inicia sesión en `/accounts/login/`. El panel administrativo está en `/admin/`.

**Importante:** el modo normal de esta entrega **no incorpora un catálogo inicial oficial ni valores autorizados de atributos**. `apps/ecomotor/initialization_config.py` deja `INITIAL_CONFIGURATION = None`. Para crear un Ducky real, el equipo responsable/Core debe suministrar y activar la configuración autorizada de Ecomotor, sus siete `EvolutionStage`, `LevelThreshold`, especializaciones y sus asociaciones `EvolutionItem`/`SpecializationItem`. `migrate` crea tablas, **no** esos datos. No uses el comando sintético `setup_team5_demo` sobre `db.sqlite3`: lo prohíbe expresamente.

### 1.2 Crear el personaje en modo normal

Cuando el catálogo y la configuración oficial estén preparados:

1. Accede con un usuario existente o crea uno desde administración.
2. Ve a <http://127.0.0.1:8000/team5/>.
3. En la pantalla de creación, selecciona **masculino** o **femenino**.
4. El formulario llama a `initialize_player_ducky()`: inicializa el perfil Ecomotor y el Ducky, comprueba su vestimenta. Después podrás recorrer Inicio, Mi Pato, Evolución, Especialización, Vestuario, Inventario, Tienda y Banco.
5. **Bank no se aprovisiona en esa función de la V1**: el Core/integración debe crear una Wallet por usuario antes de operaciones económicas. Consulta el apartado 3.

Si aparece **«Falta configuración inicial autorizada»** o **«Catálogos iniciales inválidos»**, no se resuelve cambiando de sexo: faltan o no coinciden los datos/configuración de Ecomotor. **Sin esa configuración real, no se puede prometer que el alta funcione en el servidor normal de esta V1.** Para recorrer la interfaz hoy con datos de prueba, utiliza el modo demo del apartado 2.

### 1.3 Añadir DuckyCoins desde consola, sin botones

**Solo para un entorno de desarrollo autorizado.** Bank es la fuente de verdad económica. Evita `wallet.available_balance = 500; wallet.save()`: altera el saldo sin registrar la transacción. Usa el servicio existente:

```powershell
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.bank.models import Wallet
from apps.bank.services import adjust_wallet
from uuid import uuid4

usuario = get_user_model().objects.get(username="oscar")  # sustituir por usuario real
wallet = Wallet.objects.get(user=usuario)  # debe existir
print("Saldo inicial:", wallet.available_balance)

adjust_wallet(
    usuario, 500,
    operation_key=f"prueba-manual-{uuid4().hex}",
    description="Crédito autorizado de pruebas",
    source="prueba_local",
    issuing_entity="Equipo5",
)
wallet.refresh_from_db()
print("Saldo final:", wallet.available_balance)
```

**`500` significa añadir 500**, no fijar el saldo total a 500. El servicio registra el movimiento. Si necesitas un saldo objetivo, calcula la diferencia y respeta las reglas de Bank (saldo no negativo).

### 1.4 Añadir XP desde consola, sin botones

El servicio integrado sincroniza la evolución y el outfit; **no** edites `historical_xp_total` directamente:

```powershell
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.duckies.integration_services import grant_xp_and_sync_outfit
from uuid import uuid4

usuario = get_user_model().objects.get(username="oscar")
resultado = grant_xp_and_sync_outfit(usuario, 1000, f"prueba-xp-{uuid4().hex}")
print(resultado)
```

Requisitos: perfil Ecomotor inicializado, catálogo válido y Ducky coherente. **`1000` añade XP**, no establece XP total en 1000. Estos ejemplos son para pruebas locales autorizadas, no una vía de recompensas de producción.

## 2. Servidor DEMO — base aislada y controles administrativos

### 2.1 Corregir la duplicación de comando en la V1 (una sola vez)

En la V1 existen **dos** archivos llamados `setup_team5_demo.py`:

- `apps/duckies/management/commands/setup_team5_demo.py` — el que Django ejecutó en el error observado.
- `apps/team5_demo/management/commands/setup_team5_demo.py` — usa el orden compatible con `settings_team5_demo.py`.

Antes de inicializar una demo nueva, **copia el contenido del segundo sobre el primero**, o modifica en el primero la constante `STAGES` para que sea exactamente:

```python
STAGES = (
    ('PREHISTORIA', 'Prehistoria'),
    ('GRECIA', 'Grecia'),
    ('ROMA', 'Roma'),
    ('MEDIEVAL', 'Medieval'),
    ('RENACIMIENTO', 'Renacimiento'),
    ('REVOLUCION_INDUSTRIAL', 'Revolución Industrial'),
    ('SIGLO_XX', 'Siglo XX'),
)
```

**No alteres el orden de etapas en Ecomotor para acomodar un seed equivocado.** Para la versión definitiva conviene dejar un único comando y derivar sus etapas de la configuración, sin duplicaciones.

### 2.2 Preparar base demo y usuario administrador

```powershell
python manage.py migrate --settings=config.settings_team5_demo
python manage.py setup_team5_demo --settings=config.settings_team5_demo
python manage.py createsuperuser --settings=config.settings_team5_demo
python manage.py runserver 127.0.0.1:8000 --settings=config.settings_team5_demo
```

Si el superusuario ya existe, **no lo crees otra vez**. El comando demo prepara catálogos **sintéticos**, outfits e ítems de prueba, tienda y el usuario técnico `team5_demo_local` (inactivo). **No crea automáticamente una Wallet para tu superusuario**. Si el catálogo existente es incompatible, el comando se detiene sin sobrescribirlo: revisa los datos antes de borrarlos.

Abre <http://127.0.0.1:8000/> e inicia sesión con tu **superusuario** (cuenta `is_staff=True`). En la interfaz selecciona masculino o femenino para crear tu Ducky. El panel demo permite añadir XP y DuckyCoins y probar evolución, tienda, inventario y vestuario. Las acciones demo requieren `DEBUG=True`, acceso local (`127.0.0.1` o `localhost`), cuenta staff y la base `db_team5_demo.sqlite3`.

### 2.3 Si al añadir DuckyCoins aparece `WalletNotProvisioned`

**Error real observado:** `The user has no provisioned Bank wallet.` El seed creó una Wallet para el usuario técnico, pero **no para `henry`** (ni necesariamente para el superusuario que estés utilizando). La XP puede funcionar aunque la Wallet falte.

Abre **otra terminal** en la raíz del proyecto (o detén el servidor) y ejecuta:

```powershell
python manage.py shell --settings=config.settings_team5_demo
```

```python
from django.contrib.auth import get_user_model
from apps.bank.models import Wallet

usuario = get_user_model().objects.get(username="henry")  # cambia al nombre con que entraste
wallet, creada = Wallet.objects.get_or_create(user=usuario)
print("Wallet creada:", creada)
print("Saldo:", wallet.available_balance)
```

Sal con `exit()`, vuelve al navegador y pulsa **Añadir DuckyCoins**. Se registrará el crédito a través de `adjust_wallet()`. `get_or_create` no reinicia el saldo si la Wallet ya existe. **Esta es una reparación local de la V1; la integración definitiva debe aprovisionar la Wallet en el alta del usuario.**

### 2.4 Si aparece `Catálogos iniciales inválidos`

1. Comprueba que has aplicado la corrección de `STAGES` del apartado 2.1.
2. Comprueba los catálogos en la base demo:

```powershell
python manage.py shell --settings=config.settings_team5_demo
```

```python
from apps.ecomotor.models import EvolutionStage, LevelThreshold
print(list(EvolutionStage.objects.order_by('ordinal').values_list('ordinal', 'code', 'minimum_xp')))
print(list(LevelThreshold.objects.order_by('level').values_list('level', 'minimum_xp')))
```

Si ambos resultados son `[]`, los catálogos todavía no se han creado: ejecuta `setup_team5_demo` después de corregir el comando. Si contienen datos incompatibles, **no borres la base ni los perfiles sin respaldo**; la semilla rechaza sobrescribir catálogos existentes.

### 2.5 Añadir XP o DuckyCoins sin botones en la demo

Los ejemplos del apartado **1.3** (monedas) y **1.4** (XP) funcionan también en la demo cambiando el comando de consola por:

```powershell
python manage.py shell --settings=config.settings_team5_demo
```

Usa el nombre del usuario autenticado y asegúrate de que tenga Ducky/perfil y Wallet según corresponda. También puedes usar los controles del panel demo: **Añadir XP** o **Añadir DuckyCoins** (solo usuarios staff autorizados).

## 3. Comprobaciones y errores frecuentes

| Síntoma | Causa habitual | Qué hacer |
|---|---|---|
| `no such table` | Faltan migraciones en esa base | `python manage.py migrate` con los settings del servidor correspondiente |
| Login no acepta usuario | Superusuario creado en la otra base | `createsuperuser` con los mismos settings del `runserver` |
| No aparece panel demo | Estás en modo normal o no eres staff | Usar `--settings=config.settings_team5_demo`, entrar localmente y verificar `is_staff` |
| `Catálogos iniciales inválidos` | Catálogo vacío o distinto de la configuración | Revisar `STAGES`, `LevelThreshold` y seed; no borrar datos a ciegas |
| `WalletNotProvisioned` | Falta `Wallet` del usuario autenticado | Aprovisionar con `Wallet.objects.get_or_create(user=usuario)` en la demo; corregir alta en integración |
| La XP funciona pero las monedas no | Ecomotor inicializado, Bank no | Crear Wallet para **ese** usuario |
| Saldo no coincide con movimientos | Se editó directamente el campo | Evitar cambios directos; utilizar `adjust_wallet` y revisar historial |
| Puerto 8000 ocupado | Otro servidor sigue activo | Detenerlo o arrancar en `127.0.0.1:8001` |

### Comprobar datos y detener servidor

En el navegador: <http://127.0.0.1:8000/team5/>. En la terminal del servidor, `Ctrl+C` o `Ctrl+Break` para detenerlo. Puedes ejecutar:

```powershell
python manage.py check --settings=config.settings_team5_demo
python manage.py showmigrations --settings=config.settings_team5_demo
```

### Nota para Óscar / integración final

La demo contiene **datos sintéticos** y no establece reglas oficiales de progreso. El modo normal necesita configuración y catálogos autorizados por Ecomotor/Core, además del aprovisionamiento de Bank. Mantener separadas ambas bases evita que las concesiones de prueba se mezclen con datos reales. **La V1 no debe considerarse lista para producción**: aún requiere integración del alta, eliminación de duplicidad del comando demo y pruebas funcionales completas.
