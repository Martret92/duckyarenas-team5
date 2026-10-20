# A3.3 · Clasificación persistente de perfiles · Contrato conceptual v1

## 1. Autoridad, alcance y estado vigente

**Actualización A3.4 · 20/10/2026, base 8b6b0f7:** reglas puras A3.3 integradas por
PR #66 en [profile_classification_rules.py](../../apps/ecomotor/profile_classification_rules.py),
con ClassificationRequest, PolicySnapshot y ConfirmedClassificationEvent.
Las previsiones siguientes de reglas futuras conservan su corte anterior.
[Dirección persistente A3.4](ecomotor-classification-persistence-v1.md) y
[consulta Core/P5](ecomotor-classification-core-boundary-v1.md) no aprueban modelos
Django definitivos o migraciones. No existe persistencia/servicio de clasificación.

**A3.3-ARQ-01: arquitectura aprobada internamente por el Equipo 5**, comunicada
por Jaime en 02C y documentada el 20/10/2026 sobre develop `75177a2`.
Desarrolla A3-CLAS-01; no es una especificación literal de DAR3 ni una ratificación
de Core/P5, Henry u otros consumidores. DAR3 sigue siendo la autoridad funcional
principal. Se utiliza la trazabilidad existente, sin afirmar una nueva consulta
directa de PDFs. Este contrato v1 versiona el diseño, no una API disponible.

[Decisiones A3.3](../decisions.md#a33--clasificación-persistente-de-perfiles--20102026),
[arquitectura](../architecture.md#14-a33--clasificación-persistente-de-perfiles),
[ERD conceptual](../erd/ecomotor.md#16-a33--política-de-progresión-e-historial-conceptuales),
[pendientes](../pending-decisions.md#18-a33--pendientes-de-clasificación-persistente)
y [transición A3](ecomotor-transition-target-v1.md).

| Componente | Estado verificado / frontera |
| --- | --- |
| A3.1 · PR #58 | [Auditor puro](../../apps/ecomotor/legacy_transition_audit.py) integrado: evalúa snapshots, sin ORM ni autorizaciones de migración. |
| A3.2 · PR #60 | [Extractor](../../apps/ecomotor/legacy_inventory_reader.py) integrado: materializa evidencia limitada de un perfil y alias, no clasifica ni invoca automáticamente A3.1. |
| S3 V1 | [Escritor vigente](../../apps/ecomotor/xp_service.py), con su contrato actual y puntos por nivel. Sigue funcionando incluso sin registro A3.3 mientras no haya corte global autorizado. |
| A2.1 | Planificación pura integrada; no concede XP ni activa el objetivo. |
| A3.3 · PR #66 | Reglas puras y tests integrados; sin modelos, tabla, migración, backfill, servicio transaccional o clasificación real. |

Las anotaciones anteriores que presentan A3.1/A3.2 como futuros conservan su fecha
y valor histórico. No describen la baseline actual. Esta fase no cambia S3,
A3.1/A3.2, atributos objetivo ATK/DEF/VEL/INT/LOG/CUACK ni sus decisiones.

## 2. Política por perfil · A3.3-PHYS-01

`ProfileProgressionPolicy` es un **modelo candidato** asociado de forma unívoca a
`UserProfileEcomotor` mediante OneToOne conceptual. Un perfil puede no tener
registro; un registro pertenece a un único perfil. No es `UserPlayableState` ni
un selector de escritor XP.

| Dato candidato | Significado / límite |
| --- | --- |
| profile | Perfil Ecomotor cuya clasificación se registra. |
| origin | Procedencia explícita, distinta del estado de transición. |
| transition_state | Estado de transición, no una versión de catálogo ni autorización XP. |
| revision | Revisión positiva: primera confirmación 1 y transición nueva +1, para control de concurrencia. |
| created_at / updated_at | Fechas de creación y actualización del registro. |

No condensar procedencia y transición en un campo de versión. La asociación y
campos anteriores no aprueban tipos Django, constraints físicos, on_delete,
tabla o migración. La política física sigue condicionada a Core/P5.

## 3. Procedencia y estados candidatos

**A3.3-ORIGIN-01:** procedencia explícita, sin default que clasifique automáticamente.
Valores candidatos: `LEGACY_V1`, `NATIVE_V1`, `NATIVE_TARGET`. Una procedencia
confirmada se conserva y no cambia silenciosamente durante una transición.
La matriz interna posterior de §3.1–§3.3 precisa las clasificaciones iniciales y
transiciones permitidas; no se eligen representaciones físicas Django.

**A3.3-STATE-01:** `PENDING_REVIEW`, `V1_VERIFIED`, `TARGET_PREPARED`,
`TARGET_CONFIRMED`, `BLOCKED` son el vocabulario de la matriz interna aprobada
tras la PR #63; PR #66 implementa sus tipos y reglas puros, sin registro en BD.
El corte anterior dejaba la matriz pendiente; la precisión siguiente conserva
su resolución interna, sin aprobar permisos externos o mecanismos físicos.
El servicio persistente sigue sin implementar.

**Ausencia de registro = perfil no clasificado**, no `PENDING_REVIEW`.
No inferir clasificación por fecha de creación, nivel, XP, época, especialización,
estadísticas o ausencia de `UserPlayableState`. Los perfiles existentes necesitan
auditoría; no se clasifican al leerlos ni mediante defaults/backfill automático.

### 3.1. Matriz aprobada · A3.3-MATRIX-01

Precisión de A3.3-STATE-01 y A3.3-TX-01 aprobada internamente por Equipo 5 en 02C,
documentada el 20/10/2026 sobre develop `b913bf8`, tras integrar la PR #63.
No es una exigencia literal de DAR3 ni aprobación de Core/P5.
[Registro trazable](../decisions.md#a33--matriz-recuperación-y-revisiones--20102026).

| Origen | Destino | Condición |
| --- | --- | --- |
| Sin registro | PENDING_REVIEW | Primera clasificación legacy autorizada. |
| PENDING_REVIEW | V1_VERIFIED | Verificación V1 autorizada. |
| V1_VERIFIED | TARGET_PREPARED | Preparación objetivo validada. |
| TARGET_PREPARED | TARGET_CONFIRMED | Transición autorizada, evidencia vigente y condiciones del corte cumplidas. |
| Cualquier estado registrado distinto de BLOCKED | BLOCKED | Incidencia justificada y acción autorizada. |
| BLOCKED | Estado inmediatamente anterior al bloqueo | Recuperación explícita con nueva validación, según §3.3. |

Todas las demás transiciones nuevas se rechazan, incluido
TARGET_CONFIRMED → V1_VERIFIED. Tampoco se admite BLOCKED → BLOCKED como operación
nueva; el replay de un bloqueo confirmado conserva su semántica idempotente.
Las altas iniciales nativas se rigen por §3.2, no por una transición entre estados
registrados ni por inferencia de datos existentes.

### 3.2. Procedencia y primera clasificación

| Procedencia explícita | Estado inicial | Condición |
| --- | --- | --- |
| LEGACY_V1 | PENDING_REVIEW | Primera clasificación legacy autorizada. |
| NATIVE_V1 | V1_VERIFIED | Únicamente con alta confiable y verificación correspondiente. |
| NATIVE_TARGET | TARGET_CONFIRMED | Únicamente después de activación global autorizada y alta objetivo válida. |

No inferir origen/estado por fecha, XP, nivel, estadísticas ni ausencia de otros
registros. Se mantienen las demás exclusiones de A3.3-STATE-01. La procedencia
confirmada es inmutable. Estas entradas no autorizan altas, backfill o clasificación
reales ni activan el escritor objetivo.

### 3.3. Bloqueo y recuperación · A3.3-RECOVERY-01

El evento de bloqueo debe permitir identificar inequívocamente el estado
inmediatamente anterior al bloqueo. La única recuperación permitida desde BLOCKED
vuelve a ese estado, mediante acción explícita y nueva validación; no es una
selección libre de destino ni una reparación automática.
La recuperación conserva el evento de bloqueo sin borrarlo o alterarlo.
No se elige aquí un campo/FK nuevo para representar esa evidencia.

TARGET_CONFIRMED no habilita XP por sí mismo. BLOCKED no sustituye los controles
globales de activación o suspensión del escritor XP. A3.1 COMPATIBLE y la fotografía
de A3.2 no bastan para clasificar o migrar: actualidad de evidencia y protocolo de
validación transaccional siguen pendientes (§6).

### 3.4. Revisión e historial · A3.3-REV-01

- Primera clasificación: revision = 1; registrar ausencia de estado anterior,
  sin inventar un estado histórico ni una revisión previa persistida.
- Cada transición nueva confirmada incrementa revision en 1 y requiere evento propio.
- Replay compatible: ninguna mutación, evento adicional o nueva revisión.
- Identidad conceptual UNIQUE(profile, operation_key), exclusiva de clasificación.

El protocolo conceptual de contenido, revisión esperada y replay queda precisado
por A3.3-CONTENT-01, A3.3-REV-PROTOCOL-01 y A3.3-REPLAY-PROTOCOL-01 en §4.1 y §7.
Se conserva la matriz anterior, idempotencia, conflicto de clave y D-19.
La representación física de ausencia previa, revisiones y evidencia de recuperación
continúa pendiente; no se crea esquema en esta PR.

## 4. Historial e identidad · A3.3-EVENT-01

`ProfileProgressionPolicyEvent` es un **modelo candidato** de historial inmutable,
separado de XPEvent, EvolutionEvent y StatAllocationEvent. Datos conceptuales:
perfil afectado, `operation_key`, acción de clasificación, estado/revisión
anteriores y posteriores, fecha de confirmación y referencia al operador autorizado.
La identidad técnica del operador se acuerda con Core; no se elige una FK o
política de borrado. La representación de una primera clasificación sin estado
previo debe concretarse, sin inventar un estado histórico.

Un perfil puede tener varios eventos; cada evento identifica un único perfil.
Unicidad **conceptual** `(profile, operation_key)` dentro del dominio clasificación:

- Misma clave y misma operación confirmada: repetición idempotente, sin nuevos efectos.
- Misma clave y contenido incompatible: conflicto explícito, sin mutación.

No reutilizar estos eventos como historial de XP o asignación de puntos ni
fabricar procedencia de eventos V1. El contenido comparable y el orden conceptual
se precisan a continuación; su representación física sigue pendiente.
No se publica una firma definitiva ni un formato HTTP.

### 4.1. Contenido original comparable · A3.3-CONTENT-01

Precisión aprobada internamente por Equipo 5 en 02C tras la PR #64, documentada
el 20/10/2026 sobre develop `e362cbf`. No es requisito literal nuevo de DAR3 ni
aprobación de Core/P5. [Registro de las tres decisiones](../decisions.md#a33--contenido-revisión-y-replay--20102026).

Identidad conceptual: `(profile_id, operation_key)`, independiente de eventos XP.
Conservar un contenido semántico original comparable que contemple:

- Perfil y operation_key exactos, sin normalizar silenciosamente las claves.
- Acción solicitada y procedencia pertinente a la operación.
- Destino solicitado o determinado por la acción.
- expected_revision original.
- Motivo o referencia de incidencia, cuando corresponda.
- Para recuperación, información que la vincule inequívocamente al bloqueo original.

El contenido solicitado no es el resultado confirmado ni el estado actual del
perfil. La comparación es estricta: valores de tipos distintos no son iguales;
None no equivale a 0. Misma identidad y mismo contenido original confirmado es
replay compatible; contenido diferente es conflicto sin mutación.
Si falta evidencia histórica suficiente para justificar igualdad, rechazar sin
inferirla. La representación persistente de solicitudes, eventos y relaciones,
y el mecanismo físico de conservación/comparación siguen pendientes de diseño.
La identidad técnica del operador y el tratamiento canónico de su participación
en la comparación requieren acuerdo Core/P5, sin política definitiva aquí.

## 5. Clasificación y autorización de XP · A3.3-AUTH-01

La autorización de XP no es un interruptor persistido por perfil. Separar:

1. Clasificación persistente coherente.
2. Activación global autorizada del escritor.
3. Emisor interno autorizado por el servidor.
4. Precondiciones e idempotencia de la operación XP.

`TARGET_CONFIRMED` no activa el escritor objetivo. S3 V1 conserva su contrato
y sigue siendo el único escritor vigente, también para perfiles sin registro
A3.3 mientras no se autorice el corte global. No imponerle una nueva precondición
de clasificación por esta documentación ni habilitar escritores contradictorios.
El replay XP conserva el orden histórico definido en A3/A2 y no se sustituye
por el protocolo de eventos de clasificación.

## 6. Evidencia legacy · A3.3-LEGACY-01

A3.2 obtiene una fotografía de BD; A3.1 evalúa un subconjunto limitado de ella.
`COMPATIBLE` no clasifica persistentemente, migra, repara ni autoriza XP.
No certifica integralmente estadísticas gastadas, especializaciones o Duckies.

Mientras S3 escriba, la fotografía puede quedar obsoleta. Una operación futura
de clasificación debe validar evidencia y precondiciones suficientemente actuales
bajo la misma transacción que confirma política/evento, según
[A3.6-FRESH-01](ecomotor-classification-evidence-v1.md#2-evidencia-vigente--a36-fresh-01).
Se aprueba la dirección de lector interno específico; API/consultas y cobertura
verificable siguen pendientes: no se presume que pueda invocarse el extractor A3.2
dentro de otra transacción, pues el extractor actual rechaza transacciones exteriores.
No cambiarlo ni eliminar su protección por este diseño. No realizar backfill ni
inventar identidad o procedencia de eventos antiguos.

## 7. Operación futura, atomicidad y errores · A3.3-TX-01

Entradas conceptuales necesarias: perfil, acción, procedencia/estado pertinentes,
clave de operación, revisión esperada, evidencia requerida y contexto autorizado
con alias confiable. No constituyen firma Python o servicio disponible.

Primera creación y transiciones conservan íntegramente §3.1–§3.4. El protocolo
conceptual siguiente diferencia solicitudes nuevas y operaciones ya confirmadas;
no exige elegibilidad o revisión actuales a un replay histórico compatible.

### 7.1. Revisión esperada · A3.3-REV-PROTOCOL-01

| Operación | Comprobación y efecto conceptual |
| --- | --- |
| Primera clasificación | expected_revision=None y ausencia real de política. Al confirmar, revision=1 y ausencia de estado anterior en historial, sin fabricar revisión previa persistida. 0 no sustituye a None. |
| Transición nueva | Revisión esperada exacta, coincidente con la persistida actual. Confirmación suma exactamente 1 y registra evento nuevo; revisión obsoleta rechaza sin efectos. |
| Replay compatible | No comparar expected_revision original con la revisión actual para rechazar la operación ya confirmada. Sin mutación del estado actual, eventos adicionales o incremento de revisión. |

### 7.2. Orden de procesamiento · A3.3-REPLAY-PROTOCOL-01

1. Validar datos estructurales, identidad del perfil, clave y autorización confiable
   del solicitante. La autorización inicial también es obligatoria para replay.
2. Iniciar frontera transaccional D-19 bajo el mismo alias de BD.
3. Buscar primero evento de clasificación por (profile_id, operation_key).
4. Si existe, comprobar integridad histórica y contenido original conforme a §4.1.
   Si coincide, devolver el resultado histórico sin efectos. Si difiere o no puede
   justificarse la comparación, rechazar sin mutación.
5. Solo sin evento para esa clave, comprobar ausencia de política o revisión actual,
   según corresponda; procedencia, matriz, estado, autorizaciones y evidencia necesaria.
   Una operación nueva no se confirma con evidencia insuficiente u obsoleta.
6. Confirmar conjuntamente política y nuevo evento o revertir toda la operación.

No revalidar elegibilidad actual de una transición histórica como si fuera nueva.
No presentar resultado histórico como estado actual del perfil. Replay no permite
consultar perfiles ajenos ni sustituye autorización, integridad histórica o D-19.
El protocolo de evidencia vigente y su frontera técnica siguen pendientes (§6);
no se presupone extracción A3.2 anidada ni se habilitan servicios reales.

### 7.3. Ejemplos conceptuales

| Caso | Solicitud y resultado esperado |
| --- | --- |
| A · Primera clasificación | LEGACY_V1 sin registro, expected_revision=None: confirma PENDING_REVIEW, revisión 1 y evento propio. Solicitud exactamente repetida recupera ese resultado histórico incluso si la política actual ya está en revisión 3; no la retrocede. |
| B · Conflicto de clave | Misma clave cambiando procedencia, acción, destino o revisión esperada: conflicto, sin escritura. |
| C · Revisión obsoleta | Transición nueva con expected_revision=1 y política en revisión 2: rechazo sin evento nuevo. |
| D · Recuperación | Bloquear TARGET_PREPARED confirma BLOCKED y conserva su estado anterior. Recuperación con nueva validación vuelve exclusivamente a TARGET_PREPARED y registra otra transición. Repetir después el bloqueo original es replay histórico: no vuelve a bloquear el perfil. |

Los ejemplos no eligen esquema físico, identidad del operador o autorizaciones
externas. Las referencias históricas insuficientes o incoherentes no se reparan.

Aplicar D-19: mismo alias y frontera atómica, lecturas de estado mutable dentro
de transacción, SQLite `BEGIN IMMEDIATE`, timeout de 5 segundos, protección frente
a duplicados, revisión esperada y rollback íntegro ante fallos. No asumir bloqueo
efectivo mediante `select_for_update()` en SQLite ni atomicidad entre conexiones
independientes. Sin I/O externo dentro de la transacción.

Errores conceptuales diferenciados: entrada/perfil o alias inválidos, perfil
inexistente, autorización insuficiente, procedencia/estado/transición inválidos,
intento de cambiar procedencia confirmada, conflicto de clave, revisión obsoleta,
evidencia insuficiente/obsoleta, incoherencia histórica y fallo de BD/timeout.
Sin nombres definitivos de excepciones o códigos HTTP. Los fallos no generan
clasificaciones, eventos confirmados parciales o reparaciones silenciosas.

## 8. Dependencias y límites · A3.3-CORE-01

Core/P5 debe acordar conservación histórica, eliminación/anonimización, relaciones
físicas/on_delete, identidad canónica del operador y autorización confiable del
proceso. No se seleccionan políticas físicas por analogía con tablas existentes.
Henry/Duckies y consumidores deben coordinar catálogo, referencias y transición.
Estas dependencias no están resueltas ni se contacta automáticamente con ellos.

Siguen pendientes catálogo objetivo físico, causalidad de nuevas evoluciones,
procedencia de concesiones nuevas, transformación de datos reales, ensayos y
activación global. No se desbloquean Rewards F2-A, dominio persistente, S13-A2,
economía o inventario; no se altera V1 ni se activan A2 o nuevas opciones jugables.

## 9. Secuencia y pruebas futuras · A3.3-IMP-01

| Orden | Incremento / condición |
| --- | --- |
| 1 | PR documental A3.3: único paso ejecutado aquí. |
| 2 | Reglas puras y validadores en 01B de la matriz, altas, recuperación y revisiones aprobadas en §3.1–§3.4. |
| 3 | Contratos necesarios con Core/P5. |
| 4 | Modelos y migraciones de clasificación solo tras acuerdos necesarios, inicialmente sin backfill automático. |
| 5 | Servicios transaccionales de clasificación y tests. |
| 6 | Catálogo objetivo, causalidad histórica y coordinación con Duckies. |
| 7 | Migración autorizada, ensayos y activación global posterior. |

Tests a incluir en la implementación: ausencia de registro frente a revisión;
procedencias/transiciones válidas e inválidas; procedencia/eventos inmutables;
repetición y conflicto de operation_key; revisión obsoleta y concurrencia;
rollback sin cambios/eventos parciales; evidencia obsoleta o insuficiente;
clasificación sin autorización XP; regresión completa de S3 V1; aislamiento de
perfiles, alias y autorizaciones. No se crean ni ejecutan tests Django en esta PR.

Precisión de tests para 01B tras aprobar la matriz: validadores puros de
transiciones permitidas/prohibidas, primeras clasificaciones según procedencia,
recuperación válida/inválida, procedencia inmutable, revisiones, replay compatible
y conflicto de clave. Los tests transaccionales de concurrencia, rollback e
idempotencia persistente corresponden al futuro servicio Django, después de
resolver las dependencias Core/P5; no se implementan ni ejecutan aquí.

Tests adicionales previstos para 01B del protocolo aprobado: igualdad estricta de
contenido original y conflictos de clave; primera clasificación con None y rechazo
de 0 como equivalente; revisión correcta/obsoleta; replay con revisión actual
posterior; replay de bloqueo tras recuperación; historia insuficiente/incoherente;
preservación de estado y revisión actuales durante replay. Las pruebas
transaccionales de concurrencia, rollback e idempotencia persistente siguen
reservadas al futuro servicio Django, sujeto a dependencias Core/P5.

## 10. A3.4 · Persistencia candidata y acuerdos externos

[A3.4-ARQ-01](../decisions.md#a34--dirección-de-persistencia-de-clasificación--20102026)
aprueba internamente una dirección mínima, no esquema Django definitivo:
política/evento en apps.ecomotor, campos candidatos para reconstruir exactamente
la API pura, identidad por operación y confirmación conjunta D-19.
[Contrato de persistencia](ecomotor-classification-persistence-v1.md) centraliza
campos y alternativas, replay, propuesta UNIQUE(profile, after_revision), límites
físicos, lector interno transaccional y pruebas futuras. No se modifica matriz,
contenido, revisión o replay aprobados por describir su futura persistencia.

[Propuesta Core/P5](ecomotor-classification-core-boundary-v1.md) no ratificada:
identidad/operador, autorización, ciclo de vida, retención y privacidad. No elegir
on_delete, FK al bloqueo o participación canónica del operador en comparación.
Cobertura suficiente por transición sigue pendiente; no anidar A3.2 ni ampliar
COMPATIBLE a certificación de toda V1. No modelos/migraciones, clasificación real,
backfill o activación. Las reglas puras ya integradas no sustituyen esas garantías.

## 11. A3.6 · Evidencia vigente y condiciones

[Contrato de evidencia](ecomotor-classification-evidence-v1.md) centraliza la
precisión interna A3.6-FRESH-01/COVERAGE-01/GATE-01. Se conservan matriz, altas,
recuperación, identidad, contenido, revisiones y orden de replay A3.3.
Operaciones nuevas requieren datos necesarios comprobados dentro de su transacción
y evidencia suficiente por transición; las condiciones aprobadas no fijan consultas
exhaustivas. Bloqueo autorizado no exige verificaciones de avance; recuperación
exige bloqueo íntegro y validación nueva de su destino.

Sin evidencia suficiente/vigente, autorización, condiciones externas obligatorias
o coherencia de política/historial/revisión, no confirmar operación nueva.
Replay histórico conserva autorización, contenido e integridad sin exigir nueva
elegibilidad o mutar el estado actual. COMPATIBLE no clasifica ni certifica niveles,
puntos, especializaciones/rangos o Duckies integralmente.
A3.2 no se anida; A3.5 sigue abierto y sus cinco preguntas Core/P5 no están
ratificadas. Sin modelos/servicios, migración, clasificación automática o activación.
