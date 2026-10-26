# A3 · Compatibilidad histórica y activación del Ecomotor · Contrato objetivo v1

## 1. Autoridad, alcance y estado

**Estado vigente A3.3 · 20/10/2026, base 75177a2:** A3.1 (#58) y A3.2 (#60)
ya están integrados como auditor puro y extractor de evidencia, respectivamente.
Sus propuestas futuras de §10/§12 conservan el corte histórico documentado.
[Clasificación A3.3](ecomotor-profile-classification-v1.md) desarrolla A3-CLAS-01
solo conceptualmente; no hay registro físico, clasificación, migración o activación.
S3 V1 sigue siendo el único escritor XP, incluso para perfiles sin registro A3.3.

A3-ARQ-01 aprobado **internamente y de forma condicionada por el Equipo 5**,
comunicado por Jaime. Registro documental del 20/10/2026 sobre develop
`7039ae64cd8975f14a93c4d4bbbc92893adc5ffd`. No ratifica contratos físicos con Óscar/Core, Henry u otros consumidores ni
autoriza esquema, migración o activación.
DAR3 conserva su autoridad funcional principal. La aclaración de Óscar del 19/10
sobre épocas se distingue de las decisiones técnicas internas de versionado,
mecanismos Django y despliegue. Se utiliza trazabilidad existente, sin nueva
consulta directa de PDFs ni cantidades oficiales inventadas.

[Decisiones A3](../decisions.md#a3--compatibilidad-histórica-y-activación-coordinada--20102026),
[arquitectura](../architecture.md#11-a3--compatibilidad-histórica-y-activación-coordinada),
[bloqueos](../pending-decisions.md#15-a3--condiciones-de-compatibilidad-y-activación)
y [ERD condicionado](../erd/ecomotor.md#15-a3--frontera-física-de-la-transición).
Desarrolla A3-CT-01 sin cambiar A1-CT-01 (progresión/validación) ni A2-CT-01
(XP sin puntos). Se conservan [02C](ecomotor-playable-options-target-v1.md),
[A2](ecomotor-target-xp-v1.md) y [S3 V1](ecomotor-xp-v1.md).

A1.1/A1.2 y [A2.1](../../apps/ecomotor/target_xp_plan.py) ya están integrados
(PR #52/#53/#56): validación, cálculo y planificación puros, sin concesiones.
S3 V1 sigue como escritor vigente. **Registro persistente A3, migración de perfiles
y punto de entrada futuro no están implementados.** El catálogo preparatorio de
fase 1 está integrado mediante #88, según el estado posterior de §3;
no autoriza uso real ni añade un escritor objetivo.

## 2. Clasificación persistente · A3-CLAS-01

**Desarrollo A3.3:** [contrato de clasificación](ecomotor-profile-classification-v1.md)
y [decisiones](../decisions.md#a33--clasificación-persistente-de-perfiles--20102026).
ProfileProgressionPolicy y ProfileProgressionPolicyEvent son modelos candidatos:
procedencia explícita inmutable, transición separada y revisión monotónica; historial
inmutable con identidad (profile, operation_key) propia del dominio clasificación.
Política y evento se confirman juntos bajo D-19; repetición compatible sin efectos,
contenido incompatible en conflicto. Sin registro = no clasificado, no revisión.
Nombres/matriz de procedencias/estados son candidatos; clasificación no es un
interruptor XP ni TARGET_CONFIRMED activa escritor. No se aprueba tabla, backfill,
on_delete o migración. Core/P5 y Henry/consumidores conservan sus dependencias.

Proponer un registro persistente de política de progresión asociado unívocamente
a UserProfileEcomotor. Separar **procedencia del perfil** de **estado de transición**;
no condensarlos en un diagnóstico o un texto de versión. Campos Django, tipos,
valores de estado y restricciones definitivos siguen pendientes.

No inferir clasificación por XP/nivel, época, estadísticas o ausencia de
UserPlayableState. Perfiles existentes requieren auditoría antes de considerarlos
clasificados o migrados. La clasificación por sí sola **no autoriza XP**: deben
cumplirse autorización del servidor, política de activación, escritor y demás
precondiciones de una concesión nueva. No se crea aquí un registro ni backfill.

## 3. Catálogos e integridad histórica · A3-CAT-01

Conservar EvolutionStage y EvolutionEvent V1, sus identidades, referencias
existentes y comportamientos actuales. Dirección aprobada:
**catálogo objetivo separado, versionado e inmutable una vez utilizado**.
El corte A3-CAT-01 no aprobaba esquema físico. A3-CAT-PHYS-01 concreta más abajo
los tres modelos candidatos mínimos; implementación y protección de inmutabilidad
siguen pendientes, sin modelos ni migraciones generados por esta documentación.
TargetCatalogSnapshot A1.1 es un valor puro validado, no ese catálogo persistente
ni permiso de publicación/producción.

Se distinguen nueve épocas DAR3 originales, siete etapas V1 terminadas en Actual
y siete épocas históricas objetivo: Prehistórico, Griego, Romano, Medieval,
Renacentista, Revolución Industrial y Siglo XX. Nivel 8 abre elección, no época
adicional; niveles posteriores continúan. No renombrar filas V1 para reinterpretar
EvolutionEvent ni cambiar sus atributos históricos por inferencia.

### A3-CAT-EVENT-01 · Separación de eventos objetivo

Decisión técnica interna aprobada por Equipo 5 en 02C, registrada el 21/10/2026;
no requisito literal de DAR3 ni confirmación de Óscar, Core o Henry.
Los eventos de evolución objetivo serán **separados de la tabla EvolutionEvent V1**,
en correspondencia con el catálogo objetivo separado, versionado e inmutable tras
uso. Cada evolución objetivo conservará causa XP verificable, correspondencia de
perfil e identidad histórica de época y versiones. No reconstruir esa identidad
con un catálogo vigente distinto del utilizado.

Una concesión que cruce varias épocas registrará un evento objetivo por cada época
cruzada, sin omisiones ni duplicados. Replay de una concesión existente no concede
XP ni crea evoluciones adicionales. Nivel 8 desbloquea elección, no octava época.
Se conserva la identidad (profile, operation_key) de
[A2-IDEM-01](ecomotor-target-xp-v1.md#4-identidad-y-replay-entre-versiones--a2-idem-01)
y las garantías [A2-EVO-01](ecomotor-target-xp-v1.md#5-progresión-y-eventos-causales--a2-evo-01),
sin reinterpretar, renombrar o migrar silenciosamente etapas/eventos V1.

**Diseño físico pendiente de eventos:** nombre/campos/claves/
restricciones de eventos objetivo, relaciones con perfiles, épocas/versiones y
XPEvent, y consulta histórica conjunta. La separación conceptual no selecciona
FKs, on_delete, índices o migraciones ni copia restricciones físicas V1.
EvolutionEvent.stage sigue refiriendo a EvolutionStage V1. PlayableOption histórico
fue diseñado en 02C con relación conceptual EvolutionStage; su adaptación y la
integración con EvolutionItem/vestimentas requieren acuerdo con Henry.
Conservación/supresión y relaciones siguen con Core/A3.5. Publicación oficial,
umbrales XP autorizados, migración y activación coordinada permanecen pendientes.
No existe aún servicio objetivo persistente por aprobar esta separación.

### A3-CAT-PHYS-01 · Catálogo objetivo mínimo candidato

Diseño mínimo aprobado internamente por Equipo 5 en 02C, registrado el 21/10/2026
sobre develop `18b6bbd4174cc7325f4511906cb26827d2aafeff`. No requisito técnico literal
DAR3 ni aprobación de Óscar/Core/Henry. El corte documental #85 describía **tres
modelos candidatos no implementados**; el estado posterior de fase 1 se precisa
a continuación, sin convertir ese antecedente en autorización de uso real.

| Modelo candidato | Campos conceptuales mínimos | Restricciones locales previstas |
| --- | --- | --- |
| TargetCatalogVersion | catalog_id, version | Unicidad (catalog_id, version). La identidad lógica del catálogo es distinta de la PK técnica que Django pueda necesitar; no se elige aquí su tipo. |
| TargetLevelThreshold | Referencia a TargetCatalogVersion (catalog), level, minimum_xp | Unicidad (catalog, level); level entero positivo y minimum_xp no negativa. **Sin stat_points_awarded persistente.** |
| TargetEpoch | Referencia a TargetCatalogVersion (catalog), code, name, ordinal, minimum_xp | Unicidad (catalog, ordinal) y (catalog, code); ordinal entre 1 y 7; code y name no vacíos; minimum_xp no negativa. |

Son restricciones por fila o de unicidad local expresables en BD. Los tipos,
longitudes y on_delete internos de fase 1 se concretan abajo. Códigos definitivos,
nombres oficiales y umbrales XP autorizados no se crean con ejemplos. La mera
existencia de una fila, versión textual o booleano no acredita publicación oficial,
confianza ni autorización.

La futura adaptación ORM → [A1.1](../../apps/ecomotor/target_catalog_validation.py)
construirá explícitamente LevelDefinition(level, minimum_xp, stat_points_awarded=0)
y StageDefinition(code, ordinal, minimum_xp). Aportará orden de códigos explícito
y catalog_version de la versión seleccionada, sin elegir aquí una codificación
de identidad/versiones ni una fuente autorizadora. El cero es un valor de adaptación
a la estructura pura existente, **no un campo TargetLevelThreshold** ni un cambio
de S1/V1. No se modifica el validador A1.1, que admite puntos heredados no nulos.

El servicio futuro validará el catálogo completo mediante A1.1, además de las
restricciones locales: exactamente siete épocas con ordinales consecutivos 1–7;
niveles consecutivos desde 1, al menos ocho y posibilidad de posteriores;
XP inicial cero en nivel/época iniciales; umbrales estrictamente crecientes en
ambas colecciones; códigos únicos en el orden explícito; igualdad de umbrales
nivel/época en posiciones 1–7. Nivel 8 tiene umbral propio, desbloquea elección
y no constituye octava época. Estas invariantes entre filas no se acreditan con
validar una fila o sus restricciones locales. name es metadato del modelo candidato,
no un atributo nuevo en StageDefinition ni validado por A1.1. A1.1 prueba coherencia
técnica, nunca publicación oficial o autorización.

#### A3-CAT-IMMUT-01 · Protección progresiva del catálogo objetivo

Decisión interna aprobada por Equipo 5 en **02C-2 el 21/10/2026**, registrada sobre
develop `9b03d3bf485b6d2ca7940b822e6e6544005aca11`. No requisito técnico literal DAR3
ni ratificación externa de Óscar/Core/Henry. **Sustituye únicamente la condición
temporal de A3-CAT-PHYS-01** que exigía protección completa antes de implementar
físicamente los modelos; no elimina la obligación de preservar versiones históricas.
Campos, unicidades, adaptación/validación A1.1 y separación V1 anteriores se conservan.

**Fase 1 · Persistencia preparatoria permitida:** futura implementación de
TargetCatalogVersion, TargetLevelThreshold y TargetEpoch, restricciones locales de
BD, validación de catálogo completo reutilizando A1.1, migración estructural vacía
de datos y tests. Los catálogos son preparatorios, **sin autorización de uso real**.
Esta fase no implementa protección de inmutabilidad contra escrituras directas
ni permite afirmar que las versiones estén congeladas. El corte documental #86
no creaba tablas, migraciones, validadores o tests.

Durante fase 1 no se habilitan escritor XP objetivo, referencias reales de
progresión a estas versiones, eventos de evolución objetivo basados en ellas,
publicación o activación del catálogo. No introducir campos frozen, published o
equivalentes. A1.1 valida estructura; no acredita valores aprobados por Óscar,
publicación o autorización funcional. S3 V1 sigue único escritor XP activo.

**Fase 2 · Protección obligatoria antes del primer uso real de cualquier versión:**
aprobar e implementar congelación transaccional, protección física de versión,
niveles y épocas frente a modificaciones y eliminaciones, incluidas escrituras
directas y operaciones concurrentes, y mecanismo verificable para acreditar la
condición de versión utilizada. Una versión completa utilizada permanece inmutable
junto con sus niveles/épocas; sus cambios requieren crear una nueva versión.

En el corte IMMUT-01 la garantía y sus mecanismos no estaban implementados. En el corte
documental #86 no estaban aprobados los triggers SQLite ni su política. La
decisión posterior A3-CAT-FREEZE-01, descrita abajo, aprueba su uso y la preferencia
de instalación irreversible; SQL, nombres y detalles concretos siguen pendientes.
No se simulan garantías mediante booleanos o versiones textuales. Publicación,
permisos y servicios de mantenimiento no se deciden aquí.

A3-CAT-EVENT-01 permanece intacta: evoluciones objetivo separadas de EvolutionEvent
V1, con causalidad XP, perfil y época/versiones verificables, todos los cruces y
replay sin duplicados conforme a A2-EVO-01. No se deciden relaciones físicas de
eventos con este catálogo, XPEvent o perfiles ni consulta histórica conjunta.
Core/A3.5 conserva supresión/conservación/on_delete; Henry, EvolutionItem y
vestimentas siguen pendientes. Publicación, códigos/umbrales autorizados, migración
de perfiles y activación coordinada no se desbloquean. S3 V1 sigue único escritor XP.

#### Fase 1 · Persistencia preparatoria integrada

Implementada desde `ca27e88c74b175152ef5c1bddb1383b76e1002c7`, tras #86, e integrada
mediante #88 en develop `68f0c1ac415ad741b9ccae1beddadc292c80c2ca`.
Se añaden únicamente las tres tablas y restricciones mediante
ecomotor.0006_target_catalog_preparation, sin datos, RunPython, backfill o triggers.
No se ejecuta esa migración sobre las SQLite locales existentes durante el trabajo.

Todas las PK son BigAutoField. TargetCatalogVersion usa catalog_id/version
CharField(64), unicidad conjunta y checks distintos de cadena vacía.
TargetLevelThreshold usa catalog ForeignKey(PROTECT), level PositiveIntegerField
mayor que cero y minimum_xp PositiveBigIntegerField no negativa, con unicidad
catálogo/nivel. TargetEpoch usa catalog ForeignKey(PROTECT), code CharField(64),
name CharField(100), ordinal PositiveSmallIntegerField 1–7 y minimum_xp
PositiveBigIntegerField no negativa; unicidades catálogo/code y catálogo/ordinal,
checks de ordinal/XP y textos distintos de cadena vacía. Constraints con nombres
explícitos e independientes de V1; sin stat_points_awarded ni frozen/published.

full_clean aplica validación ORM, incluidos max_length y rangos de campos; save,
create o update no lo invocan automáticamente. Los checks/constraints efectivos
de BD son distintos: SQLite no impone max_length ni los checks de cadena vacía
rechazan todo texto compuesto solo por espacios. PROTECT protege la relación
padre-hijo al borrar mediante ORM, **no congela versiones ni sus hijos**, ni
implementa la defensa histórica frente a SQL directo/concurrencia de fase 2.

API interna de lectura preparatoria:
validate_target_catalog_version(catalog_version_id, *, using) → TargetCatalogSnapshot.
PK técnica entera exacta positiva representable y alias configurado explícito;
no selección por versión textual ni búsqueda de última versión. Tres lecturas del
mismo alias, filtradas por la PK del catálogo, materializan niveles/épocas y pasan
version.version y códigos ordenados a la API pública A1.1. LevelDefinition recibe
stat_points_awarded=0; no columna física ni cambio de S1/A1.1. El resultado A1.1
conserva texto de versión, no catalog_id/PK ni un certificado de identidad global.
El llamador conserva el contexto de la PK seleccionada; no infiere autoridad.

El lector rechaza metadatos vacíos/solo espacios, tipos textuales o longitudes
inválidos; A1.1 valida los números y catálogo completo sin conversiones silenciosas.
Entrada o estructura inválida: InvalidTargetCatalogError. Versión ausente:
TargetCatalogVersion.DoesNotExist. Fallos reales DatabaseError se propagan sin
convertirlos en catálogo vacío/válido. Sin reparaciones, escrituras o llamadas XP/A4.
No transacción ni snapshot estable entre lecturas o ante cambios posteriores:
el valor puro inmutable devuelto **no demuestra congelación o autorización**.

27 tests sintéticos distinguen integridad local, límites ORM/SQLite, validación
A1.1, alias y ausencia de escrituras, y migración aislada 0005→0006 preservando
esquema/datos V1 sin precarga. Resultados reales en PR. La aserción histórica de
0005 comprueba su propia aplicación, sin exigir ser la última migración futura.
En ese corte de fase 1, fase 2 y uso real seguían pendientes. La implementación
posterior de FREEZE-01 se precisa abajo; fuente/publicación oficial, referencias
reales, eventos objetivo, conservación Core/Henry y activación siguen pendientes.

### A3-CAT-FREEZE-01 · Congelación del catálogo objetivo

Decisión interna Equipo 5, aprobada en **02C-2 el 21/10/2026**, posterior a #88.
Desarrolla la fase 2 de IMMUT-01 sin reescribir PHYS-01 ni cambiar la separación
A3-CAT-EVENT-01. DAR3 conserva autoridad funcional; no ratificación externa.
**Antecedente conceptual #89:** campo, servicio, migración y triggers no estaban
implementados. El estado posterior de implementación para revisión se detalla abajo.

**Estado único:** TargetCatalogVersion.frozen_at es una fecha nullable generada
por el servidor. NULL significa preparatoria; una fecha, marcada como congelada.
No published, active, is_used ni estados redundantes. No descongelación ni cambios
en versiones congeladas; las modificaciones requieren una versión nueva. La
marca no equivale a publicación, autorización funcional ni prueba de validación
A1.1. Las tres tablas preparatorias y el lector de fase 1 se conservan.

**Servicio interno candidato:** freeze_target_catalog_version(catalog_version_id,
*, using). No es una API disponible. Validar identidad técnica exacta y alias;
leer la versión y validar todo su contenido mediante
validate_target_catalog_version y A1.1 dentro de **una única transacción SQLite
IMMEDIATE conforme a D-19**. Si es válida y no está congelada, establecer fecha
con hora del servidor. Si ya está congelada y sigue siendo válida, devolver el
estado existente sin actualizar la fecha: repetición idempotente, no una nueva
congelación. También una repetición rechaza contenido inválido; no lo repara.

Cualquier error de identidad, alias, versión ausente, catálogo incoherente o BD
impide confirmar una congelación parcial. Distinguir esas causas en la futura
implementación; fallos y timeout no se convierten en éxito. Rollback de la marca
ante error. No fijar aún excepciones/resultados Python definitivos. Respetar el
manejo transaccional existente de Django: no introducir un BEGIN manual dentro
de una transacción activa sin diseñarlo. El servicio no publica, concede XP,
activa catálogos ni garantiza por sí solo autorización funcional.

**Protección física aprobada:** triggers SQLite sobre las tres tablas con errores
explícitos RAISE(ABORT); SQL definitivo, nombres y detalle técnico pendientes.

- TargetCatalogVersion: impedir eliminación y cualquier cambio de una versión ya
  congelada, incluida descongelación y alteración de identidad o fecha. Rechazar
  inserciones directas con frozen_at no nulo. Permitir NULL→fecha únicamente sin
  modificación simultánea de identidad.
- TargetLevelThreshold y TargetEpoch: impedir inserciones que afecten a versiones
  congeladas, y actualizaciones o eliminaciones de sus filas. Impedir traslados
  hacia o desde versiones congeladas. Comprobar OLD.catalog_id y NEW.catalog_id
  cuando corresponda, sin limitar la protección al destino de una actualización.

Los triggers protegerán las versiones **marcadas** como congeladas; no certificarán
por sí solos que la marca se estableció mediante el servicio autorizado. No se
introduce una tabla ficticia de uso ni un protocolo de publicación para suplirlo.

**Migración y conservación:** futura migración posterior a
0006_target_catalog_preparation, con campo y protección física. Preferencia
aprobada de **instalación irreversible de triggers**, para que una reversión no
elimine silenciosamente la protección. Migraciones posteriores que reconstruyan
tablas deberán preservar o reinstalar las garantías. El corte documental #89 no instalaba
esa protección; la implementación posterior y sus pruebas se precisan abajo.

**Condiciones para consumidores futuros:** identidad exacta de versión y fuente
confiable, validación de catálogo completo, protección física instalada y efectiva,
configuración funcional autorizada y referencia causal verificable a la versión
utilizada. frozen_at por sí solo no cumple esas condiciones. Uso real bloqueado;
sin eventos objetivo, referencias reales de progresión, publicación o activación.
Core/A3.5, conservación, permisos, Henry, valores oficiales y consumidores siguen
pendientes. S3 V1 continúa como único escritor XP activo.

#### Implementación FREEZE-01 para revisión · posterior a #89

Base develop `0a95115b703d26676179d6f87476d5dde6f64ab8`; implementación en PR, no
integrada hasta merge. Único campo añadido: frozen_at DateTimeField(null=True,
blank=True), sin auto_now_add ni valor predeterminado. Fecha asignada por servidor.
Sin nuevos estados de publicación ni cambios a los modelos V1.

API interna: freeze_target_catalog_version(catalog_version_id, *, using) devuelve
TargetCatalogFreezeResult(catalog_version_id, frozen_at), dataclass frozen con
slots. Una repetición válida devuelve los mismos valores sin escritura ni nueva
lectura del reloj, pero vuelve a validar el catálogo completo mediante el lector
A1.1. El resultado no contiene ni acredita publicación, autorización o uso real.

Identidad exacta positiva representable y alias explícito; entradas inválidas:
InvalidTargetCatalogError. Configuración/transacción incompatible:
TargetCatalogFreezeTransactionError. Versión ausente: TargetCatalogVersion.DoesNotExist.
Los errores de catálogo y DatabaseError se propagan sin convertirlos en éxito ni
ocultar su causa. Sin reintentos automáticos. El servicio abre atomic antes de
leer versión y contenido, y guarda exclusivamente frozen_at dentro de ese bloque.

Se exige conexión SQLite con transaction_mode IMMEDIATE y timeout=5 según D-19,
y control de autocommit compatible. **Se rechaza cualquier transacción exterior
activa**, atomic anidado o autocommit manual desactivado: un savepoint no crea
un nuevo BEGIN IMMEDIATE. No BEGIN manual ni cambios de settings. La misma
frontera contiene lectura, validación completa y marca; fallo implica rollback.
El lector preparatorio por separado conserva sus límites de concurrencia; solo
su composición dentro de este servicio aporta la transacción controlada.

0007_target_catalog_freeze depende de 0006, añade el campo e instala **nueve
triggers BEFORE**: tres por tabla, para INSERT/UPDATE/DELETE. RunSQL recibe una
lista de sentencias CREATE TRIGGER completas, sin dividir sus cuerpos por punto
y coma; reverse_sql ausente hace irreversible la instalación. Revertir a 0006
lanza IrreversibleError y conserva campo, triggers, datos y registro de migración.
Sin datos, RunPython, triggers V1 ni modificaciones de tablas V1. No se aplica la
migración a las SQLite habituales durante este trabajo.

Los triggers usan RAISE(ABORT) y protegen todos los campos del padre congelado,
incluida PK, identidad y fecha; solo permiten NULL→fecha sin cambio simultáneo de
identidad. Hijos comprueban OLD/NEW catálogo según operación y bloquean ambos
sentidos de traslado. También se rechazan reemplazos INSERT OR REPLACE/UPDATE
OR REPLACE que pudieran eliminar implícitamente una fila congelada por conflicto
de PK o unicidad, aunque el destino nuevo fuera preparatorio. Los catálogos aún
preparatorios siguen siendo editables conforme a las restricciones locales.

**Garantía probada y límites:** DML ordinario ORM y SQL directo, incluidos
QuerySet.update y reemplazos; no defensa contra administradores capaces de
eliminar triggers o alterar el esquema. Una marca directa NULL→fecha sin cambiar
identidad sigue siendo posible y no prueba ejecución de A1.1 ni autorización.
Una repetición del servicio revalida y rechaza un catálogo inválido así marcado.
Futuras reconstrucciones de tablas deben preservar o reinstalar la protección.

25 tests sintéticos cubren servicio/rollback, DML ORM/SQL, nueve triggers efectivos
en sqlite_master, conservación de datos V1 y reversión irreversible. La concurrencia
usa TransactionTestCase, SQLite temporal file-backed y conexiones independientes:
doble congelación, cambios de niveles/épocas en ambos órdenes, rechazo si el cambio
previo invalida catálogo, BEGIN IMMEDIATE antes de SELECT, timeout real de cinco
segundos sin marca parcial y reintento explícito desde nueva transacción.
Resultados de las ejecuciones en PR. El test histórico de 0006 usa sus modelos de
estado para comprobar columnas de esa migración; el test del lector con ORM actual
aplica el esquema actual en su archivo temporal. No se relajan restricciones.

La protección física implementada para revisión no completa las condiciones de
consumo real anteriores: fuente/configuración funcional autorizadas, identidad y
referencia causal de uso siguen siendo necesarias. Sin escritor objetivo, eventos
objetivo, publicación, activación o migración de perfiles; Core/A3.5, Henry,
conservación y valores oficiales permanecen pendientes. S3 V1 intacto.

### A3-XP-PREVIEW-01 · Simulación interna de XP objetivo

Aprobación interna Equipo 5 en 02C-2 del 21/10/2026; base 68b8587 tras #90.
La congelación descrita en el corte anterior ya está integrada por #90; el
simulador no la invoca ni modifica su estado.
DAR3 conserva autoridad funcional. Implementación para revisión, sin autorización
de uso real, publicación, activación o escritor objetivo.

Se simula con catálogo persistido **preparatorio o congelado**. Entrada interna:
preview_target_xp(catalog_version_id, *, using, xp_before, amount). PK técnica exacta
positiva y alias configurado explícito; XP anterior entera no negativa y amount
entero estrictamente positivo, excluyendo bool y conversiones implícitas. Obtener
snapshot con validate_target_catalog_version y A1.1; delegar íntegramente cálculo
a plan_target_xp_grant de A2.1, sin copiar reglas de niveles, épocas o puntos.

Resultado TargetXPPreview, dataclass frozen/slots con catalog_version_id y plan
TargetXPPlan. Toda progresión se consulta por plan.progression: versión textual,
XP/niveles/épocas anteriores y finales, cruces e indicadores de elección. No datos
duplicados ni octava época, selección automática, eventos o progreso persistente.
El resultado es una observación informativa y no permanece vigente indefinidamente.

Frontera exterior transaction.atomic(using=using), SQLite IMMEDIATE y timeout=5,
con comprobación de conexión coherente con D-19 antes de la primera lectura.
Transacciones exteriores activas y autocommit manual desactivado se rechazan con
TargetXPPreviewTransactionError; un savepoint no inicia BEGIN IMMEDIATE. Sin BEGIN
manual, select_for_update como bloqueo SQLite, settings nuevos o I/O externo.
Solo lecturas y cálculo puro dentro de la transacción; salida del comando después
de cerrarla. Puede bloquear temporalmente escritores. No congelación ni cambios
de frozen_at, tampoco reparación o reintentos automáticos.

Errores originales conservados: InvalidTargetCatalogError para PK/alias/catálogo,
InvalidTargetXPError para XP anterior, InvalidTargetXPAmountError para importe,
TargetCatalogVersion.DoesNotExist para versión ausente y DatabaseError para SQL,
locks o timeout. Ninguno se transforma en snapshot vacío o plan favorable.

Comando interno preview_target_xp: --catalog-version-id, --database, --xp-before
y --amount son obligatorios. Adaptación mediante BaseCommand/CommandError;
salida legible con PK, versión, XP, niveles, épocas, cruces y desbloqueo. Aviso:
**SIMULACIÓN INTERNA — No se ha concedido XP real. El catálogo no queda autorizado ni activado por esta operación.**
Sin fixtures automáticos, endpoints, publicación ni acciones administrativas.

En el corte de PR #91, A3-CAT-USE-01A y A3-CAT-TRACE-01A se mencionaban en el
traspaso sin articulado adicional aportado; se registraron solo los límites
respaldados: no autorización de uso ni trazabilidad persistente real. La
conciliación posterior documenta abajo [USE-01A](#a3-cat-use-01a--condiciones-de-uso-autorizado-del-catálogo-objetivo)
y [TRACE-01A](#a3-cat-trace-01a--procedencia-y-trazabilidad-causal-del-catálogo-objetivo).
Se conserva PREVIEW-01: su resultado no autoriza ni genera registros de uso real.
Core/A3.5, Henry, configuración oficial y activación mantienen sus bloqueos.
S3 V1, congelación y APIs A1/A2 permanecen intactos.

Cobertura de implementación: 25 tests sintéticos de servicio/comando, delegación
A1.1/A2.1, inmutabilidad, errores y ausencia de DML. Se comparan todas las tablas
de la base aislada antes/después (con perfil, estadísticas e historial V1 presentes)
y frozen_at en catálogos preparatorios/congelados. La consola se comprueba fuera
de atomic. Concurrencia TransactionTestCase file-backed con conexiones distintas:
modificación de nivel o época antes/después de la lectura y cambios conjuntos de
umbrales sin mezclar estados, más timeout real y nueva simulación tras el fallo.
Resultados reales de regresiones/suite en PR; no implican pruebas de activación.


### A3-CAT-USE-01A · Condiciones de uso autorizado del catálogo objetivo

Aprobada internamente por Equipo 5 en **02C-2 el 21/10/2026**. Articulado conciliado
sobre b60b59b tras #91; no nueva aprobación ni requisito técnico literal DAR3 o
ratificación externa. **Contrato conceptual, sin implementación de autorización.**

Para **cada nueva concesión XP objetivo**, las condiciones aprobadas son:

1. Catálogo completo y coherente según A1.1, no solo filas localmente válidas.
2. Versión congelada y protegida físicamente conforme a
   [FREEZE-01](#a3-cat-freeze-01--congelación-del-catálogo-objetivo).
3. Identidad confiable compuesta por alias de BD, PK técnica exacta y comprobación
   de catalog_id y version; ni solo texto ni PK descontextualizada.
4. frozen_at, PK y versión textual no prueban aprobación funcional.
5. Una fuente confiable del servidor deberá acreditar contenido y aplicabilidad
   de la configuración autorizada.
6. El servidor resuelve la versión aplicable; el cliente no la selecciona como
   autoridad ni convierte sus parámetros en aprobación.
7. La falta de cualquiera de estas garantías rechaza la nueva concesión sin efectos.
8. La autorización efectiva debe ser coherente con la transacción de escritura
   D-19; no basta una observación previa desligada de esa operación.
9. Antes de habilitar consumidores reales, verificar protección física instalada
   y efectiva en la BD utilizada. **No se exige inspeccionar los nueve triggers
   en cada concesión.** No se elige aquí un servicio concreto de verificación.
10. Replay autorizado recupera la operación original sin exigir que su catálogo
    histórico siga autorizado para nuevas concesiones.
11. Identidad idempotente **(profile, operation_key)**, sin catálogo o versión,
    conforme a [A2-IDEM-01](ecomotor-target-xp-v1.md#4-identidad-y-replay-entre-versiones--a2-idem-01).

**Frontera de replay:** sigue requiriendo validación inicial de identidad, acceso
e integridad del historial. No elimina controles de seguridad ni autoriza recuperar
operaciones ajenas. No se recalculan resultados históricos desde el catálogo
actual ni se sustituye la operación original por una concesión nueva. Un importe
incompatible sigue siendo conflicto. Se conserva únicamente la evidencia realmente
persistida, sin inventar snapshots ausentes, como dispone A2-IDEM-01.

**A3-CAT-USE-01B pendiente, no implementada:** fuente física de aprobación funcional,
mecanismos de publicación o selección, configuración autorizada y vinculación con
valores de Óscar, integración de permisos/Core/futuros consumidores, servicios y
diseño físico de autorización. No campos approved/published/active, tablas ni
endpoints de autorización elegidos o implementados en este incremento.

Las identidades y separación de [PHYS-01](#a3-cat-phys-01--catálogo-objetivo-mínimo-candidato)
y [EVENT-01](#a3-cat-event-01--separación-de-eventos-objetivo) se conservan;
[A2-EVO-01](ecomotor-target-xp-v1.md#5-progresión-y-eventos-causales--a2-evo-01)
no se altera. [PREVIEW-01](#a3-xp-preview-01--simulación-interna-de-xp-objetivo)
puede simular un catálogo preparatorio: ello no satisface ni evita estas puertas
para concesiones reales. S3 V1 sigue único escritor activo.

### A3-CAT-TRACE-01A · Procedencia y trazabilidad causal del catálogo objetivo

Aprobada internamente por Equipo 5 en **02C-2 el 21/10/2026**; conciliación sobre
b60b59b tras #91. No requisito técnico literal DAR3 ni ratificación de Óscar,
Core/Equipo 0 o Henry. **Garantías conceptuales, sin diseño físico de procedencia aprobado.**

1. Toda nueva concesión XP objetivo conserva procedencia persistente, inequívoca
   e inmutable de la versión usada, **incluso sin cambio de época**.
2. La procedencia identifica una versión exacta, no solo su nombre textual.
3. Cada evolución objetivo mantiene causa XP verificable, perfil correspondiente
   y correspondencia histórica de época y catálogo.
4. Si una concesión cruza varias épocas, registrar cada cruce sin omisiones ni
   duplicados, según [A2-EVO-01](ecomotor-target-xp-v1.md#5-progresión-y-eventos-causales--a2-evo-01).
5. Nivel 8 no crea octava época ni evolución ficticia; solo desbloquea elección.
6. XP, procedencia, progreso y eventos causales objetivo se confirman o revierten
   conjuntamente bajo D-19. No se afirma atomicidad entre sistemas o BD distintos.
7. Replay conserva operación y procedencia originales, sin sumar XP, duplicar
   evoluciones o sustituir catálogo histórico por otro actual; conserva la frontera
   de identidad/acceso/integridad de USE-01A y la identidad de A2-IDEM-01.
8. Ausencia de procedencia objetivo **no demuestra V1** ni autoriza reconstruir
   datos inexistentes o atribuir versiones históricas por inferencia.
9. XPEvent y EvolutionEvent V1 conservan sus modelos, registros y semántica histórica.

**Preferencia conceptual aprobada:** registro de procedencia separado para
concesiones objetivo. No es aprobación de una tabla física, modelo o relación.
Se conserva [A3-CAT-EVENT-01](#a3-cat-event-01--separación-de-eventos-objetivo):
los futuros eventos de evolución objetivo son separados de EvolutionEvent V1,
aunque el diseño físico no esté fijado. FREEZE-01 protege contenido marcado, no
crea por sí mismo esta procedencia; PREVIEW-01 no crea concesiones ni registros.

**A3-CAT-TRACE-01B pendiente, no implementada:** modelo y tabla de procedencia,
campos y tipos, referencias/FKs al catálogo, perfil y causa XP, constraints,
unicidades e índices; on_delete, privacidad, conservación y ciclo de vida con
Core/A3.5; eventos físicos de evolución objetivo; consulta histórica conjunta
V1/objetivo; integración transaccional y tests de idempotencia/concurrencia.
No se eligen estas características por inferencia ni se generan eventos retroactivos.

Estas decisiones no habilitan escritor objetivo, publicación, autorización real,
migración de perfiles o activación. Se mantienen los acuerdos pendientes de
Óscar (configuración funcional), Core/Equipo 0/A3.5 y Henry, así como los demás
contratos necesarios. S3 V1 permanece como único escritor XP activo.

### A3-CAT-AUDIT-01 · Auditoría técnica del catálogo objetivo

Aprobación interna Equipo 5 en **02C-2 el 21/10/2026**, base aabf646 tras #92.
Implementación para revisión; no autorización funcional ni habilitación de XP.
Sin dependencias externas nuevas para implementar este diagnóstico técnico.

API interna: audit_target_catalog(catalog_version_id, *, using). Exige PK entera
exacta positiva representable y alias configurado explícito. InvalidTargetCatalogAuditInputError
rechaza entradas inválidas; TargetCatalogAuditTransactionError indica frontera
incompatible. SQLite IMMEDIATE/timeout=5 y transacción exterior atomic antes de
consultar registro de migraciones, esquema, triggers o catálogo. Rechaza atomic
exterior y autocommit manual incompatible; no BEGIN manual ni select_for_update.
Solo SELECT y PRAGMA de introspección de lectura dentro del bloqueo; sin DML,
DDL, probes de escritura, reparaciones, logs persistentes o salida de consola.

Comprobaciones en la misma fotografía:

- Existencia no destructiva de django_migrations y de sus columnas app/name;
  registro ecomotor.0007_target_catalog_freeze. Sin usar ejecutores/recorders que
  puedan crear esa tabla. Registro aplicado no acredita protección instalada.
- Tres tablas objetivo, columnas requeridas (incluida frozen_at), tipos declarados,
  nulabilidad, PK simple y referencias catálogo de los hijos, derivados de los
  modelos existentes. Si faltan o son incompatibles, no se invoca el ORM/lector
  sobre esa estructura. No es un verificador general de todos los constraints o
  del DDL de la BD; su conformidad se refiere a las comprobaciones enumeradas.
- Nueve triggers y tabla de destino, consultados en sqlite_master. Referencia
  única importada mediante import_module de la lista TRIGGERS de
  0007_target_catalog_freeze, sin copiar las reglas. Comparación de SQL completo:
  solo se toleran espacios extremos y un delimitador final; **no se normalizan
  operadores, literales, comentarios, espacios internos, condiciones OLD/NEW,
  nombres, referencias a frozen_at o cuerpos RAISE(ABORT)**. Diferencias incluso
  de formato interno se rechazan conservadoramente. Triggers adicionales sobre
  esas tablas tampoco obtienen conformidad: podrían interferir en la protección.
- Con estructura suficiente, identidad exacta de la fila, catalog_id/version y
  frozen_at (texto observado SQLite), más validación completa por
  validate_target_catalog_version/A1.1, sin duplicar reglas de umbrales. Fecha
  observada ilegible o identidad no representable producen CATALOG_INVALID.
  Ninguna marca demuestra que la congelación pasó por el servicio autorizado.

TargetCatalogAuditResult (frozen/slots) conserva using, catalog_version_id,
catalog_id, version, frozen_at, state y tupla defensiva checks. Estados:
PREPARATORY (marca NULL, **no congelada**), FROZEN (marca presente) y UNOBSERVED
(estructura insuficiente/versión ausente). Cada CatalogAuditCheck tiene name,
subject e issue_code opcional; passed indica comprobación superada. issues reúne
incumplimientos; technically_conformant exige comprobaciones completas favorables
y estado observado. Todos son datos informativos inmutables, no certificados.

Códigos: MIGRATION_0007_MISSING, SCHEMA_INCOMPLETE, TRIGGER_MISSING,
TRIGGER_SQL_MISMATCH, CATALOG_INVALID y CATALOG_NOT_FOUND. Se conservan incidencias
independientes y detalles de objeto/columna cuando corresponda. Un preparatorio
válido con protección correcta puede tener conformidad técnica observada, pero
no cumple por ello los requisitos de concesión real. Un congelado inválido según
A1.1 nunca obtiene conformidad global. Errores de conexión/permisos, SQL inesperado,
lock y timeout se propagan como DatabaseError: no se transforman en incumplimiento
funcional ni éxito. No capturas generales de errores de programación ni retries.

Comando audit_target_catalog, argumentos obligatorios --catalog-version-id y
--database. BaseCommand/CommandError; imprime identidad, estado, comprobaciones
e incumplimientos fuera de atomic. Entrada inválida: código 2. Diagnóstico
completado con incumplimientos: código 2; fallo operativo/frontera incompatible:
código 3 sin resumen favorable; éxito: código 0 y mensaje exacto:
**CONFORMIDAD TÉCNICA OBSERVADA — No constituye autorización funcional ni habilita concesiones XP.**
No instala fixtures, catálogos, triggers ni otras configuraciones.

Tests sintéticos en SQLite temporal: esquema 0006 sin frozen_at, registro ausente,
tablas/columnas/tipos/PK/FKs incompletos, nueve definiciones correctas y ausentes o
alteradas, estados preparatorio/congelado e invalidez A1.1; inmutabilidad, ausencia
de DML/DDL, delegación al lector y códigos 0/2/3. Concurrencia TransactionTestCase
file-backed y conexiones independientes: cambios de catálogo y retirada de trigger
antes/después de obtener la transacción, timeout real y nueva auditoría tras fallo.
Solo las fixtures temporales manipulan esquema y triggers; nunca la BD habitual.
Resultados reales de ejecuciones en PR; sin modelos o migraciones nuevos.

**Límites:** observación puntual; puede bloquear escritores mientras dura y perder
vigencia después. No prueba autorización funcional, publicación, procedencia
persistente ni seguridad frente a administradores que alteren el esquema. No
sustituye [USE-01A](#a3-cat-use-01a--condiciones-de-uso-autorizado-del-catálogo-objetivo)
ni completa USE-01B/TRACE-01B. No llama a congelación, PREVIEW-01, S3 o Rewards ni
conecta un escritor XP objetivo. Óscar (configuración oficial), Core/A3.5, Henry y
consumidores mantienen sus pendientes. S3 V1 sigue único escritor XP activo.

## 4. Inventario, diagnóstico y migración · A3-MIG-01

Inventariar perfiles, XP, niveles, épocas, XPEvent/EvolutionEvent, estadísticas y
sus eventos, especializaciones/progresos y dependencias de Duckies. Registrar
procedencia y evidencia suficiente para evaluar compatibilidad, sin inventar
snapshots no persistidos. La ausencia de historia completa no autoriza fabricarla.

Distinguir registros compatibles, registros que requieren decisión de transición
y registros incoherentes. **Diagnóstico no es permiso automático para migrar**,
clasificar persistentemente, conceder XP o reparar. No modificar eventos, reasignar
CharacterStats a una opción o recalcular XP/niveles por inferencia; tampoco borrar
puntos heredados, progresos o historiales de asignación.

La migración futura será explícita, trazable, idempotente y protegida frente a
concurrencia. Transformaciones concretas requieren política autorizada, inventario
real, esquema compatible aprobado y acuerdos Core/P5 y propietarios. Las garantías
se verificarán mediante ensayos y pruebas, no por adoptar este contrato.

## 5. Escritor único y control de versión · A3-WRITER-01

Mantener S3 V1 y su interfaz/comportamiento hasta activación autorizada. Adoptar
un **único punto interno futuro de entrada**, con decisión confiable del servidor,
no un parámetro de cliente. No se publica firma, endpoint ni dispatcher disponible.
Separar comprobación de operación histórica y elegibilidad de escritura nueva (§6).

Para primera activación, preferir **corte global coordinado**, frente a escritores
V1/objetivo activos simultáneamente por cohortes. Preparación, suspensión temporal
de concesiones, activación objetivo y detención segura son estados conceptuales
de despliegue: no constantes Django ni mecanismos ya implementados. Una política
persistente o catalog_version no selecciona automáticamente un escritor.

El corte debe impedir que escrituras V1 en curso o consumidores antiguos vuelvan
a conceder tras la transición. Suspender y drenar antes de migrar/activar; identidad
idempotente compartida y controles transaccionales no sustituyen ese acuerdo de
activación. No se activan rutas paralelas o acceso sin autorización.

## 6. Replay entre versiones · A3-REPLAY-01

Conservar UNIQUE(profile, operation_key), sin añadir versión para duplicar un
premio. Orden conceptual coherente con A2-IDEM-01:

1. Validación inicial de identidad, autorización, importe y clave.
2. Abrir transacción D-19 en el alias común y efectuar validaciones estructurales
   necesarias antes de decidir sobre estado mutable.
3. Buscar primero XPEvent por (profile, operation_key).
4. Si existe, comprobar importe, snapshots y causalidad; conflicto o incoherencia
   se rechazan sin efectos. Recuperar datos históricos disponibles **sin exigir
   catálogo, clasificación o elegibilidad del escritor de concesiones nuevas**.
5. Solo si no existe, comprobar clasificación y escritor autorizados por el servidor;
   después validar configuración/progreso y aplicar la nueva concesión conjunta.

La autorización inicial sigue siendo obligatoria en replay; este orden no abre
una ruta alternativa ni cambia la semántica actual S3. XPEvent V1 no guarda
versión, nivel o época como snapshots. EvolutionEvent referencia la etapa sin
guardar sus atributos históricos originales. No reconstruir códigos, umbrales,
niveles/puntos ausentes a partir del catálogo actual ni prometer replay completo.

**Nuevas operaciones objetivo requieren procedencia persistente e inmutable**.
Representación física pendiente; no se añade campo a XPEvent, tabla auxiliar o
FK por este acuerdo. No inventar procedencia de los eventos V1 ni alterar su identidad.

## 7. Resultados y puntos · A3-RES-01

S3 V1 sigue concediendo puntos por nivel mientras esté activo. Nuevas concesiones
objetivo no los conceden; compatibilidad prevista: stat_points_awarded=0 y
available_points_after=None. No significan saldo heredado cero ni autorizan borrarlo.
No reinterpretar resultados V1 o campos históricos sin snapshot. La interfaz
compartida final sigue pendiente, respetando las limitaciones de los contratos
históricos; no se cambia XPGrantResult ni ningún servicio ahora.

## 8. Secuencia de activación · A3-DEPLOY-01

| Etapa conceptual | Condición / alcance |
| --- | --- |
| 1. Inventario | Datos y dependencias reales identificados; no transformación automática. |
| 2. Preparación de esquema compatible | Solo cuando su diseño y migraciones estén aprobados; conservar identidades/historia V1. |
| 3. Clasificación y auditoría | Procedencia y transición explícitas; diagnósticos no son autorización de migración. |
| 4. Ensayo de migración aislado | Verificar política, integridad, idempotencia y comportamiento de consumidores sin modificar datos habituales. |
| 5. Suspensión y drenaje de escritores antiguos | Evitar concesiones en curso o rutas antiguas que compitan con migración/activación. |
| 6. Migración autorizada | Ejecución explícita/trazable, idempotente y protegida frente a concurrencia bajo política aprobada. |
| 7. Activación del escritor objetivo | Servidor autorizado, catálogo y datos coherentes, escritor único y consumidores compatibles. |
| 8. Supervisión y detención segura | Detectar inconsistencias y detener de forma controlada, sin reparaciones silenciosas o doble escritura. |

La activación exige datos coherentes, catálogos autorizados, escritor único,
consumidores compatibles, pruebas superadas y acuerdos externos necesarios.
**No prometer reversión automática a S3 después de conceder XP objetivo.**
Detención segura no equivale a rollback de negocio ni restaura interpretación V1;
recuperación posterior requiere revisión explícita. No se implementan flags,
comandos de despliegue, transiciones persistentes o transformaciones de datos aquí.

D-19 sigue aplicando a futuras operaciones críticas: atomic antes de lecturas
mutables, SQLite BEGIN IMMEDIATE, timeout 5 s, constraints/idempotencia, rollback
y retry explícito en nueva transacción. Sin I/O externo dentro de transacciones,
retry automático, row locking efectivo por select_for_update en SQLite o garantía
entre BD independientes. Esto no demuestra por sí solo que un despliegue global
sea atómico; suspensión/drenaje y coordinación deben diseñarse y probarse.

## 9. Dependencias reales con Duckies

Duckies está integrado por PR #54. [models.py](../../apps/duckies/models.py) define
EvolutionItem.stage como OneToOne a EvolutionStage, PROTECT. En
[services.py](../../apps/duckies/services.py), initialize_ducky y
sync_historical_outfit buscan vestimenta por current_stage_code del perfil;
select_historical_outfit consulta EvolutionStage y compara ordinales. También
consulta active_specialization_code para condiciones de vestimenta/selección.

Época de progresión, identidad jugable y apariencia histórica tienen propietarios
y responsabilidades diferenciados. Cambiar referencias del catálogo, semántica
de códigos o selección requiere coordinación con Henry y consumidores; no se
presupone que el cambio sea transparente para Duckies. El código observado no
ratifica todas las propuestas funcionales DOC-5/02C. No se modifica apps.duckies,
su esquema o sus contratos ni se aprueba una migración de sus referencias.

## 10. A3.1 · Propuesta de auditoría pura posterior

Candidatos: apps/ecomotor/legacy_transition_audit.py y
apps/ecomotor/test_legacy_transition_audit.py. **No se crean en esta PR**;
nombres/firmas definitivos se concretarán antes de implementar en 01B.
Recibir snapshots explícitos y emitir diagnósticos inmutables; sin ORM, escrituras,
XP, clasificación persistente o autorización de migración. Diagnosticar no migra.

Pruebas futuras: entradas/snapshots inválidos, compatibilidad y casos que exigen
decisión frente a incoherencias, copia/inmutabilidad, límites de historia disponible
y ausencia de efectos. Pruebas de migración, concurrencia, rollback y activación
son posteriores y mantienen sus bloqueos; no se afirman implementadas o ejecutadas.

## 11. Pendientes y límites

Siguen pendientes modelo físico de clasificación, catálogo objetivo físico,
relaciones causales de nuevas evoluciones, adaptación PlayableOption y procedencia
persistente de nuevas concesiones. También inventario/transformaciones de datos
reales, interfaz compartida, conservación/anonimización/eliminación/on_delete
Core/P5, contratos Duckies/consumidores, catálogos y XP numérica autorizados, y
pruebas de migración, concurrencia, rollback y activación.
No se desbloquean Rewards F2-A, dominio persistente, S13-A2 o economía/inventario.
A1/A2 puros integrados no autorizan activar objetivo. Solo documentación: sin
código, modelos, migraciones, tests nuevos o ejecución de tests Django.

## 12. A3.2 · Extracción de evidencia separada de auditoría

Actualización sobre `8024fa7`: A3.1 ya está integrado por PR #58 como
[auditor puro y clases de snapshots](../../apps/ecomotor/legacy_transition_audit.py).
§10 conserva su propuesta histórica previa a implementación; su extractor en
pruebas de aislamiento es código de test, no un servicio de producción instalado.
A3.1 recibe evidencia, no lee BD ni autoriza migraciones; COMPATIBLE tiene alcance
estructural limitado, no certificación global de historia/Duckies o activación.

[A3.2 · Inventario legacy](ecomotor-legacy-inventory-v1.md) documenta el extractor
futuro aprobado internamente: un perfil, alias confiable, transacción corta
IMMEDIATE/timeout 5 con costes de bloqueo, snapshots tipados y cobertura íntegra
o fallo. Causalidad extranjera confirmada falla sin historiales ajenos; causa
realmente ausente se conserva si representable para diagnóstico A3.1 posterior.
Ausencia observada de stats es None, no error de lectura. La extracción no llama
automáticamente al auditor, clasificador o migración, ni activa política.

Fuera del alcance integral: asignaciones de stats, especializaciones, Duckies,
umbrales históricos, puntos gastados y futura compatibilidad de migración.
Operation_key se conserva exacta sin registrarla en logs/errores/trazas/exportaciones.
Privacidad y autorización Core siguen obligatorias. S3 V1 continúa activo; no se
modifica ni se ejecuta migración/activación. A3.2 y sus tests son futuros 01B,
sin cambios iniciales de A3.1, S3, modelos/migraciones o configuración.
[Pendientes A3.2](../pending-decisions.md#16-a32--alcance-y-validaciones-pendientes).

## 13. INT-A-00 · Plan de integración progresiva · 26/10/2026

**Plan aprobado internamente en 02C-2 el 26/10/2026, exclusivamente documental.**
Baseline: develop `032e05a25d84c200d6da5b93278c874164984d79`. Las PR #114–#117
integran REW-MULTI-03 en el laboratorio persistente. Según el traspaso del Equipo 5,
también ha sido validado interactivamente en ese entorno sintético; esta PR no
repite ni amplía esa validación. El [contrato combinado](ecomotor-target-demo-rewards-combined-v1.md)
conserva sus evidencias y cortes históricos. DAR3 mantiene autoridad funcional;
no hay ratificación de Óscar/Core ni autorización de integración productiva.

### Etapas y entregables de planificación

| Etapa | Trabajo previsto y resultado que debe revisarse |
| --- | --- |
| INT-A1 · Contraste | Comparar `apps.ecomotor` con `apps/ecomotor/ecomotor_target_demo/`: inventariar funcionalidades, reglas, servicios y dependencias; distinguir componentes reutilizables, adaptaciones condicionadas por contratos y elementos exclusivamente demostrativos. El resultado será un contraste trazable, no un traslado automático de código. |
| INT-A2 · Evolución | Planificar siete épocas objetivo, elección desde nivel 8 y eventos de evolución separados, conservando íntegramente identidades, referencias e interpretación de historiales V1. Reutilizar A1.1/A1.2, A2.1, catálogos objetivo, congelación, auditoría técnica y reglas puras A3.3; identificar las piezas persistentes y contratos todavía pendientes. No inferir autorización de catálogo congelado, auditoría conforme o clasificación. |
| INT-A3 · Rewards | Planificar Rewards en Parte A principal con contratos de Core, Bank, Duckies y emisores reales: identidad/autorización del hecho y destinatario, reglas autorizadas, causalidad, replay, errores y garantías transaccionales acordadas con propietarios. Los usuarios, umbrales, presupuestos, artículos, reglas e importes sintéticos no se convierten en oficiales. |

### Orden lógico y puertas de avance

1. Documentar plan y dependencias INT-A1/A2/A3, comenzando por el contraste; cada
   implementación posterior requerirá alcance y revisión propios.
2. Obtener acuerdos Core/A3.5 y evidencia A3.6 suficiente y vigente. Las
   [cinco respuestas concretas requeridas](ecomotor-classification-core-boundary-v1.md#7-int-a-00--respuestas-concretas-requeridas-de-core--26102026)
   siguen pendientes; una preferencia interna no las sustituye.
3. Resolver autorización USE-01B y trazabilidad TRACE-01B, conforme a las
   fronteras de §3; no simularlas con datos de laboratorio.
4. Implementar y probar el escritor XP objetivo separado solo tras resolver sus
   precondiciones. Estar implementado o probado no autoriza activarlo.
5. Ensayar compatibilidad V1 y transición autorizada de escritor único conforme
   a §4–§8: suspensión/drenaje y consumidores coordinados, sin reinterpretar
   historia ni duplicar concesiones. S3 V1 continúa como único escritor XP activo
   fuera del laboratorio; no activar simultáneamente ambos escritores.
6. Integrar las recompensas combinadas de REW-MULTI-03 en Parte A con Core,
   Bank, Duckies y emisores reales solo
   después de cerrar los contratos necesarios y autorizar la transición. Las
   pruebas locales de atomicidad no demuestran esa integración global.
7. Ejecutar pruebas conjuntas y plantear la eventual retirada del laboratorio
   únicamente cuando exista un reemplazo funcional verificado y estén resueltas
   sus dependencias de acceso. INT-A-00 no aprueba fecha ni eliminación.

**Precisión de 02C-2:** la precedencia evolución objetivo → recompensas
combinadas describe este traslado del laboratorio; no modifica ni bloquea
automáticamente Rewards F2-A. Su arquitectura independiente, aprobada
internamente en [DOC-6 / Rewards §12](rewards-v0.md#12-f2-a--persistencia-y-xp-histórica-local--doc-6),
contempla XP histórica positiva mediante S3 V1 y NO_REWARD, con identidad,
persistencia, idempotencia y causalidad propias. F2-A puede continuar diseño o
preparación por sus propias dependencias, sin esperar automáticamente a INT-A2
o INT-A3; tampoco queda desbloqueada por la validación de REW-MULTI-03.
Conserva los acuerdos pendientes de Core sobre identidad, autorización,
conservación, relaciones físicas y demás condiciones de su contrato. Su alcance
original no incorpora DuckyCoins, HINT ni efectos combinados V4. Esta precisión
no autoriza activar Rewards productivo ni dos escritores XP simultáneos; S3 V1
permanece como único escritor XP activo fuera del laboratorio.

Se conserva la identidad de replay XP `(profile, operation_key)` de §6, sin
añadir versión o escritor como vía para repetir una concesión. Resolver historia
compatible antes de elegibilidad nueva, con autorización y límites de evidencia
histórica intactos. Las identidades sintéticas Rewards y las claves causales del
laboratorio no definen por sí solas el contrato de emisores productivos.

### Coordinación con Henry y conservación del laboratorio

Según el traspaso, el enlace añadido por Henry desde `feature/demo-interfaz`
hacia Rewards es navegación entre demos: no integra inventarios, economías,
sesiones ni contratos productivos. Antes de retirar `ecomotor_target_demo`, se
debe acordar y verificar con Henry una alternativa funcional para ese acceso.
No se modifica su rama ni se envían comunicaciones desde esta tarea.

El fallo `DemoPackageLayoutTests.test_only_the_new_physical_package_exists`
comunicado por Henry permanece pendiente de diagnóstico y evidencia reproducible.
No se atribuye a Rewards ni se determina su causa sin evidencia; este plan no
modifica código, tests, paquetes ni sus expectativas para resolverlo.

Los [pendientes INT-A-00](../pending-decisions.md#33-int-a-00--puertas-de-integración-progresiva--26102026)
registran las puertas abiertas. No código, modelos, migraciones, seeds, cambios
de settings/despliegue, refactorización o retirada del laboratorio por este corte.

## 14. INT-A1 · Contraste técnico del laboratorio y Parte A · 26/10/2026

**Estado:** contraste documental del código de `develop` en `dae5212bf78a516ef18cf291ca94ceb1807fb7a7`, para revisión de 02C-2. No se aprueban implementaciones productivas, esquemas, permisos ni valores oficiales. Se conserva la planificación de §13 y la independencia de Rewards F2-A.

**Criterio:** «Conservar» significa reutilizar el contrato ya integrado; «Adaptar» significa extraer garantías, no copiar implementación; «No trasladar» comprende identidades, tablas y parámetros ficticios. Ninguna capacidad de la demo supone publicación o autorización.

### Matriz trazable

| Bloque | Parte A principal: evidencia y estado real | Laboratorio: evidencia y diferencia | Dictamen y dependencia |
| --- | --- | --- | --- |
| **1. Progresión y catálogo** | [A1.1 `target_catalog_validation.py`](../../apps/ecomotor/target_catalog_validation.py), [A1.2 `target_progression.py`](../../apps/ecomotor/target_progression.py) y [A2.1 `target_xp_plan.py`](../../apps/ecomotor/target_xp_plan.py): validación, cálculo y planificación puros ya integrados, siete épocas e indicador de elección desbloqueada desde nivel 8, sin octava época ni puntos de ascenso objetivo. | [`data.py`](../../apps/ecomotor/ecomotor_target_demo/data.py) y [`catalog.py`](../../apps/ecomotor/ecomotor_target_demo/catalog.py): códigos, umbrales, versión y seed sintéticos exactos. | **Conservar** A1.1/A1.2/A2.1 (A1.1 conserva metadatos heredados de puntos, sin que el cálculo objetivo los conceda); **no trasladar** versiones, códigos ni umbrales ficticios. Pendientes valores y fuentes oficiales. |
| **1. Catálogo persistente** | [`models.py`](../../apps/ecomotor/models.py): `TargetCatalogVersion`, `TargetLevelThreshold`, `TargetEpoch`; [`target_catalog_persistence.py`](../../apps/ecomotor/target_catalog_persistence.py): lectura validada; [`target_catalog_freeze.py`](../../apps/ecomotor/target_catalog_freeze.py) y [`target_catalog_audit.py`](../../apps/ecomotor/target_catalog_audit.py): congelación/auditoría técnicas implementadas. | [`catalog.py` demo](../../apps/ecomotor/ecomotor_target_demo/catalog.py): seed preparatorio seguido de congelación en SQLite propia. | **Conservar** infraestructura; `frozen_at`/auditoría no acreditan publicación, autorización USE-01B ni procedencia TRACE-01B. **No trasladar** seed. |
| **2. XP y evolución V1** | [`xp_service.py`](../../apps/ecomotor/xp_service.py) es S3 V1 activo; [`XPEvent`, `EvolutionEvent`, `EvolutionStage`](../../apps/ecomotor/models.py) conservan identidad `(profile, operation_key)` de XP, eventos históricos y puntos de ascenso V1. Replay V1 no reconstruye snapshots inexistentes. | [`services.py` demo](../../apps/ecomotor/ecomotor_target_demo/services.py) concede XP ficticia sin llamar a S3. | **Conservar V1 sin reinterpretar**, sin doble escritor ni adoptar claves de sesión de demo. |
| **2. XP objetivo y causalidad** | [`target_xp_preview.py`](../../apps/ecomotor/target_xp_preview.py) combina lector y A2.1, pero solo simula; [`models.py`](../../apps/ecomotor/models.py) no contiene aún `TargetEvolutionEvent` productivo ni escritor objetivo. | [`services.py` demo](../../apps/ecomotor/ecomotor_target_demo/services.py) usa `_grant_xp_in_transaction`; [`models.py` demo](../../apps/ecomotor/ecomotor_target_demo/models.py) guarda `DemoTargetXPEvent` (snapshots y códigos/niveles cruzados) y un `DemoTargetEvolutionEvent` por época cruzada (causa XP, época, ordinal y catálogo exacto). | **Adaptar** snapshots, múltiples cruces y replay bajo contrato; **no copiar** esquema `DemoTarget*`. Requiere TRACE-01B, A3.5/A3.6, catálogo autorizado, escritor objetivo separado y conservación V1. |
| **3. Clasificación** | [`legacy_transition_audit.py`](../../apps/ecomotor/legacy_transition_audit.py) A3.1, [`legacy_inventory_reader.py`](../../apps/ecomotor/legacy_inventory_reader.py) A3.2 y [`profile_classification_rules.py`](../../apps/ecomotor/profile_classification_rules.py) A3.3 están integrados; no existen aún modelos físicos `ProfileProgressionPolicy`/evento de clasificación ni servicio de confirmación real. | [`DemoTargetProgress`](../../apps/ecomotor/ecomotor_target_demo/models.py) es una partida persistente, no clasificación de `UserProfileEcomotor`. | **Conservar** auditor A3.1 y reglas A3.3 puros, y lector ORM A3.2 de solo lectura. **No inferir** clasificación por nivel o sesión. Persistencia depende de Core/A3.5 y evidencia vigente/suficiente A3.6. |
| **3. Identidad y Core** | [`xp_service.py`](../../apps/ecomotor/xp_service.py) recibe perfil Ecomotor persistido; [frontera Core A3.5](ecomotor-classification-core-boundary-v1.md) mantiene pendientes operador, permisos, ciclo de vida, retención, privacidad y `on_delete`. | [`services.py` demo](../../apps/ecomotor/ecomotor_target_demo/services.py) usa token firmado y `session_owner`; [`DemoTargetProgress`](../../apps/ecomotor/ecomotor_target_demo/models.py) tiene `synthetic_user` opcional. | **No trasladar** tokens/identidades sintéticas como autenticación/atribución Core; **adaptar** controles a contexto servidor y perfil canónico acordados. |
| **4. Estadísticas y opción** | [`target_stats_validation.py`](../../apps/ecomotor/target_stats_validation.py), [`target_stats_config_validation.py`](../../apps/ecomotor/target_stats_config_validation.py) y [`target_stats_preparation.py`](../../apps/ecomotor/target_stats_preparation.py): validación/preparación puras existentes; [`target_stats_resolution.py`](../../apps/ecomotor/target_stats_resolution.py) rechaza siempre la resolución real, sin fuente autorizada. | [`stats_definitions.py`](../../apps/ecomotor/ecomotor_target_demo/stats_definitions.py) usa bases cero y presupuesto 45 sintéticos. | **Conservar** validadores, **no oficializar** 45/bases/códigos demo. Resolver fuente de definiciones, parámetros y permisos antes de elegir. |
| **4. Estado jugable** | [`models.py`](../../apps/ecomotor/models.py) tiene especializaciones y progreso de dominio V1, no estado de opciones objetivo productivo. | [`playable_services.py`](../../apps/ecomotor/ecomotor_target_demo/playable_services.py) implementa configure/switch/redistribute, revisión, historial y replay; [`models.py` demo](../../apps/ecomotor/ecomotor_target_demo/models.py) define `DemoTargetOptionConfiguration`, `DemoTargetPlayableState`, `DemoTargetPlayableEvent`. | **Adaptar** control de revisión, idempotencia e historial cuando haya contrato; **no copiar** modelos ni asociar opción ficticia a Ducky real. Dependencias A4, Core, Henry. |
| **5. Rewards F1-A / F2-A** | [`reward_types.py`](../../apps/ecomotor/reward_types.py), [`reward_identity.py`](../../apps/ecomotor/reward_identity.py), [`reward_rules.py`](../../apps/ecomotor/reward_rules.py): F1-A puro implementado. [DOC-6 / Rewards F2-A](rewards-v0.md#12-f2-a--persistencia-y-xp-histórica-local--doc-6): arquitectura interna **no implementada** para XP histórica positiva con S3 V1 y NO_REWARD; requiere Core. | [`reward_demo_rules.py`](../../apps/ecomotor/ecomotor_target_demo/reward_demo_rules.py) utiliza F1-A con hechos/reglas inventados; [`DemoTargetRewardEvent`](../../apps/ecomotor/ecomotor_target_demo/models.py) no es el modelo F2-A. | **Conservar F1-A. F2-A es independiente** de INT-A2/INT-A3: puede avanzar en diseño por sus propias puertas sin quedar desbloqueado por la demo. No incluye automáticamente monedas, HINT ni V4. |
| **5. Rewards combinado** | No existe coordinador combinado productivo en Parte A ni autorización de Rewards F2-A. | [`reward_demo_services.py`](../../apps/ecomotor/ecomotor_target_demo/reward_demo_services.py) implementa V4: un `DemoTargetRewardEvent` con causas XP/Bank/Item, atomicidad local, histórico y replay; [`reward_demo_rules.py`](../../apps/ecomotor/ecomotor_target_demo/reward_demo_rules.py) fija 700 XP + 5 DuckyCoins + 1 HINT ficticios. | **Adaptar** garantías de unicidad de hecho, causalidad, resultado histórico y rollback para INT-A3. **No trasladar** importes, tokens, esquemas V4 ni identidades demo. |
| **5. Bank y Duckies** | [`bank/services.py`](../../apps/bank/services.py) proporciona `credit_coins` y ledger; [`duckies/services.py`](../../apps/duckies/services.py) proporciona `grant_item`; sus [modelos Bank](../../apps/bank/models.py) y [modelos Duckies](../../apps/duckies/models.py) tienen propietarios propios. | [`reward_demo_services.py`](../../apps/ecomotor/ecomotor_target_demo/reward_demo_services.py) compone estos servicios en la SQLite aislada, no en un sistema global integrado. | **Conservar** propiedad de Bank/Duckies; **adaptar** coordinación tras contratos. La transacción en una SQLite no asegura atomicidad entre bases ni inventario común con Henry. |
| **Aislamiento y navegación** | [`alpha_urls.py`](../../apps/ecomotor/alpha_urls.py) expone consulta V1 bajo montaje futuro de Core. | [`target_persistent_demo_settings.py`](../../apps/ecomotor/target_persistent_demo_settings.py), [`isolation.py`](../../apps/ecomotor/ecomotor_target_demo/isolation.py) y [`urls.py` demo](../../apps/ecomotor/ecomotor_target_demo/urls.py) aíslan SQLite, sesión, alias y ruta. Henry comunica enlace desde `feature/demo-interfaz`; no se ha comprobado una identidad/economía compartida. | **No trasladar** ruta/settings/sesión demo. Mantener laboratorio hasta reemplazo probado y alternativa de navegación acordada con Henry. Test de layout comunicado: causa no confirmada. |

### Conclusiones y asignación

**Conservar:** A1.1/A1.2, A2.1/preview como cálculo/consulta, persistencia-congelación-auditoría de catálogo, auditor A3.1 y reglas A3.3 puros, lector ORM A3.2 de solo lectura, validación/preparación estadística, F1-A y toda la historia/semántica S3 V1.

**Adaptar bajo contratos:** servicio XP objetivo **separado**, eventos causales de evolución objetivo, clasificación persistente autorizada, elección jugable real, Rewards combinado coordinado con Core/Bank/Duckies. **No trasladar:** modelos `DemoTarget*`, sesión y `synthetic_user`, semillas/catálogos/umbrales/45/bases cero sintéticos, recompensas 700/5/HINT y URLs/SQLite de laboratorio.

**Destino:** INT-A2 se ocupa de evolución objetivo y su compatibilidad V1; INT-A3 de recompensas combinadas con emisores/propietarios; retirada futura solo después de sustitución verificada. Rewards F2-A sobre S3 V1 sigue la ruta independiente DOC-6, no bloqueada automáticamente por INT-A2/INT-A3 ni aprobada por el éxito del laboratorio.

### Primer incremento INT-A2 recomendado (propuesta, no decisión)

**INT-A2.1 propuesto: preparador puro de propuestas de evolución causal, sin ORM ni escrituras.** Reutilizar `TargetXPPlan.progression.crossed_epoch_codes` (ya calculados por A1.2/A2.1), no reimplementar umbrales. A partir de un plan obtenido mediante `plan_target_xp_grant()` sobre un snapshot A1.1 validado y referencias explícitas de causa/catálogo suministradas por el llamador, producir una secuencia inmutable de propuestas, una por época cruzada, sin persistirlas ni autenticar tales referencias. Construir directamente un `TargetXPPlan` no acredita por sí solo la coherencia semántica del plan ni autorización. No elegir automáticamente versión, escritor, usuario o clave; nunca tocar `EvolutionEvent` V1. Esto reduce riesgo antes de decidir tablas, `on_delete`, identidad histórica y activación; no debe confundirse con `TargetEvolutionEvent` implementado.

**Alternativa:** cerrar primero solo el contrato físico/causal TRACE-01B y posponer cualquier adaptador. Preferible si 02C-2 considera prematuro fijar incluso la forma de una propuesta causal. La arquitectura del incremento debe ratificarse antes de programarlo.

**Puertas:** para el preparador puro, aprobación de interfaz y límites sin autoridad; para persistencia posterior, TRACE-01B, Core/A3.5, A3.6, USE-01B, datos oficiales, escritor objetivo separado y consumidores. No bloquear ni fusionar este trabajo con F2-A.

**Tests futuros, no ejecutados aquí:** cero/uno/múltiples cruces, salto de seis épocas, nivel 8 sin octava época, orden/unicidad, ausencia de puntos por ascenso objetivo, referencias y versiones explícitas sin inventar, errores estructurales, copia/inmutabilidad y cero ORM/SQL/efectos. Tras aprobar persistencia: causalidad XP, replay idempotente, concurrencia, rollback, compatibilidad con V1 y retención. INT-A1 no ejecuta tests Django.

**Estado final:** inventario documental; sin activación, backfill, migraciones, integración productiva, retirada del laboratorio ni modificación de módulos propietarios.

## 15. INT-A2-T01 · Contrato causal mínimo de evolución objetivo · 26/10/2026

**Estado:** estudio documental del código y contratos en `develop` `13f00114b4bd825333185142fce36076abd32c79`, para revisión de 02C-2. Se desarrollan garantías ya aprobadas internamente en [A3-CAT-TRACE-01A](#a3-cat-trace-01a--procedencia-y-trazabilidad-causal-del-catálogo-objetivo), [A2-EVO-01](ecomotor-target-xp-v1.md#5-progresión-y-eventos-causales--a2-evo-01), [A2-IDEM-01](ecomotor-target-xp-v1.md#4-identidad-y-replay-entre-versiones--a2-idem-01) y [A3-CAT-EVENT-01](#a3-cat-event-01--separación-de-eventos-objetivo). **No se aprueba un esquema físico ni se cierra TRACE-01B**; las alternativas nuevas identificadas abajo son propuestas, no decisiones tomadas. DAR3 mantiene autoridad funcional y Core no ha ratificado relaciones, permisos o conservación.

### 15.1. Causa XP V1 y frontera de escritura

[`XPEvent`](../../apps/ecomotor/models.py) ya materializa una concesión histórica con `profile`, `operation_key`, `amount`, `xp_before`, `xp_after` y `created_at`; su unicidad real es `(profile, operation_key)`. [`grant_historical_xp`](../../apps/ecomotor/xp_service.py) es el escritor S3 V1 vigente y recupera eventos existentes por esa identidad; [`EvolutionEvent`](../../apps/ecomotor/models.py) conserva una causa `xp_event` y una etapa **V1**, sin snapshots completos de sus atributos. El [contrato A2](ecomotor-target-xp-v1.md) prevé que el *futuro* escritor objetivo separado cree un `XPEvent` por concesión nueva y evoluciones objetivo separadas. **Reutilizar `XPEvent` como causa conceptual no equivale a adaptar ahora S3 ni a introducir FKs nuevas**: el escritor objetivo y la comprobación transaccional de su causa no existen.

- La identidad compartida para búsqueda/replay sigue siendo `(profile, operation_key)`, **sin incluir catálogo, versión o escritor**. Un importe distinto con la misma identidad es conflicto; no hay nueva concesión ni doble escritor activo.
- La autenticación/autorización del llamador no la resuelve `grant_historical_xp`: S3 recibe un perfil persistido y valida estado e integridad. El acceso confiable corresponde al contexto servidor/Core; la exigencia conceptual de autorización previa del futuro servicio no se presenta como una comprobación Core ya implementada en S3.
- Antes de una concesión objetivo nueva habrá que demostrar clasificación/escritor autorizados, catálogo exacto autorizado, estado previo compatible y procedencia persistida. Una fila XP por sí sola no demuestra que sea V1 u objetivo; **ausencia de procedencia no clasifica automáticamente como V1**.
- Las concesiones objetivo y sus eventos causales deberán confirmarse o revertirse juntos con progreso y procedencia conforme a D-19; no se presume atomicidad entre BD distintas. S3 V1, `XPEvent` y `EvolutionEvent` históricos no se reescriben, reparan ni reinterpretan.

### 15.2. Procedencia por concesión, también con cero cruces

**Garantía aprobada TRACE-01A:** cada concesión nueva **objetivo** necesita una evidencia persistente, inequívoca e inmutable de la **versión exacta del catálogo utilizada**, aun cuando `crossed_epoch_codes` esté vacío. Un registro únicamente en cada evento de evolución es insuficiente para ese caso. Una versión textual sola, `frozen_at` o un resultado de `preview_target_xp` no constituyen prueba de uso autorizado; identidad de versión y procedencia deben ser comprobables en su contexto/alias confiable.

| Alternativa conceptual de representación | Ventaja y límite | Estado |
| --- | --- | --- |
| **A. Registro de procedencia separado por concesión objetivo**, enlazable inequívocamente con la causa XP y su perfil, con identidad exacta de versión. | Cubre concesiones sin evolución y permite comprobar el vínculo en replay sin tocar la semántica de los eventos V1. La relación física concreta, cardinalidad, unicidad, campos y forma de preservar evidencia aún no están definidos. | **Preferencia conceptual ya aprobada** en TRACE-01A; **diseño físico pendiente TRACE-01B**. |
| **B. Extender físicamente `XPEvent` con metadatos objetivo**. | Concentraría datos en el evento causal, pero alteraría una tabla e interfaz histórica compartida y requeriría preservar explícitamente la interpretación V1; no satisface por sí sola conservación/autorización. | **Alternativa de estudio, no aprobada**; no desplaza A ni autoriza modificar `XPEvent`. |
| **C. Registrar versión solo en eventos de evolución o deducirla del catálogo actual**. | Pierde concesiones sin cruces; una versión posterior podría cambiar el significado histórico y no cubre replay fiel. | **No satisface TRACE-01A**; no se propone como implementación. |

Cualquier forma física futura debe tratar de modo explícito el identificador de causa XP, perfil, alias, versión exacta y posibilidad de ausencia/supresión legítima de evidencia. **No se decide** FK, `OneToOne`, campo en `XPEvent`, tabla, `on_delete` o retención mediante este estudio.

### 15.3. Vínculos de evolución y posibles invariantes

Según A2-EVO-01, un cruce real de época objetivo produce **un evento objetivo por época cruzada**, nunca un `EvolutionEvent` V1. Cada registro conceptual debe permitir comprobar: (a) cuál fue el **mismo `XPEvent` causal** de la concesión; (b) que coincide su perfil destinatario; (c) cuál era la identidad exacta de catálogo y época utilizada al confirmar el cruce; (d) que el cruce pertenece al recorrido XP original y no se duplicó ni insertó retrospectivamente. Nivel 8 solo desbloquea elección; no añade octava época. [`TargetXPPlan.progression.crossed_epoch_codes`](../../apps/ecomotor/target_xp_plan.py) conserva los códigos calculados por A1.2, **no PK técnicas, causa XP persistida ni prueba de autorización**.

| Invariante funcional que habrá que preservar | Restricción/comprobación física **candidata**, no acordada |
| --- | --- |
| Una operación XP por `(profile, operation_key)` entre versiones; replay no vuelve a conceder. | `XPEvent` ya tiene `UNIQUE(profile, operation_key)`; el futuro escritor debe respetarla con comprobación causal en servicio. No añadir catálogo/escritor a la clave. |
| Una procedencia objetivo verificable por **cada** concesión nueva objetivo, incluso sin cruces, y sin dos evidencias incompatibles para una misma causa. | Evaluar una unicidad de causa en la futura representación separada; aún sin decidir cardinalidad, tipos, FK o comprobación transaccional. |
| Cada evento de época apunta a su causa XP, al **mismo perfil** y a la versión/época correspondientes; exactamente todos los cruces y ningún cruce repetido. | Evaluar unicidad de `(causa XP, época exacta)` y controles de correspondencia en servicio. No copiar automáticamente `UNIQUE(profile, stage)` de V1 ni confundir prevención de duplicados con validación causal o cobertura exacta de cruces. |
| XP, procedencia, progreso y eventos objetivo se confirman juntos sin eventos huérfanos ni reparaciones silenciosas. | Comprobaciones bajo una transacción D-19, unicidades/índices de apoyo y validación de referencias; el mecanismo concreto y tratamiento de borrados quedan abiertos. |

La BD por sí sola no acredita que las épocas registradas sean **exactamente** los cruces del plan autorizado, que un operador tenga permiso o que la referencia a la versión haya sido obtenida de fuente confiable. Estas son verificaciones del futuro servicio, y el contrato físico no está aprobado.

### 15.4. Evidencia histórica y replay

El [orden ya acordado en §6](#6-replay-entre-versiones--a3-replay-01) exige validar primero identidad/acceso e integridad, buscar `(profile, operation_key)` dentro de la frontera D-19 y **solo ante ausencia de operación** evaluar clasificación/escritor/catálogo para conceder. Un replay existente no recalcula desde el catálogo actual ni inserta XP, procedencia o evoluciones nuevas. No se puede prometer reconstrucción de datos que no se guardaron:

| Evidencia | Disponible hoy / requisito futuro |
| --- | --- |
| `XPEvent` V1 | Importe, XP anterior/posterior, perfil, operación, fecha e IDs causales que realmente existan. **No** niveles, épocas, cruces ni puntos históricos completos persistidos en ese evento; el replay S3 devuelve `None` en parte de estos campos. |
| `EvolutionEvent` V1 | Relación con `XPEvent` y `EvolutionStage` V1; no contiene los atributos originales de la etapa como snapshot inmutable. No atribuir catálogo objetivo o versión retroactiva. |
| Nueva operación objetivo | **Propuesta de evidencia mínima a resolver en TRACE-01B:** causa/perfil/clave/importe y XP previo/final; identidad exacta de versión y época previa/final; niveles previo/final; lista original ordenada de cruces; referencias a cada evento objetivo confirmado y su causa. Decidir cuáles se persistirán como snapshots propios, cuáles mediante relaciones inmutables y los límites de consulta y conservación. No reconstruir los que falten. |
| Replay con evidencia incoherente o legítimamente suprimida | Rechazo/control específico pendiente de Core y diseño de errores: nunca tratar como concesión nueva, reparar o fingir replay completo. No prometer conservación ilimitada. |

Para resultados nuevos objetivo no se conceden puntos por nivel (A2-RES-01); si se mantienen campos de compatibilidad del resultado, `stat_points_awarded=0` y `available_points_after=None` son los **valores acordados conceptualmente**, no datos V1 que deban reescribirse ni garantía de un snapshot físico aprobado.

### 15.5. Puertas y responsabilidades aún abiertas

- **Equipo 5 / 02C-2:** decidir TRACE-01B (representación física de procedencia y eventos, correspondencia XP/perfil/versión, cardinalidad/unicidades, snapshot y consulta conjunta V1/objetivo), tests transaccionales, interfaz del futuro escritor separado y compatibilidad histórica. Esta sección **no elige** modelos, migraciones, FKs ni políticas de backfill.
- **Core / A3.5:** identidad y atribución canónica, autenticación/autorización de escritura y replay, bajas, privacidad, retención, supresión y `on_delete`; no convertir propuestas internas o silencio en ratificación. **Equipo 5 / A3.6:** comprobar suficiencia y vigencia de evidencias sin tomar el diagnóstico como permiso de migración.
- **USE-01B y responsables de catálogo:** fuente y autorización funcional de valores/versiones, publicación/selección confiable y conexión con la operación XP real; congelación y auditoría técnicas no conceden autorización.
- **Consumidores / Henry / otros equipos:** compatibilidad de eventos, visualización, `EvolutionItem`, vestimentas y lectura histórica, sin modificar Duckies, Core, Bank ni Shop desde este incremento.
- **Integración:** transición con un único escritor XP activo, suspensión/drenaje y pruebas de idempotencia/concurrencia/rollback; S3 V1 sigue activo. El laboratorio y Rewards F2-A sobre S3 V1 conservan sus fronteras independientes.

### 15.6. ¿Añadir ahora un preparador puro INT-A2.1?

**Evaluación técnica, no decisión:** A1.2 (`calculate_target_progression`) y A2.1 (`plan_target_xp_grant`) ya proporcionan `crossed_epoch_codes`, orden y XP/niveles/épocas anterior y posterior. Un adaptador que solo copie esos cruces a otra tupla **no aporta una garantía independiente** y duplicaría superficie de tests. Un eventual preparador tendría valor únicamente si formalizara un contrato de *intenciones causales* o referencias históricas estables que A2.1 no conoce. Podría validar su estructura, pero no acreditar existencia, pertenencia o autorización de causas persistidas; esas comprobaciones seguirían en el futuro servicio y su diseño pendiente TRACE-01B. Presentar la propuesta pura como confirmación causal sería engañoso.

**Recomendación para decidir en 02C-2:** precisar primero el mínimo causal de TRACE-01B y los snapshots necesarios; posponer la aprobación/implementación del preparador hasta demostrar una responsabilidad distinta del plan existente. Alternativa abierta: un adaptador puro estrictamente no autoritativo, aprobado de forma separada, sin ORM y sin sustituir las comprobaciones del futuro escritor. **No iniciar ninguna opción por esta PR.**

**Tests futuros, no ejecutados aquí:** concesión objetivo sin cruce y con uno/varios cruces; identidad y conflicto de importe entre versiones; integridad de causa/perfil/versión; unicidades y replay sin efectos; snapshots históricos con catálogo cambiado; historia V1 parcial; fallo/rollback y concurrencia D-19; conservación y acceso según Core. Cada test de persistencia queda condicionado al diseño físico y sus acuerdos. Esta sección documenta garantías y alternativas, **no cierra TRACE-01B, USE-01B ni activa INT-A2**.
