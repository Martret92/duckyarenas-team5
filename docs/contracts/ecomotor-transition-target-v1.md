# A3 · Compatibilidad histórica y activación del Ecomotor · Contrato objetivo v1

## 1. Autoridad, alcance y estado

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
S3 V1 sigue como escritor vigente. **A3, su registro persistente, catálogo físico
objetivo, migración y punto de entrada futuro no están implementados.**

## 2. Clasificación persistente · A3-CLAS-01

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

Conservar identidades y referencias EvolutionStage V1. Dirección aprobada:
**catálogo objetivo separado, versionado e inmutable una vez utilizado**.
Su esquema físico y la relación entre versiones y filas no están aprobados.
TargetCatalogSnapshot A1.1 es un valor puro validado, no ese catálogo persistente
ni permiso de publicación/producción.

Se distinguen nueve épocas DAR3 originales, siete etapas V1 terminadas en Actual
y siete épocas históricas objetivo: Prehistórico, Griego, Romano, Medieval,
Renacentista, Revolución Industrial y Siglo XX. Nivel 8 abre elección, no época
adicional; niveles posteriores continúan. No renombrar filas V1 para reinterpretar
EvolutionEvent ni cambiar sus atributos históricos por inferencia.

**Bloqueo físico obligatorio:** EvolutionEvent.stage hoy refiere a EvolutionStage;
debe diseñarse cómo identificar nuevas épocas y conservar causalidad/referencias
sin mezclar identidades históricas. PlayableOption histórico fue diseñado en 02C
con relación conceptual EvolutionStage; su adaptación al catálogo separado requiere
validación adicional. No se elige una FK alternativa, tabla, relación polimórfica,
reescritura de eventos o migración para resolverlo en esta documentación.

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
