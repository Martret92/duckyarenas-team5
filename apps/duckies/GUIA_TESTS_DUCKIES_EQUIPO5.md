# Guía de pruebas de Duckies — Equipo 5

> **Objetivo:** permitir que cualquier integrante del Equipo 5 ejecute las pruebas de backend y compruebe visualmente la interfaz de Duckies, incluidas las vestimentas históricas y las especializaciones.
>
> **Ámbito:** entorno **local de desarrollo**. El servidor `127.0.0.1:8000` no es un despliegue remoto. Los comandos de demostración no deben utilizarse en producción.

## 1. Dos tipos de pruebas: diferencias

| Tipo | Cómo se ejecuta | Qué permite comprobar | Qué no demuestra por sí solo |
| --- | --- | --- | --- |
| **Automatizadas (backend)** | `python manage.py test apps.duckies.tests` | Reglas de negocio y escenarios incluidos en los tests, operaciones de modelos/servicios/vistas y comandos de prueba | Que todas las imágenes, estilos y botones se vean correctamente o que las cuatro apps estén integradas |
| **Manuales (templates/UI)** | Preparar datos demo, `runserver`, abrir el navegador | Renderizado, navegación, imágenes, formularios, estados bloqueados/desbloqueados y experiencia visual | Cobertura automática, seguridad completa, evolución real de Ecomotor o pagos de Shop/Bank |

**Importante:** el testeo visual es una **comprobación manual**, no una segunda batería de tests automáticos. Ambos métodos se complementan.

## 2. Requisitos previos

Desde la raíz del repositorio (donde está `manage.py`):

```powershell
# Activar entorno virtual en Windows PowerShell (si no está activo)
.\.venv\Scripts\Activate.ps1

# Comprobar instalación y configuración
python manage.py check
python manage.py migrate
```

Se requiere que las dependencias del proyecto estén instaladas, la base de datos de desarrollo configurada y las apps Django habilitadas. Para la demostración debe estar `DEBUG=True`. Si una orden indicada en esta guía no aparece en vuestra rama, primero hay que incorporar el código de demo correspondiente.

## 3. Pruebas automatizadas del backend

### 3.1. Ejecutarlas

```powershell
python manage.py test apps.duckies.tests
```

En la ejecución documentada se obtuvo:

```text
Found 27 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...
Ran 27 tests in 12.544s

OK
Destroying test database for alias 'default'...
```

**Interpretación:** se descubrieron 27 pruebas y las 27 terminaron sin fallos ni errores. El número puede cambiar si se añaden o eliminan tests. `OK` solo confirma los escenarios efectivamente implementados en esos tests.

### 3.2. Qué se pretende validar

- **Ducky y usuario:** creación/inicialización y reglas básicas del personaje.
- **Evolución histórica:** relación de vestimentas con las etapas, selección permitida y restricciones según el progreso.
- **Especializaciones:** asociación de la vestimenta con la especialización activa y rechazo de selecciones no autorizadas, en los escenarios cubiertos por los tests.
- **Inventario:** concesión de objetos y reglas de operaciones, en los escenarios incluidos.
- **Equipamiento y objetos tácticos:** selección, niveles y uso según la cobertura implementada.
- **Vistas/comandos de demostración:** respuestas y preparación de datos, cuando tengan pruebas específicas.

Para conocer la **cobertura exacta** y las aserciones, revisar `apps/duckies/tests/` de la rama ejecutada. Esta guía no presupone que todas las variantes de cada funcionalidad tengan un test.

### 3.3. Avisos sobre especializaciones no registradas

Es posible ver mensajes como:

```text
Especialización DEVELOPER no registrada en Ecomotor. Se omite.
Especialización GAMER no registrada en Ecomotor. Se omite.
Especialización CIBER no registrada en Ecomotor. Se omite.
Especialización SISTEMAS no registrada en Ecomotor. Se omite.
Especialización DATA_IA no registrada en Ecomotor. Se omite.
Catálogo Duckies procesado: 7 históricos, 6 tácticos, 18 niveles y 0 especializaciones vinculadas.
Pendientes en Ecomotor: DEVELOPER, GAMER, CIBER, SISTEMAS, DATA_IA
```

**No es necesariamente un error.** Django crea una **base de datos temporal** para los tests. Si el test ejecuta el seed sin crear previamente especializaciones de Ecomotor, el seed informa de que no puede vincularlas. Si el resultado final es `OK`, los tests han aceptado ese comportamiento. **No implica que se hayan eliminado las especializaciones de la base de datos habitual.**

También pueden aparecer mensajes de creación, repetición y limpieza de las siete etapas demo: corresponden a las pruebas de los comandos de preparación.

### 3.4. Volver a ejecutar tras cambios

```powershell
python manage.py test apps.duckies.tests --verbosity 2
```

`--verbosity 2` muestra más información sobre cada test. Recomendado antes de crear un pull request y después de modificar modelos, servicios, vistas o reglas de especialización.

## 4. Pruebas manuales de templates y flujo visual

### 4.1. Preparar los datos demo

Ejecutar **en este orden** desde la raíz:

```powershell
python manage.py migrate
python manage.py prepare_duckies_demo_stages
python manage.py prepare_duckies_demo_specializations
python manage.py seed_duckies
python manage.py demo_duckies --username demo_duckies
```

En el entorno de desarrollo ya probado, la preparación produjo **7 vestimentas históricas, 5 especializaciones vinculadas, 6 objetos tácticos y 18 niveles de objetos**. Si `seed_duckies` indica **0 especializaciones vinculadas**, comprobar primero que el comando de especializaciones se ejecutó correctamente y que sus códigos coinciden con los de Ecomotor.

**Precaución:** estos comandos alteran datos **de demostración** de la base local. No ejecutarlos sobre una base de datos real o compartida sin revisar su implementación. El comando `demo_duckies` requiere `DEBUG=True`; no modifica deliberadamente XP ni Bank.

### 4.2. Arrancar y entrar

```powershell
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/` y entrar en las páginas de Duckies mediante sus enlaces o rutas configuradas en `apps/duckies/urls.py`.

Usuario demo creado por defecto:

```text
Usuario: demo_duckies
Contraseña: DuckyDemo2026!
```

**La contraseña predeterminada es solo para desarrollo.** Si el usuario ya existía, `demo_duckies` no necesariamente le cambia la contraseña. No subir contraseñas personales, `.env` ni bases de datos locales a GitHub.

### 4.3. Checklist de navegación

- [ ] **Setup:** permite inicializar/consultar el personaje según el estado del usuario.
- [ ] **Dashboard:** muestra el Ducky, su vestimenta actual, su imagen y los datos disponibles.
- [ ] **Museo histórico:** aparecen las siete etapas y sus imágenes.
- [ ] **Museo de especializaciones:** aparecen Developer, Gamer, Ciber, Sistemas y Data IA con sus imágenes.
- [ ] **Inventario:** se ven los objetos tácticos concedidos por el comando demo.
- [ ] **Equipamiento:** se pueden comprobar los objetos equipados y los mensajes de las acciones.
- [ ] **Navegación:** enlaces, formularios, redirecciones y mensajes funcionan.
- [ ] **Diseño:** imágenes sin rutas rotas, CSS cargado y visualización aceptable en móvil y escritorio.

### 4.4. Probar las restricciones históricas

**Estado inicial:** el usuario demo suele empezar en la primera etapa (`PREHISTORICO` o el código equivalente definido por Ecomotor), sin especialización activa. En ese estado, **no debería poder seleccionar vestimentas de etapas posteriores**. Que aparezcan bloqueadas es un resultado esperado, no un fallo.

Para simular otra etapa, modificar **solo el usuario demo** desde Django Shell, comprobando antes los códigos reales:

```powershell
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from apps.users.models import UserProfileEcomotor
from apps.ecomotor.models import EvolutionStage

print(list(EvolutionStage.objects.order_by('ordinal').values_list('code', flat=True)))
user = get_user_model().objects.get(username='demo_duckies')
profile = UserProfileEcomotor.objects.get(user=user)

# Sustituir por el código exacto que devuelva la consulta anterior.
profile.current_stage_code = 'SIGLO_XX'
profile.save(update_fields=['current_stage_code'])
```

Actualizar el Museo y comprobar los estados. **No se está otorgando XP ni ejecutando el motor real de evolución**: solo se está simulando el dato de progreso que consume Duckies.

### 4.5. Probar las cinco especializaciones

Consultar primero los códigos existentes en Ecomotor:

```python
from apps.ecomotor.models import Specialization
print(list(Specialization.objects.values_list('code', flat=True)))
```

Con el usuario demo y el `profile` del apartado anterior:

```python
profile.active_specialization_code = 'DEVELOPER'
profile.save(update_fields=['active_specialization_code'])
```

Actualizar el Museo. Comprobar que:

- [ ] La vestimenta **Developer** queda disponible cuando `DEVELOPER` es la especialización activa.
- [ ] Las vestimentas de **Gamer, Ciber, Sistemas y Data IA** siguen sin poder seleccionarse con `DEVELOPER` activo.
- [ ] Se puede seleccionar la vestimenta Developer desde el Museo.
- [ ] Las vestimentas históricas permitidas por la regla de progreso siguen siendo seleccionables.

Repetir la prueba, **una especialización cada vez**, cambiando el valor a `GAMER`, `CIBER`, `SISTEMAS` y `DATA_IA` (si esos son los códigos reales de la rama):

```python
profile.active_specialization_code = 'GAMER'
profile.save(update_fields=['active_specialization_code'])
```

**Importante:** cambiar manualmente `active_specialization_code` no equivale al cambio real de especialización gestionado por Ecomotor y **no prueba la sincronización automática de la vestimenta**. Ese comportamiento está pendiente de la integración definitiva.

### 4.6. Probar imágenes masculina y femenina

El comando demo permite elegir sexo al crear un usuario nuevo:

```powershell
python manage.py demo_duckies --username demo_duckies_female --sex female
```

Usar ese segundo usuario para revisar las imágenes de las siete etapas y cinco especializaciones en versión femenina. Alternativamente, en una **base demo**, se puede editar el campo `sex` de un Ducky existente desde Django Shell. No hacerlo con datos reales de usuarios.

### 4.7. Inventario y equipamiento

El comando `demo_duckies` concede objetos tácticos de nivel 1 al usuario demo (según la implementación de la rama). Comprobar visualmente:

- [ ] Se muestran los seis tipos de objetos previstos y sus imágenes.
- [ ] El inventario presenta las cantidades correspondientes.
- [ ] Las acciones de equipar o consumir se comportan según las reglas de los servicios.
- [ ] No se pueden realizar acciones prohibidas y se informa correctamente al usuario.

**No confundir** la concesión de objetos de demostración con una compra real en Shop ni con una operación monetaria en Bank.

## 5. Qué está probado y qué queda pendiente de integrar

| Funcionalidad | Estado que puede afirmarse |
| --- | --- |
| Ejecución de la batería actual de Duckies | **27/27 OK** en la ejecución documentada |
| Preparación local del catálogo | **Ejecutada correctamente** con 7 históricos, 5 especializaciones, 6 tácticos y 18 niveles |
| Arranque del servidor de desarrollo | **Comprobado** sin errores del system check |
| Interfaz completa de todos los escenarios | **Requiere checklist manual**; no se demuestra con `OK` |
| Evolución y XP reales de Ecomotor | **Pendiente de prueba integrada** |
| Cambio real de especialización y autoequipado condicionado | **Pendiente de implementación/integración definitiva** |
| Compra y concesión desde Shop | **Pendiente de integración** |
| Saldo y operaciones de Bank | **Pendiente de integración** |
| Flujo completo de las cuatro apps | **Pendiente de prueba extremo a extremo** |

### Regla acordada para la futura sincronización de especialización

Cuando Ecomotor implemente el cambio de especialización:

1. Si el Ducky lleva puesta la **vestimenta de la especialización anterior**, Duckies deberá sustituirla automáticamente por la **nueva especialización activa**.
2. Si lleva puesta una **vestimenta histórica**, debe **conservarla**.
3. Ecomotor sigue siendo responsable del cambio de especialización y del progreso/XP; Duckies solo sincroniza la vestimenta.

**Esta regla no debe darse por validada solo por los 27 tests actuales.** Necesita implementación y pruebas específicas con la API definitiva de Ecomotor.

## 6. Problemas habituales

| Síntoma | Posible explicación / acción |
| --- | --- |
| El Ducky está en Prehistórico y no deja cambiar | Es la restricción prevista para un perfil inicial; simular progreso con el apartado 4.4 |
| Las especializaciones aparecen bloqueadas | El perfil no tiene `active_specialization_code` o no coincide con el código de Ecomotor |
| `seed_duckies` vincula 0 especializaciones en la demo | Ejecutar `prepare_duckies_demo_specializations` antes de `seed_duckies` y revisar códigos |
| Durante `manage.py test` aparecen 0 especializaciones | Puede ser normal en la **base temporal** del test; mirar el resultado final y las aserciones |
| No aparecen imágenes | Revisar archivos bajo `apps/duckies/static/duckies/images/`, rutas de `image_registry.py` y `{% load static %}` |
| La contraseña demo no funciona | Puede existir un usuario anterior cuya contraseña no fue reemplazada; revisar el comando demo |
| El test backend pasa pero un botón visual falla | Son verificaciones distintas: revisar template, URL, vista, formulario y mensajes |

## 7. Cómo colaborar y comunicar resultados

Antes de hacer un pull request:

```powershell
python manage.py check
python manage.py test apps.duckies.tests
```

Compartir en el PR: rama y commit probados, número de tests ejecutados, resultado (`OK` o error), checklist visual realizado y cualquier dependencia pendiente de Ecomotor/Shop/Bank.

**Resumen para el Equipo 5:** Duckies tiene una batería automatizada que ha superado **27 tests** y una demo local para revisar templates, siete etapas, cinco especializaciones e inventario. La demo permite **simular** estados de Ecomotor, pero no sustituye las pruebas reales de integración entre las cuatro aplicaciones.
