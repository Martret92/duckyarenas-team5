# DuckyArena — Equipo 5
## Guía de instalación, acceso y pruebas de la integración local

> **Ámbito:** versión `DuckyArena_Equipo5_Imagenes_Integradas.zip`. Esta guía describe el entorno de demostración local del Equipo 5; **no** es una guía de despliegue ni sustituye la integración oficial de Core.

## 1. ¿Qué se puede probar?

La interfaz permite recorrer las secciones **Inicio, Mi Pato, Evolución, Especialización, Vestuario, Inventario, Museo, Tienda, Banco, Rewards y Arena**. Entre los flujos implementados para probar en local están:

- Registro de usuario e inicio/cierre de sesión.
- Creación del Ducky y selección de sexo para sus variantes visuales.
- Progresión por XP y consulta de nivel/época.
- Selección de especialización y vestimentas disponibles.
- Catálogo de Shop, compra de objetos con DuckyCoins, inventario y equipamiento.
- Visualización de imágenes de personajes y variantes de ítems asociadas a la vestimenta seleccionada.
- Consulta del saldo y movimientos de Wallet.

**Alcance:** algunas secciones pueden funcionar como vista informativa o enlace a otros módulos. Las variantes visuales y la integración completa deben verificarse en ejecución; la existencia de archivos de imagen no garantiza por sí sola que todas las pantallas se actualicen correctamente.

## 2. Requisitos

- Python instalado (el repositorio de referencia indica Python 3.12).
- PowerShell en Windows, o una terminal equivalente.
- Archivo ZIP del proyecto descomprimido.
- Dependencias de `requirements.txt` (el repositorio fija Django 5.2.17).

Abre PowerShell **dentro de la carpeta que contiene `manage.py`**.

## 3. Instalación inicial en Windows (PowerShell)

Se recomienda usar directamente el ejecutable de Python del entorno virtual para evitar problemas con la política de ejecución de PowerShell.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check --settings=config.settings_team5_local
.\.venv\Scripts\python.exe manage.py migrate --settings=config.settings_team5_local
.\.venv\Scripts\python.exe manage.py team5_setup_local --settings=config.settings_team5_local
```

**¿Qué hace cada comando?**

1. `venv` crea un entorno Python aislado.
2. `pip install` instala las dependencias.
3. `check` revisa la configuración de Django.
4. `migrate` prepara las tablas en la base de datos local.
5. `team5_setup_local` carga el catálogo sintético de épocas, niveles, especializaciones y vestimentas.

La configuración `config.settings_team5_local` usa la base **`db_team5_local.sqlite3`**, separada de la base SQLite normal del proyecto. También activa la preparación local del catálogo Shop. **No ejecutar estos comandos con los settings oficiales o de producción.**

## 4. Cómo entrar: registro normal o `createsuperuser`

### Opción A: crear una cuenta desde la web

1. Arranca el servidor siguiendo el apartado 5.
2. Abre `http://127.0.0.1:8000/accounts/register/`.
3. Completa el formulario de registro.
4. La aplicación inicia sesión con la cuenta recién creada y te redirige al inicio.
5. En **Mi Pato**, crea el Ducky si aún no existe.

### Opción B: crear un superusuario desde la terminal

También se puede acceder con una cuenta creada mediante `createsuperuser`:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser --settings=config.settings_team5_local
```

Django pedirá **nombre de usuario, correo electrónico (según configuración) y contraseña**. 


En caso de elegir la opcion A, Después:

- Accede a `http://127.0.0.1:8000/accounts/login/` con ese usuario y contraseña para utilizar la interfaz del Equipo 5.
- Accede a `http://127.0.0.1:8000/admin/` con las mismas credenciales para entrar al panel de administración de Django.
- Si el superusuario todavía no tiene un Ducky, entra en **Mi Pato** y créalo desde la interfaz.

**Importante:** ser superusuario **no implica** tener automáticamente XP, DuckyCoins, objetos comprados o todas las vestimentas desbloqueadas. Para probar esos casos se usan los comandos locales del apartado 7.

## 5. Si has elegido la opcion B, iniciar el servidor y navegar

```powershell
.\.venv\Scripts\python.exe manage.py runserver --settings=config.settings_team5_local
```

Abre `http://127.0.0.1:8000/`.

Rutas útiles:

| Ruta | Uso |
| --- | --- |
| `/` | Inicio / panel del Equipo 5 |
| `/accounts/register/` | Registro |
| `/accounts/login/` | Inicio de sesión |
| `/admin/` | Administración de Django (superusuario) |
| `/player/` | Mi Pato |
| `/evolution/` | Evolución |
| `/specialization/` | Especialización |
| `/wardrobe/` | Vestuario |
| `/inventory/` | Inventario |
| `/shop/` | Tienda |
| `/wallet/` | Banco / Wallet |
| `/museum/` | Museo |
| `/rewards/` | Rewards |
| `/arena/` | Arena |

Para detener el servidor: **Ctrl + C** en la terminal.

## 6. Flujo de prueba recomendado

1. **Crear usuario** mediante registro o `createsuperuser` e iniciar sesión.
2. **Crear el Ducky** desde Mi Pato, eligiendo la variante de personaje disponible.
3. **Consultar evolución** y comprobar el estado inicial de XP, nivel y época.
4. **Conceder XP localmente** con el comando del apartado 7; volver a Evolución y revisar el progreso.
5. **Seleccionar una vestimenta** desbloqueada desde Vestuario y comprobar que cambia el aspecto del personaje.
6. **Elegir una especialización** cuando el flujo lo permita; revisar la vestimenta correspondiente.
7. **Conceder DuckyCoins localmente** y verificar el saldo en Banco.
8. **Entrar en Tienda**, comprar un objeto y comprobar que se descuenta el importe.
9. **Abrir Inventario**, verificar que aparece la compra e intentar equipar el objeto.
10. **Cambiar de vestimenta** y comparar las imágenes de los objetos en Tienda e Inventario. Debe cambiar la **representación visual**, no la propiedad del artículo, el saldo ni sus características.

Los objetos comprados siguen perteneciendo al usuario al cambiar de época o especialización. Algunas imágenes son genéricas provisionales para completar las variantes todavía no diseñadas.

## 7. Comandos para pruebas: XP y DuckyCoins

Abre **otra terminal** en la carpeta del proyecto; el servidor puede seguir ejecutándose en la primera.

### Conceder 500 XP

```powershell
.\.venv\Scripts\python.exe manage.py team5_grant_xp --username TU_USUARIO --amount 500 --settings=config.settings_team5_local
```

### Conceder 1.000 DuckyCoins

```powershell
.\.venv\Scripts\python.exe manage.py team5_grant_coins --username TU_USUARIO --amount 1000 --settings=config.settings_team5_local
```

Sustituye `TU_USUARIO` por el nombre de usuario real, también si has usado `createsuperuser`. Ambos comandos **añaden** la cantidad indicada; no establecen un saldo o XP total fijo. Solo aceptan importes positivos hasta 1.000.000 y exigen el entorno local.

- **XP:** se concede a través del servicio de integración con Ecomotor.
- **DuckyCoins:** se conceden a través de Bank, que es la fuente de verdad del saldo de Wallet.
- **No** existen botones ordinarios de usuario para regalar XP o monedas en la interfaz.

> Estos comandos son herramientas de desarrollo. No deben habilitarse como funcionalidad pública ni ejecutarse contra la base oficial.

## 8. Imágenes y variantes visuales

La versión con imágenes integradas incorpora vestimentas masculinas/femeninas y variantes de ítems por época y especialización. Las rutas principales son:

```text
apps/duckies/static/team5_ui/img/outfits/
apps/duckies/static/team5_ui/img/items/variants/
apps/duckies/team5_ui/image_registry.py
apps/duckies/item_visual_variants.json
apps/duckies/item_visuals.py
```

La selección de vestimenta determina una clave visual; el sistema busca la imagen específica del ítem y, cuando no está disponible, recurre a una imagen por defecto. **El cambio de imagen no crea ni compra otro objeto**.

Para revisar la funcionalidad, cambia entre dos vestimentas, abre Tienda e Inventario y comprueba tanto las imágenes como que el inventario y el saldo siguen siendo coherentes.

## 9. Problemas frecuentes

| Problema | Qué comprobar |
| --- | --- |
| `No module named django` | Ejecutar con `.\.venv\Scripts\python.exe` e instalar `requirements.txt`. |
| `no such table` o errores de base de datos | Ejecutar `migrate` con `--settings=config.settings_team5_local`. |
| No aparecen épocas o vestimentas | Ejecutar `team5_setup_local` con los settings locales. |
| No aparecen objetos en Shop | Confirmar que se han ejecutado las migraciones locales; revisar la carga del catálogo Shop y los registros disponibles. |
| El usuario no puede comprar | Comprobar que tiene Ducky, que la oferta está disponible y que Wallet dispone de saldo. |
| No cambia una imagen | Comprobar la vestimenta seleccionada, las rutas del registro visual y la existencia del archivo estático correspondiente. |
| No puedo acceder a `/admin/` | Usar un superusuario creado en **esta misma base local**. |
| `Port is already in use` | Detener el otro servidor o arrancar con `runserver 8002 --settings=config.settings_team5_local`; sustituir `8000` por `8002` en las URLs de acceso. |

Si se usa otro puerto, los enlaces absolutos a servicios externos de demostración pueden seguir apuntando al puerto configurado originalmente.

## 10. Límites y precauciones de integración

- Este entorno **no es producción** y utiliza catálogos sintéticos para facilitar pruebas.
- El registro y login locales no sustituyen el sistema definitivo de autenticación de Core.
- El resultado de `git merge-tree` sin conflictos indica compatibilidad de fusión **a nivel Git**, no garantiza compatibilidad funcional entre módulos.
- Antes de integrar en `develop`, revisar las diferencias, ejecutar pruebas automatizadas y comprobar los flujos con los demás equipos.
- Evitar subir al repositorio la base local (`db_team5_local.sqlite3`), el entorno `.venv`, credenciales o datos de prueba sensibles.
- El catálogo, la economía, los contratos y la configuración oficial deben seguir las decisiones acordadas con los equipos propietarios.

## 11. Comprobación rápida antes de comunicar que funciona

- [ ] Se instalan las dependencias y `check` no da errores.
- [ ] Migraciones y catálogo local completados.
- [ ] Registro de usuario y login con `createsuperuser` comprobados.
- [ ] Creación de Ducky y evolución con XP comprobadas.
- [ ] Selección de vestimentas y especializaciones comprobada.
- [ ] Wallet, compra, inventario y equipamiento comprobados.
- [ ] Cambio de imágenes según vestimenta comprobado en las pantallas correspondientes.
- [ ] No hay regresiones detectadas al integrar con los demás módulos.

---

**Nota para el equipo:** la guía documenta las rutas, comandos y flujos presentes en el ZIP inspeccionado. Las comprobaciones marcadas arriba deben realizarse en un entorno Django real antes de considerar validada la integración completa.
