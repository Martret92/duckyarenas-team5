# DuckyArena — Equipo 5
## Guía de acceso y pruebas de la interfaz local

**Destinatarios:** integrantes de Equipo 5 y compañeros que quieran revisar la integración de **Ecomotor, Duckies, Bank y Shop**.

> **Importante:** esta interfaz es una **demo local de desarrollo**, no la interfaz de producción ni la integración definitiva con Core. Se accede sin iniciar sesión, pero únicamente con `DEBUG=True` y desde `localhost` o `127.0.0.1`. **No publicarla en internet ni ejecutarla con una base de datos compartida o real.**

## 1. Requisitos

- Repositorio actualizado de DuckyArena Equipo 5 y entorno virtual `.venv` activado.
- Dependencias de Python del repositorio instaladas.
- Archivos de la interfaz añadidos al proyecto: `apps/duckies/team5_ui/`, `apps/duckies/templates/team5_ui/`, `apps/duckies/static/team5_ui/` y el comando `apps/duckies/management/commands/seed_team5_ui.py`.
- En `config/urls.py`, importar `include` y añadir esta ruta dentro de `urlpatterns`:

```python
path("team5/", include("apps.duckies.team5_ui.urls")),
```

## 2. Utilizar una base de datos de demostración independiente

El comando `seed_team5_ui` **no modifica automáticamente** un catálogo existente de Ecomotor si lo considera parcial o externo. Si aparece el mensaje `Catálogo Ecomotor parcial/externo...`, **no borrar datos ni migraciones**: crear una base de datos de demo independiente.

Crear `config/settings_team5_demo.py`:

```python
from .settings import *

DATABASES["default"]["NAME"] = BASE_DIR / "db_team5_demo.sqlite3"
DEBUG = True
```

Esta configuración está pensada para el repositorio con SQLite. Si el proyecto cambia de motor de base de datos, hay que adaptar la configuración. El archivo `settings_team5_demo.py` es una **configuración local adicional**; no forma parte obligatoria del paquete original.

Desde la raíz del repositorio, en PowerShell:

```powershell
python manage.py migrate --settings=config.settings_team5_demo
python manage.py seed_team5_ui --settings=config.settings_team5_demo
python manage.py runserver 127.0.0.1:8000 --settings=config.settings_team5_demo
```

Abrir en el navegador:

**http://127.0.0.1:8000/team5/**

> Mantener el servidor vinculado a `127.0.0.1`, **no** a `0.0.0.0`. El acceso sin login utiliza el usuario local `team5_demo_local`, compartido por quienes utilicen esa misma base de datos; para pruebas independientes, cada compañero debe usar su propia base de datos local.

## 3. Persistencia de datos y reinicio completo desde cero

### ¿Se pierde el progreso al cerrar el servidor?

**No.** Detener `runserver` con `Ctrl + C`, cerrar PowerShell/VS Code o reiniciar el ordenador **no borra** el progreso, siempre que vuelvas a ejecutar la demo con la misma configuración y el mismo archivo de base de datos (`db_team5_demo.sqlite3`). Se conservan la XP, las Ducky Coins, las compras, el inventario, las vestimentas, las especializaciones y el personaje creado.

| Acción | ¿Se conserva el progreso? |
|---|---|
| Detener y volver a iniciar `runserver` con los mismos settings | Sí |
| Cerrar VS Code o reiniciar el equipo | Sí |
| Ejecutar `migrate` sobre la misma base | Normalmente sí; no es un reinicio |
| Borrar `db_team5_demo.sqlite3` | **No: se pierde todo el progreso de esa demo** |
| Ejecutar con otra base de datos | Se verá el progreso de la base seleccionada, no el anterior |

### Reiniciar la interfaz completamente para repetir las pruebas

> **Advertencia:** este procedimiento **destruye definitivamente todos los datos de la demo**: personaje masculino/femenino, XP, monedas, compras, inventario, equipamiento, movimientos bancarios y progreso. **No borrar `db.sqlite3` ni otros archivos de bases de datos del equipo.** Si quieres conservar el estado actual, haz antes una copia de `db_team5_demo.sqlite3`.

**Paso 1.** Detener el servidor con `Ctrl + C` y situarse en la raíz del repositorio (`duckyarenas-team5`, donde está `manage.py`).

**Paso 2.** Comprobar que existe el archivo de configuración `config/settings_team5_demo.py` y que apunta a `BASE_DIR / "db_team5_demo.sqlite3"`. No continuar si apunta a otra base de datos.

**Paso 3.** Eliminar **únicamente** la base de datos de demostración. En PowerShell:

```powershell
Remove-Item .\db_team5_demo.sqlite3
```

Si PowerShell indica que no existe, comprobar la ruta y el nombre antes de continuar. **No sustituir el nombre por `db.sqlite3`.**

**Paso 4.** Reconstruir las tablas y volver a generar los datos iniciales:

```powershell
python manage.py migrate --settings=config.settings_team5_demo
python manage.py seed_team5_ui --settings=config.settings_team5_demo
```

**Paso 5.** Iniciar la interfaz:

```powershell
python manage.py runserver 127.0.0.1:8000 --settings=config.settings_team5_demo
```

**Paso 6.** Abrir **http://127.0.0.1:8000/team5/**. La demo empezará de nuevo desde los datos iniciales generados por `seed_team5_ui`. Podrás volver a crear el personaje y elegir masculino o femenino, probar XP, monedas, compras y equipamiento desde cero.

**Importante:** no hace falta ejecutar `seed_team5_ui` cada vez que inicias el servidor; solo al preparar por primera vez una base de datos nueva o al reconstruir la demo. El comportamiento del comando ante datos existentes depende de sus validaciones; no lo uses como método para reiniciar el progreso.

### Reinicio para probar ambos sexos

Como el sexo del Ducky se establece durante su creación y la interfaz no permite cambiarlo después, para probar **masculino** y luego **femenino** puedes reiniciar la base de datos de demo con el procedimiento anterior. Si necesitas conservar ambas pruebas, usa copias separadas de la base de datos o configura dos bases de demostración distintas.

## 4. Primera entrada

1. Abrir `/team5/`.
2. Entrar en **Mi Pato** y crear el Ducky de demostración, eligiendo **masculino** o **femenino**.
3. La inicialización usa la integración de Duckies con Ecomotor y prepara una Wallet local para el jugador de prueba.
4. **El sexo del Ducky no se puede cambiar después de crearlo** mediante esta interfaz, por contrato del backend. Para probar ambos personajes, usar bases de datos de demo separadas y nuevas.
5. Usar los enlaces del menú lateral para visitar las distintas secciones.

## 5. Funcionalidades que se pueden probar

| Sección | Qué hacer | Qué verificar |
|---|---|---|
| **Inicio** | Abrir el dashboard | Nombre del jugador, nivel, XP, etapa, especialización, monedas y resumen de inventario/equipamiento cuando existan datos. |
| **Mi Pato** | Inicializar el personaje masculino o femenino | Creación coherente de Ducky, perfil de progreso y Wallet de demo; no duplicar el personaje. |
| **Evolución** | Consultar etapas y añadir XP | Aumento de XP y nivel; avance de etapa cuando se alcanza el umbral; sincronización de vestimentas históricas. |
| **Especialización** | Elegir o cambiar especialización cuando se permita | Restricciones de desbloqueo; especialización activa y vestimenta correspondiente; conservación del progreso según las reglas del backend. |
| **Vestuario** | Seleccionar una vestimenta permitida | Se guarda la vestimenta seleccionada; las épocas futuras y las especializaciones ajenas deben seguir bloqueadas. |
| **Inventario** | Consultar objetos y pulsar **Equipar** en un objeto compatible | La operación usa Duckies; comprobar el equipamiento guardado. **Limitación actual:** el indicador visual de qué pieza está equipada es insuficiente y debe mejorarse. |
| **Museo** | Revisar épocas y progreso histórico | Visualización de etapas; no confundir una etapa visible con una desbloqueada. |
| **Tienda** | Comprar un objeto del catálogo | Descuento de monedas mediante Bank, registro de compra en Shop y entrega al inventario mediante Duckies. |
| **Banco** | Consultar saldo e historial; añadir monedas de prueba | El saldo aumenta mediante el servicio de Bank y las compras generan movimientos de débito. |
| **Arena** | Abrir la sección | Se informa de que los combates y efectos tácticos reales dependen de otras integraciones y no están implementados en esta demo. |

### Herramientas de prueba

La interfaz incluye acciones para:

- **Añadir XP**: ejecuta la operación de integración con Ecomotor; la etapa cambia por los umbrales de XP, **no** por una modificación manual arbitraria de la base de datos.
- **Añadir Ducky Coins**: utiliza `bank.services.credit_coins` y registra un crédito de prueba.
- **Elegir especialización**: utiliza los adaptadores de integración existentes y respeta sus validaciones.
- **Seleccionar vestimenta / equipar objeto**: utiliza servicios de Duckies.
- **Comprar**: utiliza `shop.services.purchase_item`, que coordina Shop, Bank y Duckies.

**Orden sugerido de demostración:** crear Ducky → añadir monedas → comprar un objeto → comprobar inventario y movimientos → equipar objeto → añadir XP → consultar nuevas etapas y vestimentas → elegir especialización cuando se desbloquee → probar restricciones.

## 6. Qué se ha comprobado y qué no

### Verificaciones automatizadas del backend realizadas anteriormente

En una versión anterior del repositorio se ejecutaron estos comandos con resultados satisfactorios:

| Comprobación | Resultado comunicado |
|---|---|
| `python manage.py check` | Sin incidencias |
| `python manage.py makemigrations --check --dry-run` | Sin cambios pendientes |
| Tests de integración Duckies/Ecomotor/Bank/Shop | **30/30** correctos |
| Tests Bank + Shop | **22/22** correctos |
| Tests Duckies | **47/47** correctos; incluyen los 30 de integración |
| Suite global | **1.294 ejecutados; 1.292 superados, 2 omitidos, 0 fallos** |

Estas cifras **no son pruebas ejecutadas sobre la última interfaz visual**. Se refieren a los resultados que el equipo obtuvo previamente sobre el backend. Las 30 pruebas de integración ya están incluidas en las 47 de Duckies: no se deben sumar como si fueran pruebas independientes.

### Qué permite observar la interfaz

La interfaz proporciona un recorrido manual para **comprobar visualmente** que los servicios de las cuatro aplicaciones trabajan juntos: XP y etapas de Ecomotor, personaje e inventario de Duckies, saldo y transacciones de Bank, y compras de Shop.

**No se afirma todavía que todos esos recorridos se hayan completado satisfactoriamente desde el navegador.** Cada compañero debe registrar sus resultados reales, errores y capturas. Los tests de servicios no sustituyen los tests de vistas ni las pruebas manuales de la interfaz.

### Limitaciones conocidas

- Las ilustraciones masculina y femenina son imágenes de demostración. **No se actualizan automáticamente** para reflejar cada objeto equipado o vestimenta histórica; el cambio se guarda en el backend y se presenta en datos de la interfaz.
- El inventario permite equipar, pero **todavía falta una indicación visual clara y completa de todas las piezas equipadas**, así como distinguir bien «Equipar» de «Equipado».
- El cambio de sexo después de crear el Ducky no está soportado.
- La especialización solo puede elegirse cuando las reglas de progresión lo permitan.
- Los efectos reales de objetos de ataque/defensa en batallas y la Arena dependen de otros equipos.
- La integración definitiva con Core y la plataforma principal no está validada por esta demo.
- Los catálogos generados por `seed_team5_ui` son **datos sintéticos de pruebas**, no el catálogo oficial de producción de Ecomotor.

## 7. Reemplazo de imágenes

Los recursos visuales se encuentran en:

```text
apps/duckies/static/team5_ui/img/
├── backgrounds/
│   └── castle.jpg
├── characters/
│   ├── ducky_male.png
│   └── ducky_female.png
└── items/
    ├── smoke.svg
    ├── options.svg
    ├── overclock.svg
    ├── shield.svg
    ├── filter.svg
    └── clock.svg
```

Para sustituir una imagen genérica por una definitiva, **conservar su ruta y nombre de archivo**. Así los templates existentes seguirán encontrándola sin cambios. Si se quieren ilustraciones diferentes para **cada vestimenta y combinación de equipamiento**, habrá que ampliar el mapeo de imágenes y la presentación del personaje: no basta con reemplazar las dos imágenes base.

## 8. Comprobaciones técnicas opcionales

Ejecutar contra la configuración de demo:

```powershell
python manage.py check --settings=config.settings_team5_demo
python manage.py makemigrations --check --dry-run --settings=config.settings_team5_demo
python manage.py test apps.duckies.tests.integration apps.bank apps.shop --settings=config.settings_team5_demo -v 1
```

Para una revisión completa del repositorio actualizado:

```powershell
python manage.py test --settings=config.settings_team5_demo -v 1
```

**Atención:** los tests de Django crean una base de datos de pruebas temporal. No confundir sus resultados con el estado de los datos que se ven en el navegador.

## 9. Errores habituales

**`Remove-Item` indica que la base de demo está en uso**: detener `runserver` y cerrar procesos que tengan abierta esa base antes de intentar el reinicio.

**`No migrations to apply`**: normal cuando todas las migraciones ya están aplicadas.

**`Catálogo Ecomotor parcial/externo`**: se está intentando preparar la demo en una base con datos preexistentes incompatibles. Usar una base SQLite demo nueva, **sin borrar el catálogo de Jaime**.

**404 en `/team5/`**: comprobar que se ha añadido la ruta en `config/urls.py`, que `DEBUG=True` y que se accede desde `localhost` o `127.0.0.1`.

**La compra falla por saldo insuficiente**: añadir Ducky Coins desde Banco y repetir la compra.

**No se puede elegir una especialización o vestimenta**: comprobar los requisitos de etapa, especialización activa y objetos desbloqueados.

**El objeto se equipa pero no se ve sobre el dibujo del Ducky**: limitación de representación gráfica, no prueba por sí sola de un fallo del servicio. Consultar el estado del inventario/equipamiento y anotar la incidencia visual.

## 10. Registro de pruebas del equipo

Cada miembro puede documentar los resultados con esta tabla:

| Fecha | Persona | Flujo probado | Resultado (OK/Error) | Evidencia o incidencia |
|---|---|---|---|---|
| | | Creación de Ducky masculino | | |
| | | Creación de Ducky femenino (BD nueva) | | |
| | | Añadir XP y avanzar etapa | | |
| | | Elegir/cambiar especialización | | |
| | | Comprar y recibir objeto | | |
| | | Equipar y consultar objeto | | |
| | | Añadir monedas y revisar movimientos | | |
| | | Restricciones de vestimenta | | |

---

**Resumen:** la interfaz local permite que los integrantes del Equipo 5 recorran las funciones disponibles de Ecomotor, Duckies, Bank y Shop desde el navegador, sin iniciar sesión y sin modificar los templates originales. Es una herramienta de integración y demostración; **no sustituye la validación funcional, visual ni de seguridad de la futura versión de producción**.
