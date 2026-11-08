# A4-TARGET-PERSIST-DEMO-01 · Opciones y estadísticas persistentes de demo

> **Corte técnico posterior · Fase B · 08/11/2026.** Esta PR implementa
> [DIAG-ATR-OBJ-02-SNAP-01 · Fase B](../decisions.md#diag-atr-obj-02-snap-01--fase-b--compatibilidad-cuack-y-esp--08112026),
> autorizada internamente por 02C-3. A4 usa `ATK, DEF, VEL, INT, LOG, ESP`;
> `CUACK` y `SPE` no son alias aceptados por A4. Los antecedentes ATR-OBJ-01,
> ATR-OBJ-02 y Fase A conservan su fecha y describen sus respectivos cortes.
> El código propuesto en esta PR sustituye el estado técnico anterior que
> todavía indicaba CUACK en los validadores; no atribuye aprobación a Óscar/Core.
> La demo nueva usa `persist-stats-demo-esp-v2`, bases cero y presupuesto
> sintético 45 por opción. El archivo `persist-stats-demo-2026-10-22-v1`
> conserva CUACK sin conversión y queda cerrado a toda operación jugable.
> A4.4.1 sigue sin fuente confiable; 45+5 y A4-45+5-MATH-01 no se implementan.

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
py manage.py test apps.ecomotor.ecomotor_target_demo.demo_tests --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py test
py manage.py test --settings=apps.ecomotor.target_persistent_demo_settings
```

No Rewards, producción, escritor objetivo definitivo, integración global, valores
oficiales, migración legacy ni cierre de USE-01B/TRACE-01B. Pendientes Óscar,
Core/A3.5, Henry y consumidores. S3 V1 sigue intacto y no interviene en la demo.

## Consolidación física del laboratorio

CONSOLIDACIÓN-A-01 conserva los contratos y datos de este paso. El paquete actual
es `apps.ecomotor.ecomotor_target_demo`; settings, SQLite y URL no cambian.
Las migraciones 0001–0003, tablas, ContentTypes, sesiones y tokens mantienen su
identidad. No ejecutar fake, recrear tablas ni borrar bases para efectuar el traslado.
[Decisión y alcance](../decisions.md#consolidación-a-01--reorganización-física-del-laboratorio).
## Precisión DIAG-ATR-OBJ-02-SNAP-01 · Lector histórico separado, Fase A · 08/11/2026

**Decisión interna posterior:** [DIAG-ATR-OBJ-02-SNAP-01](../decisions.md#diag-atr-obj-02-snap-01--compatibilidad-sintética-histórica-cuack--fase-a--08112026)
autoriza un lector puro de archivo histórico CUACK para datos exclusivamente
sintéticos; **no convierte este contrato original en un sistema ESP implementado**.
Las referencias anteriores a CUACK describen el formato almacenado de la demo
vigente, no el atributo canónico del Ecomotor objetivo, que por
[ATR-OBJ-02](../decisions.md#atr-obj-02--esp-como-sexto-atributo-objetivo--07112026)
es ESP.

| Formato | Versión interna exacta | Claves históricas o futuras |
| --- | --- | --- |
| Legacy, solo lectura futura | `persist-stats-demo-2026-10-22-v1` | `ATK, DEF, VEL, INT, LOG, CUACK` |
| ESP objetivo para demo futura | `persist-stats-demo-esp-v2` | `ATK, DEF, VEL, INT, LOG, ESP` |

**Contrato del nuevo lector Fase A:** `validate_legacy_playable_archive(*,
progress_id, catalog_pk, catalog_id, catalog_version, events, current_state)`
acepta estructuras JSON explícitas; cada evento contiene `event_id`,
`progress_id`, `operation_key`, `action`, `option_code`, `original_request`,
`before` y `after`. `current_state` conserva el esquema del snapshot final
`progress_id`, `catalog_id` (PK), `revision`, `active_option` y
`configurations`. El módulo replica solo las garantías históricas de validación:
seis claves estrictas, versión y catálogo coherentes, presupuesto 45, bases cero,
enteros exactos, cálculos, cadena ordenada, unicidad y relaciones entre transiciones
y estado actual. Exige **al menos un evento** para reconocer un archivo CUACK;
una partida sin configuraciones no se identifica por inferencia como legada.
Devuelve dataclasses inmutables específicas, nunca objetos A4 autorizados.

El lector no se invoca desde la app en esta fase; no importa A4 ni Django,
no hace IO, consultas, escrituras, conversiones, fallback ni reparación.
La Fase B futura decidirá selección de lector y bloqueo efectivo de todos los
POST jugables legados, incluidos replay y no-op. **En el HEAD actual esos
bloqueos aún no están integrados.** La interfaz de XP/Rewards sintéticos y
el aislamiento físico de SQLite no cambian. Sin efecto sobre los contratos
productivos, User/Core, V1 ni migraciones.


## Fase B · Contrato de lectura y cierre jugable · 08/11/2026

La selección de lector ya no se decide por excepción: bajo `_scope()` se cargan
todas las filas y versiones, estableciendo previamente propiedad y catálogo.
EMPTY solo admite ausencia total de eventos, configuraciones y estado. Cualquier
combinación parcial es inválida. V1 homogénea se envía al lector de archivo con
los JSON originales; V2 homogénea exige `persist-stats-demo-esp-v2` exacto y A4
ESP. Ambos caminos contrastan toda la cadena y el estado actual. No hay fallback.

`read_demo_playable` mantiene `(state, history)`: para CUACK devuelve las
representaciones inmutables de Fase A; para ESP conserva las representaciones
vigentes con preparación A4. `is_legacy(state)` permite a la vista distinguirlas
sin convertir el archivo en configuración autorizada. La consulta admite
`operation_token` y `action` opcionales para verificar la pertenencia del token
dentro de `_scope()` antes de interpretar un formulario POST; no emite tokens
ni autoriza una mutación por esa validación. El módulo histórico no se modifica. Una partida vacía puede iniciar ESP aunque su fecha sea anterior.

La consulta GET legada devuelve 200, estadísticas CUACK e historia originales,
sin emitir tokens ni formularios jugables. No borra ni adapta `playable_last`.
El cierre se aplica también en el servicio: emisión de token y cualquier
configure/switch/redistribute, replay o no-op se rechazan. Un token ajeno o
alterado se rechaza antes del conflicto de solo lectura; no se revela una
partida ajena. La vista reconoce el formulario histórico cerrado para rechazar
su operación, nunca para escribir o convertir su reparto. Campos adicionales,
duplicados, ausentes o números inválidos: 400. CSRF/acceso/token: 403. Archivo
CUACK válido bloqueado: 409 específico. Historia incoherente: 409 de integridad.

XP/Rewards y las consultas Bank/inventario permanecen independientes del cierre
jugable. GET puede mantener sesiones Django y emitir sus tokens propios; eso no
representa DML sobre configuraciones, estado o eventos jugables. Las lecturas
no prometen una única instantánea global de la página.

En ESP se conservan PRG, seis campos canónicos, revisiones, idempotencia y
prioridad de revisión de switch; no-op y replay compatibles no crean eventos.
La nueva definición mantiene presupuesto provisional 45 y bases cero. Sin
45+5, fuente A4.4.1, migraciones, datos oficiales ni integración productiva.


### Evidencia de regresión de Fase B · 08/11/2026

En configuración externa aislada y con auditoría de aperturas SQLite: 26 casos
focalizados (14 nuevos y los 12 de Fase A) aprobados en 57,442 s; regresión A4 y
demos: 191 ejecutados, 189 aprobados y 2 omitidos, en 29,286 s. El DemoRunner
original completo ejecutó su fase habitual (1.414 tests, 1.412 aprobados y 2
omitidos, 214,022 s) y su fase persistente (170 padres aprobados, sin fallos,
errores ni omisiones, 820,851 s). Sus 41 subprocesos completaron 116 casos hijos
satisfactorios, contados por separado. Los focalizados son subconjuntos de las
suites y no se suman nuevamente al total. Descubrimiento: 170 padres únicos.

Django check sin incidencias; autodetector normal sin cambios y grafo de modelos
persistentes coincidente con migraciones, sin abrir una base personal. Lector y
12 tests de Fase A intactos; conservación de JSON/timestamps y ausencia de DML
jugable comprobadas en lectura y rechazos HTTP. Siete archivos personales con
existencia y SHA-256 idénticos; fixtures temporales cerrados y retirados.
La primera prueba ampliada detectó un 400 en lugar de 403 para un token de otra
partida con campos antiguos: se corrigió la prioridad de autorización y pasó la
repetición focalizada y el runner completo. No se relajaron tests históricos.
Estos resultados no validan datos oficiales ni una integración productiva.
