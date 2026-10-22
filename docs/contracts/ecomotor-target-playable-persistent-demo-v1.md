# A4-TARGET-PERSIST-DEMO-01 · Opciones y estadísticas persistentes de demo

Aprobación **interna de Equipo 5 / 02C-2 del 22/10/2026**. Implementación para
revisión en 01B sobre develop `9e1a66a8fcd081306e0abc6bbcb4925f683cf463`, que
incluye PR #96 de Henry. DAR3 conserva autoridad funcional. No es autorización
productiva, USE-01B, TRACE-01B ni integración con Core o Duckies.

## Entorno y antecedentes

Extiende el [Paso 2](ecomotor-target-persistent-demo-v1.md) en su misma app,
SQLite exclusiva `instance/target_persistent_demo.sqlite3`, sesiones, backend,
settings y ruta `/demo/objetivo-persistente/`. Se conservan el aislamiento físico,
la apertura `mode=rw` (solo migrate puede crear), IMMEDIATE/timeout=5 y el runner
de dos fases. La [demo #94](ecomotor-target-demo-v1.md) permanece independiente.
El escritor XP del Paso 2 y sus eventos no se modifican.

## Esquema local

Migración `ecomotor_target_demo.0002_playable_configurations`, dependiente de
`ecomotor_target_demo.0001_initial` y `ecomotor.0007_target_catalog_freeze`.
Django 5.2/SQLite: tres CreateModel, constraints, sin datos ni RunPython.

| Entidad | Contenido y restricciones |
| --- | --- |
| DemoTargetOptionConfiguration | BigAutoField, FKs progress/catalog, option_code Char(64), definition_version Char(64), JSON bases/increments como seis pares canónicos, budget y revision PositiveBigInteger, fechas creación/actualización. Unicidad (progress, option_code); identidades no vacías; presupuesto 0…2⁶³−1, revisión 1…2⁶³−1. |
| DemoTargetPlayableState | BigAutoField, OneToOne progress, FK active_configuration, revisión positiva representable. Solo se crea con la primera configuración válida. |
| DemoTargetPlayableEvent | BigAutoField, FK progress, operation_key Char(32), action Char(16), option_code Char(64), JSON solicitud original y snapshots completos before/after, fecha. Unicidad (progress, operation_key); clave/opción no vacías; acciones configure/switch/redistribute. |

Todas las FKs usan PROTECT **solo como política de esta demo**. Índices implícitos
por FK/unicidad. SQLite no impone todos los max_length de texto. Los checks locales
no prueban coherencia entre tablas ni la estructura de JSON: el servicio valida
sesión, partida, catálogo, referencias, seis atributos, revisiones y cadena causal.
No relaciones con User, duckies.Ducky, inventario o propiedad real. No triggers
nuevos ni garantía de inmutabilidad ante un administrador que altera estos datos.

## Datos sintéticos y composición A4

Doce códigos locales: persist-demo-epoch-1…7 y persist-demo-tech-developer,
-ciber, -sistemas, -data-ia y -gamer. Siete opciones históricas jugables y cinco
tecnológicas. Se desbloquean desde nivel 8; no hay octava época.

Cada definición inicial usa seis bases cero, presupuesto **45 provisional por
opción** y versión `persist-stats-demo-2026-10-22-v1`. No son valores oficiales.
`stats_definitions.py` construye definiciones con A4.2.1; `playable_services.py`
prepara mediante A4.3.1, que usa A4.1. Los códigos ATK, DEF, VEL, INT, LOG y CUACK
se conservan. Gasto completo, parcial y cero permitidos. Sin puntos por nivel.
No se llama a la resolución A4.4.1 ni se simula una fuente oficial.

Lecturas/replay y redistribuciones reconstruyen A4 desde bases, presupuesto y
versiones **persistidos**, sin sustituirlos por una definición futura. El resultado
muestra incrementos, usados/restantes y efectivas explícitamente sintéticas.

## Servicio, revisiones y atomicidad

API local: `issue_playable_operation`, `configure_demo_option`,
`switch_demo_option`, `redistribute_demo_option`, `read_demo_playable`.
La configuración inicial y la adicional comparten configure: crear únicamente si
la opción no existe y activarla. Para la primera expected_revision=None; para las
posteriores se exige la revisión exacta de estado. El estado no existe antes.

Cada mutación efectiva incrementa **una revisión global del estado**; una nueva
configuración empieza en revisión 1 y únicamente su redistribución incrementa su
revisión propia. Redistribuir exige ambas revisiones; también invalida formularios
de estado anteriores, incluso si se redistribuye una opción inactiva. Cambiar de
opción no cambia revisiones ni atributos de configuraciones. Así una redistribución
no deja formularios anteriores aparentemente vigentes.

Cambiar exige comprobar primero la revisión actual, incluso si el destino ya está
activo o la operación figura en historial. Una solicitud obsoleta se rechaza.
Con revisión vigente, destino activo o redistribución con incrementos idénticos
son no-op: sin evento, escrituras ni aumento de revisiones. Redistribuir conserva
bases, presupuesto, versión e identidad originales. No configura implícitamente
opciones ausentes. Redistribución gratuita e ilimitada en esta demo.

Cada servicio comprueba el backend aislado antes de abrir atomic exterior
IMMEDIATE, recarga propiedad y partida, comprueba historial XP y coherencia del
progreso, catálogo exacto/congelado/A1.1 y elegibilidad para operaciones nuevas.
Reutiliza únicamente los comprobadores internos de lectura del Paso 2 dentro de
la misma transacción; no anida sus APIs transaccionales. No confía en caches del
objeto recibido, no select_for_update ni reintentos automáticos. Configuración,
estado y evento se confirman o revierten juntos. No escribe XP ni evoluciones.
Errores de entrada/acceso, revisión (`DemoRevisionError`), conflicto, integridad,
transacción, BD y bloqueo permanecen distinguibles. A4 propaga sus errores.

## Identidad y snapshots

Namespace de firma separado del de XP, ligado a partida, hash de secreto de sesión
y propósito configure/switch/redistribute. El servidor emite claves aleatorias;
no caducan por reloj para permitir replay, pero requieren sesión/contexto y firma
válidos. No son permisos Core. La identidad persistente es (progress, operation_key).

Configure/redistribute buscan primero una operación histórica: solicitud original
canónica idéntica devuelve resultado frozen histórico sin escrituras, aunque haya
operaciones posteriores. Un cambio de contenido o revisión original es conflicto.
Switch mantiene la política de revisión obsoleta anterior, sin replay que la eluda.
No-op no crea identidad persistente ni altera revisiones.

Cada evento conserva la solicitud (acción, opción, incrementos canónicos y ambas
revisiones pertinentes) y snapshots completos de todas las configuraciones/estado
antes y después, incluidos IDs, catálogo lógico/técnico, versiones, bases,
incrementos, presupuesto y revisiones. Efectivas/usados/restantes son derivados
exactos A4 de esas cifras históricas. Se comprueban estructura exacta, tipos,
orden canónico, continuidad, efecto de la acción, conservación de otras opciones
y correspondencia del estado final con las tablas. Historial contradictorio se
rechaza sin reparar. No se presenta esta comprobación como firma criptográfica
de los registros frente a un administrador capaz de reescribir toda la historia.

`PlayableResult`, `PlayableSnapshot` y `ConfigurationSnapshot` son frozen/slots y
contienen propuestas A4 inmutables; replay describe su pasado, no el estado actual.

## HTTP y reproducción PowerShell

Solo GET/POST; CSRF, escape, ASCII numérico estricto, límites de transporte/rango
SQLite, rechazo de extras/duplicados y revisión explícita. La sesión identifica
partida/propietario; ningún ID de navegador sustituye la autorización de sesión.
POST confirmado usa redirect. GET consulta y emite formularios, nunca configura.
Las escrituras de sesión pertenecen a la misma base sintética; no hay login Core.

```powershell
New-Item -ItemType Directory -Force instance | Out-Null
py manage.py migrate --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py seed_persistent_target_demo --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py runserver 127.0.0.1:8002 --settings=apps.ecomotor.target_persistent_demo_settings
```

1. Abrir http://127.0.0.1:8002/demo/objetivo-persistente/ e iniciar partida ficticia.
2. Conceder 700 XP: nivel 8, seis evoluciones, doce opciones.
3. Configurar Gamer y seis incrementos de suma ≤45; confirmar.
4. Configurar Romano con otro reparto; cambiar a Gamer mediante su tarjeta.
5. Redistribuir Gamer; comprobar que Romano mantiene su reparto.
6. Detener y reiniciar el mismo servidor, manteniendo cookies y SECRET_KEY:
   recuperar XP700, seis evoluciones, Gamer activo y ambas configuraciones.
7. Reenviar la última operación de configuración/redistribución sin cambiar su
   contenido: replay sin duplicados. Formularios de cambio antiguos son obsoletos.
8. Iniciar otra partida no borra los registros anteriores. Para limpiar solo los
   datos ficticios seguir el procedimiento de borrado aislado del contrato Paso 2.

## Pruebas y límites

`demo_tests.py` conserva la suite del Paso 2 y añade integridad local, migración,
flujo completo, A4, revisiones/no-op, snapshots/replay/conflicto, rollback, sesiones,
HTTP/CSRF/escape, reapertura, aislamiento y carreras SQLite file-backed con
conexiones independientes (incluido XP concurrente). No se ocultan pruebas
heredadas. Se mantiene el runner de dos fases y se amplía únicamente su etiqueta
predeterminada heredada a `apps`, para incluir los 22 tests Bank/Shop ya integrados
en develop que la lista anterior omitía. No cambia el alcance de etiquetas
explícitas. Resultados reales y comprobación
visual/reinicio se entregan en la PR.

```powershell
py manage.py test apps.ecomotor_target_demo.demo_tests --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py test
py manage.py test --settings=apps.ecomotor.target_persistent_demo_settings
```

No Rewards, producción, escritor objetivo definitivo, integración global, valores
oficiales, migración legacy ni cierre de USE-01B/TRACE-01B. Pendientes Óscar,
Core/A3.5, Henry y consumidores. S3 V1 sigue intacto y no interviene en la demo.
