# S4-A · Consultas locales de progreso e historial V1

## Estado y alcance

Decisión interna aprobada por Jaime/Parte A sobre S1, S2-A y S3 ya persistidos.
Solo servicios Python de lectura: no HTTP, autenticación, inicialización, premios,
reparación ni escrituras. Las convenciones siguientes son técnicas de esta V1,
no números oficiales de DAR3 ni aprobación global de Óscar/Core/Rewards.

## Entrada y errores compartidos

Ambos servicios reciben UserProfileEcomotor persistido y existente, con CharacterStats
asociado. Recargan el estado desde su alias de BD; no confían en campos cacheados.
Validan estructura sin conversiones silenciosas de datos legacy ni consultas a User,
Bank u otros módulos. No exigen catálogos para leer estado básico o historial.

- `InvalidQueryProfileError`: perfil incorrecto/no persistido/inexistente.
- `InconsistentQueryStateError`: perfil parcial, campos estructurales inválidos o
  historial inválido/causalmente incompatible detectado.
- `InvalidHistoryParametersError`: limit o before_id fuera del contrato.
- `ProgressQueryDatabaseError`: fallo real de BD, con causa preservada.

Solo errores de validación esperados de configuración/catálogos se traducen a
UNAVAILABLE. Fallos de BD y errores de programación no se ocultan como objetivos
no disponibles. Los resultados son dataclasses frozen con colecciones en tuplas.

## get_progress_overview(profile)

Devuelve ProgressOverview: profile_id, historical_xp_total, current_level,
current_stage_code, atk, def_stat, log_stat, spe, vel, int_stat, available_points,
next_level y next_stage. Los valores básicos proceden de perfil/stats persistidos;
no son estadísticas efectivas ni una reinterpretación del progreso.

Ambos objetivos usan GoalProjection y GoalState:

| Estado | Significado y datos |
| --- | --- |
| CALCULABLE | Próximo nivel o código de etapa conocido, minimum_xp y remaining_xp = minimum_xp - XP actual. level o stage_code identifica el objetivo según su tipo. |
| COMPLETED | Último elemento del catálogo completo validado alcanzado coherentemente. Sin objetivo posterior ni umbrales inventados; no significa fin inmutable del juego. |
| UNAVAILABLE | Configuración ausente/inválida, catálogo inválido o estado desalineado. Datos de objetivo None y reason técnico controlado, sin aproximaciones. |

Validar LevelThreshold completo con validate_level_catalog y comprobar el nivel
actual mediante resolve_level de S1. Buscar el primer nivel posterior del catálogo;
si no existe, COMPLETED. No asumir incrementos constantes.

Para etapas, obtener exclusivamente
initialization_config.INITIAL_CONFIGURATION.ordered_stage_codes, sin validar los
seis atributos iniciales. No derivar códigos de filas. Validar siete etapas con
validate_evolution_stage_catalog y comprobar el estado con resolve_stage de S1.
Buscar la siguiente por ordinal, o COMPLETED al alcanzar la última coherentemente.
La correspondencia funcional es interna confiable y todavía no contiene valores
oficiales de producción. Nivel válido puede proyectarse sin ella; stage UNAVAILABLE
no oculta datos básicos ni el resultado independiente de nivel, y viceversa.

Motivos técnicos: INVALID_LEVEL_CATALOG, INVALID_STAGE_CATALOG,
STAGE_CONFIGURATION_UNAVAILABLE, INVALID_STAGE_CONFIGURATION,
LEVEL_STATE_MISMATCH y STAGE_STATE_MISMATCH. No reparan ni descienden progreso.

## list_progress_history(profile, *, limit=50, before_id=None)

limit entero positivo sin bool, máximo 100; before_id opcional entero positivo
sin bool. 50/100 son límites técnicos, no parámetros de DAR3. XPEvent del perfil
ordenados por -pk, filtrados por pk < before_id, sin offsets. Recuperar limit+1
para has_more y devolver como máximo limit entradas. next_before_id es el ID de
la última entrada devuelta solo cuando hay más; en otro caso None.

ProgressHistoryPage contiene entries (tupla), has_more y next_before_id.
Cada XPHistoryEntry contiene únicamente id, profile_id, operation_key, amount,
xp_before, xp_after, created_at y evolutions (tupla de EvolutionHistoryEntry).
Cada evolución expone id, xp_event_id causal, stage_id y created_at, por PK ascendente.
Se recuperan las evoluciones de la página en una consulta agrupada, sin N+1.

No se consultan catálogos ni configuración para reconstruir historia. No se
devuelven niveles anteriores/finales, puntos, saldo histórico, códigos, ordinales
o nombres históricos: no están congelados en XPEvent/EvolutionEvent. stage_id es
identidad persistida; cambios posteriores de la etapa no inventan un snapshot.
Los snapshots XP originales se devuelven sin recalcular ni confundir con total actual.

Los XPEvent se filtran por el perfil. Validar causalidad en evoluciones de la página;
además detectar por existencia evoluciones declaradas del perfil con causa de otro
perfil. Solo se comparan identificadores de la relación incompatible; nunca se
devuelven datos del otro usuario ni se corrige el historial. Campos históricos
estructuralmente inválidos se rechazan sin normalización.

## Consistencia y límites

No hay transaction.atomic(), BEGIN IMMEDIATE, select_for_update(), save, create,
update, delete ni equivalentes en estos servicios. Distintas lecturas pueden ver
estados confirmados en momentos distintos bajo concurrencia; V1 no garantiza un
snapshot transaccional único de perfil/stats/catálogos/historial. La paginación por
cursor tiene orden estable por ID, sin prometer un historial congelado entre páginas.
No se añade módulo de tests concurrentes porque no se amplía esa garantía.

No modifica S1/S2-A/S3, modelos, migraciones o settings. No sustituye vistas
autenticadas, interfaz o CRUD pendientes de PR07. Conservación/legacy, autoridad
Core, configuración oficial y contratos compartidos permanecen pendientes.
