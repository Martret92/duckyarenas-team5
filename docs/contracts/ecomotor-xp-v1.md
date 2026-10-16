# S3 V1 · Concesión transaccional de XP histórica

## Autoridad y precondición

Decisión interna aprobada por Jaime/Parte A bajo V2-A12/A22/A23, D-19 y
[S2-A](ecomotor-initialization-v1.md). No es requisito específico nuevo de DAR3
ni aprobación global de Óscar/Core/Rewards. Requiere UserProfileEcomotor persistido,
existente y con CharacterStats estructuralmente válidos, en la misma BD/alias.
No inicializa, llama a S2-A, repara ni normaliza progreso. No autentica emisores.

## Interfaz y resultado

`grant_historical_xp(profile, amount, operation_key)` recibe el perfil, un entero
positivo (sin bool ni conversiones implícitas) y una cadena no vacía de hasta
255 caracteres. Los espacios son caracteres: V1 no añade normalización ni trim
de la clave y mantiene su identidad exacta, conforme al campo persistente.

Devuelve `XPGrantResult`, dataclass frozen; colecciones como tuplas:

| Campo | Concesión nueva | Replay histórico |
| --- | --- | --- |
| replayed | False | True |
| profile_id, xp_event_id, amount, operation_key | Identidad persistida de la operación | Mismos datos del XPEvent recuperado |
| xp_before, xp_after | Snapshots de la concesión | Snapshots originales; no total actual del perfil |
| evolution_event_ids, evolved_stage_ids | Eventos/etapas realmente registrados por esta causa, en orden de inserción funcional | IDs persistidos de esa causa, ordenados por PK de EvolutionEvent; sin inferir ordinales históricos de catálogos actuales |
| level_before, level_after, stage_before_code, stage_after_code | Estados calculados por S1 para esta operación | None: no están guardados como snapshots en XPEvent |
| crossed_levels, crossed_stage_codes | Niveles y códigos nuevos calculados por S1 | None: no se reconstruyen con configuración actual |
| stat_points_awarded, available_points_after | Incremento S1 y saldo tras esta operación | None: no están almacenados en el historial; saldo actual puede incluir usos/concesiones posteriores |

El replay no devuelve un objeto de progreso recalculado. La FK de EvolutionEvent
conserva identidad de etapa, no un snapshot de su código, ordinal o umbral; por eso
no se presentan los valores actuales de esa fila como datos históricos originales.

## Entradas, errores y configuración

Excepciones diferenciadas de xp_service:

- `InvalidProfileError`: instancia incorrecta/no persistida/inexistente.
- `InvalidXPAmountError`: cantidad no entera positiva o bool.
- `InvalidOperationKeyError`: clave no string, vacía o demasiado larga.
- `IdempotencyConflictError`: misma pareja perfil/clave con cantidad distinta.
- `InvalidXPConfigurationError`: correspondencia ausente/inválida o catálogos inválidos.
- `InconsistentProgressError`: estructura parcial/inválida, nivel/etapa actual no
  coherentes con XP para una concesión nueva, o historial causal incompatible detectado.
- `XPOverflowError`: XP, importe, nivel o saldo de puntos fuera del rango técnico
  representable de sus campos según el backend; no es un límite de juego.
- `XPDatabaseError`: fallo real de BD, incluido timeout; conserva causa y rollback.

Para una clave nueva, leer LevelThreshold/EvolutionStage completos del alias del
perfil y validarlos con los validadores existentes. Obtener únicamente
initialization_config.INITIAL_CONFIGURATION.ordered_stage_codes, sin validar
los seis atributos iniciales de S2-A. Deben ser siete códigos únicos no vacíos de
hasta 32 caracteres en correspondencia funcional explícita; no derivarlos de filas.
La configuración real sigue ausente; fixtures no constituyen parámetros oficiales.

## Concesión nueva

En atomic() antes de cualquier lectura mutable: recargar perfil y stats, buscar
XPEvent por perfil/clave y comprobar integridad causal. Para clave nueva, validar
configuración/catálogos y transformar filas en LevelDefinition/StageDefinition.
Comprobar límites de amount y xp_before+amount; llamar exclusivamente a
calculate_progression() de S1, que proporciona estados anterior/final y transiciones.
Comparar su estado anterior con nivel/etapa persistidos, sin reconciliación automática.
Comprobar límites del nuevo nivel y available_points+total_stat_points_awarded.

Crear exactamente un XPEvent con snapshots coherentes y un EvolutionEvent por
cada etapa nueva de S1, con el mismo perfil y XPEvent causal. No crear evolución
inicial. Rechazar etapas cruzadas ya registradas en el perfil como incoherencia,
sin modificar registros anteriores. Actualizar XP/nivel/etapa y sumar puntos al
saldo existente; no exigir suma histórica, pues pueden haberse gastado puntos.
No cambiar seis atributos base, especialización activa ni progresos de dominio.

## Replay y coherencia

Misma clave y amount devuelve el resultado histórico sin escribir, incluso tras
otras concesiones o cambios/ausencia de configuración y catálogos. Cantidad diferente
es conflicto; no se convierte IntegrityError en replay supuesto. Validar estructura
actual de perfil/stats, snapshots del evento recuperado y correspondencia causal
de perfiles en las evoluciones relevantes; un evento no puede tener xp_after mayor
que la XP histórica actual no decreciente. No exigir coincidencia con catálogos
vigentes para recuperar historia persistida ni reconstruir lo no almacenado.

V2-A28 no queda resuelta: cambios administrativos que desalineen estado actual y
catálogos impiden nuevas concesiones hasta revisión; no recalcular pasado ni puntos.
No imponer una historia completa ficticia ni crear eventos retroactivos.

## Atomicidad, concurrencia y límites de integración

D-19: transaction.atomic(), SQLite BEGIN IMMEDIATE, timeout 5; escritor único de
toda la BD, sin bloqueo de fila efectivo por select_for_update(). Unicidad
XPEvent(profile, operation_key) y evolución perfil/etapa protegen persistencia.
Todas las escrituras se confirman o revierten juntas; transacciones cortas, sin I/O
externo ni ATOMIC_REQUESTS. No hay retry automático: tras error de BD, nueva
transacción y misma clave. Mismo alias es condición; no se promete atomicidad global.

Pruebas reales file-backed con TransactionTestCase y conexiones independientes:
misma clave/cantidad, clave igual/cantidad distinta, claves distintas con múltiples
transiciones, y timeout/retry. S3 no concede monedas/objetos, inventario, Rewards,
puntos directos ni APIs; no modifica User/Bank. La idempotencia local no sustituye
la de Rewards. Core, conservación legacy, autorización, configuración oficial y
contratos compartidos siguen pendientes. Sin migraciones ni nuevas tablas.
