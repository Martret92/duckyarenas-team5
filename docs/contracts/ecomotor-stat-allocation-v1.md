# S7-A · Asignación transaccional de puntos V1

Decisión interna aprobada por Jaime/Parte A. DAR3/ERD aportan el contexto de
progresión, estadísticas y puntos; las reglas técnicas siguientes no se atribuyen
al profesor, Core ni Rewards. Valores oficiales y conservación global pendientes.

## Servicio y elegibilidad

`allocate_stat_points(profile, attribute, points, operation_key)` recibe perfil
persistido existente, con CharacterStats, usando su alias. No crea ni repara.
attribute: exactamente atk, def_stat, log_stat, spe, vel o int_stat. points: entero
positivo sin bool/conversión, representable. Clave str de 1–255 sin normalización.
Nueva operación: correspondencia confiable de siete códigos desde
INITIAL_CONFIGURATION, validación del catálogo EvolutionStage y resolve_stage de
S1 con StageDefinition. Etapa derivada de XP debe coincidir con la persistida y
con ordinal 7 (Actual). Sin códigos literales, catálogo de niveles ni validación
de stats iniciales S2-A. Contradicción es inconsistencia, no reparación.
Saldo suficiente: cada punto gasta una unidad y aumenta una unidad del único
atributo elegido. Sin máximos funcionales, redistribuciones, devoluciones o reset.
No modifica perfil, XP/nivel/etapa/especialización, otros atributos ni XP de dominio.

## Evento, resultado y errores

StatAllocationEvent: BigAutoField; profile FK CASCADE provisional; operation_key
CharField(255), attribute CharField(16), points_spent/increase_applied y snapshots
available_points_before/after PositiveIntegerField; attribute_before/after
IntegerField con signo; stage_code_at_allocation CharField(32), created_at automático.
Sin FK al catálogo: código histórico persistido, no reinterpretado con filas actuales.
BD: UNIQUE(profile, operation_key), clave/código no vacíos, atributo permitido,
gasto/incremento positivos, increase_applied = points_spent,
available_points_before = available_points_after + points_spent,
attribute_after = attribute_before + increase_applied y saldo no negativo por tipos.
Servicio valida tipos/rangos estrictos sin conversiones legacy y todos los snapshots.
Sin eventos ficticios/retroactivos ni promesa de inmutabilidad universal del ORM.

StatAllocationResult frozen: replayed, profile_id, allocation_event_id, operation_key,
attribute, points_spent, increase_applied, available_points_before/after,
attribute_before/after y stage_code_at_allocation. En replay conserva el significado
histórico original, no el estado actual; todos estos datos están persistidos.

Excepciones públicas: InvalidAllocationProfileError, InvalidAttributeError,
InvalidPointsError, InvalidAllocationKeyError, InvalidAllocationConfigurationError,
IneligibleStageError, InsufficientPointsError, AllocationConflictError,
InconsistentAllocationStateError, AllocationOverflowError, AllocationDatabaseError.
Cantidad de entrada fuera de rango: InvalidPointsError; snapshot/resultado no
representable: AllocationOverflowError. BD conserva causa y revierte; no oculta
errores arbitrarios de programación ni convierte errores en replay supuesto.

## Idempotencia, transacción y conservación

Validar entradas; atomic(using=alias) antes de leer estado mutable; recargar perfil,
stats y evento previo. Validar evento antes de exigir configuración/elegibilidad
nueva: propietario/clave/PK/fecha, tipos/rangos, atributo permitido, cantidades
positivas, igualdades aritméticas y código histórico estructuralmente válido.
Mismos parámetros: replay=True sin UPDATE/evento nuevo. Parámetros distintos:
conflicto. Corrupción: inconsistencia sin reparación. No compara snapshots con
saldo actual ni código histórico con configuración posterior. Funciona tras otras
asignaciones/S3 o retirada de configuración; coherencia no demuestra autorización.
Unicidad local en StatAllocationEvent no deduplica XPEvent ni Rewards global.

SQLite D-19: BEGIN IMMEDIATE serializa escritores de toda la BD, timeout 5s,
constraints persistentes y transacciones cortas sin I/O externo. Sin dependencia
de select_for_update. Evento y stats se confirman o revierten juntos. S3/S7-A
evitan pérdidas de actualización; precondiciones se evalúan al adquirir turno.
Timeout/fallo: rollback completo; retry del consumidor en nueva transacción con
misma clave, sin bucles automáticos.
0005 aditiva desde 0004, solo tabla/constraints; sin backfill. Como 0002–0004,
RunPython sin reverse_code protege reversión incluso con tabla vacía.

## Admin, compatibilidad y límites

ReadOnlySuperuserAdmin: solo superusuario activo consulta; búsqueda perfil/clave/
atributo, filtros y orden útiles; no altas/edición/borrado/acciones ni POST de escritura.
S4-A/S5-A reflejan stats confirmadas sin cambiar historial XP; visualización de
asignaciones fuera de alcance. S1–S6-A intactos. CASCADE provisional, conservación
Core/legacy, configuración oficial, V2-A28 y contratos compartidos/Rewards siguen
pendientes. No autorización global, avatar, economía ni especializaciones nuevas.
