# DuckyArena — Equipo 5
## Guía rápida para iniciar y probar la interfaz local

Esta guía explica **únicamente cómo poner en marcha la interfaz y utilizarla** para probar personajes, XP, DuckyCoins, evolución, vestuario, compras e inventario.

> **Importante:** utilizar siempre `--settings=config.settings_team5_local`. Este entorno usa `db_team5_local.sqlite3`, una base de datos independiente de la configuración oficial. Los comandos de XP y DuckyCoins son exclusivamente para demostraciones locales.

## 1. Preparar el proyecto (primera vez)

Abrir PowerShell en la carpeta del repositorio que contiene `manage.py`.

Si todavía no existe el entorno virtual:

```powershell
py -m venv .venv
```

Instalar las dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Preparar la base de datos y los datos de demostración:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --settings=config.settings_team5_local
.\.venv\Scripts\python.exe manage.py team5_setup_local --settings=config.settings_team5_local
```

Estos dos últimos comandos preparan las tablas y los catálogos locales necesarios para probar la interfaz. **No es necesario repetirlos cada vez que se inicia el servidor** si el entorno ya está preparado.

## 2. Crear un usuario

Hay dos formas de acceder:

**Opción A — Registro desde la interfaz:** iniciar el servidor (apartado 3), abrir `http://127.0.0.1:8000/accounts/register/` y registrar un usuario normal.

**Opción B — Crear un superusuario desde PowerShell:** (recomendado)

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser --settings=config.settings_team5_local
```

Introducir el nombre de usuario, correo electrónico si se solicita y contraseña. Después se puede iniciar sesión en `http://127.0.0.1:8000/accounts/login/`. El panel administrativo de Django está en `http://127.0.0.1:8000/admin/`.

**Crear un superusuario no crea automáticamente el Ducky ni concede XP o DuckyCoins.** Hay que crear el personaje desde la interfaz y añadir recursos de prueba con los comandos del apartado 5.

## 3. Iniciar la interfaz con `runserver`

Ejecutar:

```powershell
.\.venv\Scripts\python.exe manage.py runserver --settings=config.settings_team5_local
```

Abrir en el navegador:

**http://127.0.0.1:8000/**

Iniciar sesión con el usuario creado. Para detener el servidor, pulsar **Ctrl + C** en esa terminal.

En los siguientes usos, si la base de datos ya está preparada, basta con ejecutar el comando `runserver` anterior.

## 4. Crear el Ducky y entrar en las secciones

1. Iniciar sesión.
2. Abrir **Mi Pato** (`/player/`).
3. Crear el Ducky y seleccionar la variante masculina o femenina cuando se ofrezca.
4. Navegar por las secciones desde el menú de la interfaz.

| Sección | Dirección local |
| --- | --- |
| Inicio | `http://127.0.0.1:8000/` |
| Mi Pato | `http://127.0.0.1:8000/player/` |
| Evolución | `http://127.0.0.1:8000/evolution/` |
| Especialización | `http://127.0.0.1:8000/specialization/` |
| Vestuario | `http://127.0.0.1:8000/wardrobe/` |
| Inventario | `http://127.0.0.1:8000/inventory/` |
| Tienda (Shop) | `http://127.0.0.1:8000/shop/` |
| Banco (Wallet) | `http://127.0.0.1:8000/wallet/` |
| Museo | `http://127.0.0.1:8000/museum/` |
| Rewards | `http://127.0.0.1:8000/rewards/` |
| Arena | `http://127.0.0.1:8000/arena/` |

## 5. Añadir DuckyCoins y XP de prueba

**Dejar el servidor ejecutándose en la primera terminal.** Abrir una **segunda terminal PowerShell** en la carpeta del proyecto para introducir los siguientes comandos.

Sustituir `TU_USUARIO` por el nombre de usuario con el que se ha iniciado sesión, tanto si es normal como si es superusuario.

### Añadir 1.000 DuckyCoins

```powershell
python manage.py team5_grant_coins --username TU_USUARIO --amount 1000 --settings=config.settings_team5_local
```

Volver a la página **Banco** (`/wallet/`) y actualizar el navegador para ver el saldo. Las monedas se gestionan en **Bank/Wallet**.

### Añadir 500 XP

```powershell
python manage.py team5_grant_xp --username TU_USUARIO --amount 500 --settings=config.settings_team5_local
```

Volver a **Mi Pato** y **Evolución** y actualizar el navegador para consultar la progresión. Los desbloqueos dependen de los umbrales de la configuración local.

**Notas:** ambos comandos **suman** la cantidad indicada; no establecen un total fijo. Se pueden repetir con cantidades positivas dentro del límite permitido. No existen botones de concesión de XP o monedas en la interfaz normal.

## 6. Recorrido práctico para probar la interfaz

1. **Personaje:** crear el Ducky desde **Mi Pato** y comprobar su imagen y estadísticas.
2. **XP y evolución:** conceder XP con el comando anterior; actualizar **Evolución** y revisar el nivel, la época y los desbloqueos disponibles.
3. **Especialización:** abrir **Especialización** y seleccionar una opción cuando el nivel y los requisitos lo permitan.
4. **Vestuario:** abrir **Vestuario**, seleccionar una vestimenta disponible y comprobar el cambio de apariencia del personaje.
5. **Banco:** conceder DuckyCoins, abrir **Banco** y comprobar el saldo.
6. **Tienda:** abrir **Shop**, elegir un artículo disponible y comprarlo. Comprobar el historial de compras y el descuento del saldo en Bank.
7. **Inventario:** abrir **Inventario**, comprobar que aparece el artículo comprado y equiparlo si está disponible esa opción.
8. **Variantes visuales:** cambiar de vestimenta y volver a **Shop** e **Inventario**. Las imágenes de los objetos pueden adaptarse a la vestimenta activa, pero el artículo comprado sigue siendo el mismo y no hay que recomprarlo.
9. **Persistencia:** detener el servidor, volver a arrancarlo con `runserver` e iniciar sesión. Comprobar que se conservan el saldo, los artículos y las selecciones guardadas.

Algunas secciones, como Rewards o Arena, pueden mostrar contenido informativo o depender de integraciones pendientes; esta guía no presupone que todas sus funciones estén habilitadas.

## 7. Problemas habituales

| Problema | Qué hacer |
| --- | --- |
| No se encuentra Django | Ejecutar los comandos con `.\.venv\Scripts\python.exe` e instalar `requirements.txt`. |
| Error `no such table` | Ejecutar `migrate` con `--settings=config.settings_team5_local`. |
| No aparecen épocas o vestimentas | Ejecutar `team5_setup_local` con los settings locales y actualizar la página. |
| No se puede iniciar sesión | Verificar que el usuario se creó con `config.settings_team5_local`. |
| No aparece el Ducky | Entrar en **Mi Pato** y crearlo desde la interfaz. |
| No hay saldo para comprar | Ejecutar `team5_grant_coins` para el usuario correcto y actualizar **Banco**. |
| No se observa progresión | Comprobar que el comando `team5_grant_xp` terminó correctamente y actualizar **Evolución**. |
| El puerto 8000 está ocupado | Detener el servidor anterior o arrancar en otro puerto: `... manage.py runserver 8001 --settings=config.settings_team5_local`. |

---

**Resumen para los siguientes arranques:** abrir PowerShell en la raíz del proyecto, ejecutar `runserver` con `config.settings_team5_local`, entrar en `http://127.0.0.1:8000/` y, cuando sea necesario, usar otra terminal para conceder XP o DuckyCoins de prueba.
