# A2 · XP histórica objetivo · Arquitectura v1

## 1. Autoridad, procedencia y estado

A2-ARQ-01 y A2-VER/IDEM/EVO/RES/VAL/IMP-01 aprobadas **internamente en 02C**,
comunicadas por Jaime en el encargo documental. Registro del 20/10/2026 sobre
develop `6a7d1d7c8cede455e1aa9ecd2de66382bea3aba7`. No son requisitos técnicos
literales de DAR3 ni ratificación de Óscar/Core o de los demás propietarios.
DAR3 sigue como fuente funcional principal; se conserva su trazabilidad existente,
sin afirmar una nueva consulta directa de PDFs.

**Diseño objetivo, no servicio implementado ni activación autorizada.** A1.1
([catálogos](../../apps/ecomotor/target_catalog_validation.py), PR #52) y A1.2
([progresión](../../apps/ecomotor/target_progression.py), PR #53) sí están integrados.
S3 sigue vigente en [xp_service.py](../../apps/ecomotor/xp_service.py) y su
[contrato V1](ecomotor-xp-v1.md), sin cambios.
[Decisiones A2](../decisions.md#a2--arquitectura-de-xp-histórica-objetivo--20102026),
[estado arquitectónico](../architecture.md#10-a2--adaptación-de-xp-histórica-objetivo),
[pendientes A3](../pending-decisions.md#14-a2--dependencias-para-xp-histórica-objetivo)
y [contrato objetivo 02C](ecomotor-playable-options-target-v1.md).
A2-CT-01 es adaptación de XP sin puntos por nivel; A3-CT-01 sigue siendo
compatibilidad de catálogos, migración legacy y activación coordinada.

## 2. Servicio separado y alternativas

A2-ARQ-01 elige un servicio objetivo separado. El siguiente contraste explica
esa elección; no atribuye una deliberación o rechazo adicional al profesor:

| Alternativa de diseño | Consecuencia / justificación |
| --- | --- |
| Cambiar S3 en su sitio | Mezclaría nuevas concesiones sin puntos con el comportamiento V1 y sus consumidores antes de resolver compatibilidad. S3 no se modifica. |
| Añadir a S3 una versión elegida por el consumidor | No resuelve autorización ni clasificación persistente; texto de versión no es permiso para seleccionar escritor. No se introduce ese selector. |
| Servicio objetivo separado (aprobado) | Mantiene S3 V1 estable y permite revisar explícitamente escritor, resultados e historia bajo A3 antes de activar. Separación de implementación no habilita dos escritores contradictorios. |

S3 conserva `grant_historical_xp(profile, amount, operation_key)`, puntos de nivel,
validaciones y replay actuales. La futura firma A2 no se publica como disponible.
El servicio objetivo conservará XP histórica acumulativa, nivel, época, todos los
cruces y trazabilidad, **sin conceder puntos por nivel**. No configura ni selecciona
opciones jugables, ni redistribuye estadísticas.

## 3. Versión confiable y escritor único · A2-VER-01

El servidor decide de forma confiable qué versión puede conceder XP a un perfil.
Un catalog_version textual, un TargetCatalogSnapshot válido o indicadores de
elección de A1.2 no autorizan producción ni clasifican al jugador. A1.1 conserva
stat_points_awarded en sus definiciones y admite valores no nulos; A1.2 no los
utiliza. Validación técnica no es activación funcional.

A3 debe resolver clasificación persistente de perfiles, configuración autorizada,
compatibilidad de catálogos y frontera coordinada de activación/rutas de escritura.
No inferir versión por nivel, época, forma de la clave o ausencia de estado jugable.
No escoger automáticamente la última versión ni activar por recibir un snapshot.
Un perfil no debe recibir escrituras contradictorias de S3 y A2; su selección de
escritor se controla en servidor y se verifica bajo la frontera de escritura.
No se fija aquí el modelo físico o mecanismo de esa clasificación/activación.

## 4. Identidad y replay entre versiones · A2-IDEM-01

Mantener **(profile, operation_key)**. No añadir versión, prefijo de versión o
catálogo a la identidad para volver a conceder una misma operación. Una clave
existente se recupera sin reevaluar catálogos actuales ni volver a aplicar efectos;
mismo perfil/clave con importe incompatible es conflicto, aunque cambie versión.
Validar identidad, acceso e integridad del registro recuperado; no presentar un
fallo de BD o historial corrupto como replay correcto.

XPEvent actual conserva importe, xp_before/xp_after, clave, perfil y fecha; **no
registra versión, nivel o época como snapshots**. EvolutionEvent referencia
EvolutionStage, pero no guarda sus atributos históricos originales (código,
ordinal o umbral). No deducir esos valores de la fila de catálogo actual ni
inventar procedencia V1/objetivo a partir de ellos.

El replay conserva los datos realmente persistidos, incluidos IDs causales. No
prometer niveles, épocas, cruces o puntos históricos completos si no están guardados.
Los resultados V1 no se transforman en resultados objetivo ni se fuerzan a cero
sus puntos antiguos. Si diferenciar procedencia requiere información no persistida,
A3 debe establecer la política de compatibilidad: no resolverla por inferencia,
crear eventos retroactivos o alterar la identidad idempotente.

## 5. Progresión y eventos causales · A2-EVO-01

Para una concesión nueva autorizada, utilizar snapshot A1.1 y cálculo A1.2 de XP
anterior/posterior, nivel, época y todas las transiciones cruzadas. Comprobar que
el estado anterior calculado corresponde al perfil según su clasificación activa.
No invocar el cálculo V1 para obtener puntos ni sumar los puntos de sus definiciones.

La futura escritura crea exactamente un XPEvent para la concesión y un evento
de evolución objetivo por cada época realmente cruzada, **separado de la tabla
EvolutionEvent V1**, con el mismo perfil y la causa XP verificable correspondiente.
Esta precisión posterior de
[A3-CAT-EVENT-01](ecomotor-transition-target-v1.md#a3-cat-event-01--separación-de-eventos-objetivo)
conserva la obligación conceptual A2-EVO-01 de registrar todos los cruces, sin
imponer el modelo V1 al objetivo. Identidad histórica de época/versiones y catálogo
objetivo separado se preservan; relaciones físicas con XPEvent/perfil/catálogo
siguen pendientes. Ninguna evolución inicial ficticia, transiciones omitidas,
duplicadas o de otra causa. Nivel 8 desbloquea elección, **no crea octava época**;
Siglo XX sigue siendo última época histórica aunque aumente el nivel.

Validar correspondencia estable de códigos/filas y ausencia de transiciones ya
registradas incompatibles; rechazar incoherencia sin reparar. Replay de concesión
existente no añade XP ni eventos de evolución. A3 debe asegurar identidad histórica
de catálogos/migración: no renombrar etapas referenciadas para reinterpretar
EvolutionEvent V1 ni trasladar automáticamente su unicidad perfil/etapa al esquema
objetivo pendiente. Se mantiene conceptualmente la prevención de duplicados.

## 6. Resultados sin puntos por nivel · A2-RES-01

Una concesión objetivo nueva no modifica stats, presupuesto ni puntos disponibles.
Si se mantienen campos de compatibilidad del resultado, devolver
**stat_points_awarded=0 y available_points_after=None** para esa concesión nueva:
None no afirma que el saldo existente sea cero ni debe consultarse para simular
un saldo de puntos de ascenso. A1.2 ya devuelve progreso sin campos de puntos.

Estos valores no reescriben resultados históricos V1. Una concesión nueva de S3 V1 mantiene su
semántica vigente de puntos concedidos/saldo; su replay sigue devolviendo None
en campos no almacenados. A3 debe cerrar la representación y compatibilidad de
resultados entre versiones, sin prometer reconstrucción histórica completa.
No se define aquí dataclass final, endpoint o nombres de excepciones disponibles.

## 7. Validaciones y perfiles heredados · A2-VAL-01

Para concesiones nuevas, validar perfil persistido/existente y alias, XP e importe
técnicamente válidos, nivel y etapa, estado de estadísticas **según clasificación
del perfil**, catálogos/versionado autorizados, límites técnicos representables y
causalidad de eventos. Rechazar incoherencias sin normalizar ni reparar datos legacy.
El replay conserva las validaciones estructurales e históricas necesarias de §8,
sin exigir clasificación o elegibilidad de un escritor de concesiones nuevas.

No copiar a ciegas la exigencia S3 de CharacterStats global a cualquier futuro
perfil objetivo ni dispensar validación por ausencia de esa fila. A3 debe definir
clasificación e invariantes aplicables antes de la escritura; ausencia de nuevo
estado no significa perfil nuevo. No inicializar automáticamente, reasignar stats,
reiniciar progresos, recalcular niveles/XP ni borrar historiales.

Distinguir errores de entrada/perfil, versión no autorizada/clasificación ausente,
configuración/catálogos, estado o causalidad incompatibles, conflicto idempotente,
capacidad técnica y BD. Sus firmas/representaciones se diseñarán posteriormente;
ningún error autoriza concesión parcial o reparación silenciosa.

## 8. Atomicidad y concurrencia · D-19

Orden conceptual de recuperación y futura escritura:

1. Validar inicialmente identidad, autorización, importe y clave.
2. Abrir transaction.atomic en el alias común conforme a D-19, antes de lecturas
   mutables, y realizar las validaciones estructurales necesarias.
3. Buscar XPEvent por (profile, operation_key).
4. Si existe, comprobar importe, snapshots y causalidad y devolver el resultado
   histórico disponible, sin exigir clasificación, elegibilidad del escritor
   actual o catálogos de concesiones nuevas. Un replay V1 sigue siendo recuperable
   tras un cambio de versión, con las limitaciones históricas descritas en §4.
5. Si no existe, resolver la clasificación persistente y el escritor autorizado
   conforme a A3.
6. Solo entonces validar catálogos/progreso y confirmar conjuntamente los efectos
   de la concesión nueva sobre perfil, XPEvent y eventos de evolución objetivo
   separados de EvolutionEvent V1, conforme a §5. Sus relaciones físicas no se
   aprueban mediante este orden conceptual.

La autorización inicial sigue siendo obligatoria también para el replay; este
orden no crea una ruta alternativa sin autorización, no modifica S3 V1 ni
implementa un dispatcher o resuelve el esquema pendiente de A3.

SQLite BEGIN IMMEDIATE, timeout cinco segundos, unicidad persistente perfil/clave
y prevención de evoluciones duplicadas como defensas complementarias; las claves
y restricciones físicas objetivo siguen pendientes, sin copiar automáticamente
UNIQUE(profile, stage) de EvolutionEvent V1. No depender de select_for_update
como bloqueo de fila. Todo confirma o revierte conjuntamente, sin dobles premios
por concurrencia entre rutas/versiones. Timeout/fallo produce rollback; retry
explícito en nueva transacción con la misma identidad. Sin I/O externo o retries
automáticos dentro de transacción, ni atomicidad prometida entre BD independientes.

## 9. Dependencias obligatorias de A3

Antes de persistir/activar A2, deben cerrarse clasificación persistente nuevos/
heredados, política de migración sin reinterpretación histórica, compatibilidad de
catálogos/resultados y activación coordinada del escritor. Identificar datos reales
antes de migrar; no fijar esa política mediante ejemplos o un nombre de versión.
Conservación, anonimización/eliminación y on_delete siguen con Core/P5, sin
inferencias ni nuevas relaciones/migraciones aprobadas por este documento.
Configuración técnica válida requiere además autorización funcional/instalación
real; no se fijan cantidades XP oficiales. El planificador puro no levanta esos bloqueos.

## 10. Primer incremento puro y pruebas previstas · A2-IMP-01

Primer incremento implementable: planificador puro sobre A1.1/A1.2 que prepare
la progresión de una concesión objetivo sin escribir ni confirmar efectos.
**No se crea target_xp_plan.py en esta PR.** Tipos/firmas exactos se concretarán
en su incremento, sin leer ORM, seleccionar versiones automáticamente o activar
concesiones. Puede probarse con entradas explícitas y datos sintéticos antes de A3;
no sustituye validaciones persistentes, autorización o idempotencia de servicio.

Pruebas previstas, no añadidas ni ejecutadas aquí:

- XP/importe/perfil conceptual de entrada inválidos y configuración incompatible,
  según alcance del planificador; inmutabilidad de entradas/resultados.
- Umbrales exactos, varias épocas/niveles en una concesión, nivel 8 sin época
  extra y continuidad posterior; puntos heredados no nulos ignorados por objetivo.
- Plan sin puntos, sin escrituras, activación ni selección automática de versión.
- Para futuro servicio persistente: replay de claves previas entre versiones sin
  catálogo actual, conflicto de importe, limitaciones históricas, causalidad,
  rechazo de legacy incoherente, rollback y concurrencia SQLite file-backed D-19.

Estos últimos casos requieren el diseño A3 y no se atribuyen a pruebas puras ya
implementadas. La PR presente solo documenta; no ejecuta tests Django.

## 11. Fronteras

No cambia S3, A1.1/A1.2, modelos, tests, migraciones, configuración o contratos V1.
No implementa Rewards, XP de dominio, rangos S13-A2, puntos directos, inventario,
vestimenta/equipamiento, selección jugable, API o autenticación nueva. Rewards F2-A
conserva DOC-6 y sus bloqueos; el consumo futuro de A2 requiere coordinación,
sin aprobar adaptadores o alterar snapshots del contrato Rewards por inferencia.
A2-CT-01 sigue siendo XP histórica; A3-CT-01 conserva compatibilidad/migración.

Referencia posterior: [A3 · Compatibilidad histórica y activación condicionada](ecomotor-transition-target-v1.md)
desarrolla las dependencias aquí registradas; el estado vigente de A2.1 puro está
en [arquitectura A3](../architecture.md#11-a3--compatibilidad-histórica-y-activación-coordinada).
Las decisiones A2 y el corte histórico de este contrato se conservan.
