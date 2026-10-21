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
