# S2-A · Inicialización local de Ecomotor v1

## Estado y autoridad

Decisión interna aprobada por Jaime/Parte A, apoyada en V2-A13, D-19 y R-12.
No es un nuevo requisito oficial de DAR3 ni aprobación global de Óscar/Core.
No redefine User, autenticación, conservación ni contratos Rewards/A/B/C.

## Entrada, salida y errores

`ensure_ecomotor_initialized(user)` recibe un objeto del modelo User configurado,
persistido y existente. Opera en el alias donde está guardado ese User, con perfil,
estadísticas y catálogos en la misma BD. No acepta atributos desde el consumidor,
no crea User ni realiza autenticación/autorización.

Devuelve `InitializationResult(profile_id, character_stats_id, created)`, dataclass
inmutable. Excepciones diferenciadas del módulo initialization:

- `InvalidUserError`: objeto incorrecto, no persistido o ya inexistente.
- `InvalidInitializationConfigError`: configuración ausente/inválida o catálogos
  incompletos/incoherentes; encadena la causa de validación cuando procede.
- `InconsistentInitializationStateError`: perfil parcial o estructura inválida.
- `InitializationDatabaseError`: error real de BD, incluido timeout de lock;
  encadena la causa y sale de atomic() con rollback, nunca devuelve éxito aparente.

Un consumidor puede reintentar tras un error de BD en una nueva transacción,
recuperando por User la pareja persistida; no hay bucle de retry automático.

## Configuración y primera creación

initialization_config proporciona una dataclass frozen con atk, def_stat, log_stat,
spe, vel, int_stat y ordered_stage_codes como tupla. La configuración interna
INITIAL_CONFIGURATION es None inicialmente: el uso real falla de forma controlada
hasta que se incorporen valores autorizados por una revisión de configuración.
No hay seis valores de 5, vectores oficiales supuestos ni códigos inventados.
Tests sustituyen temporalmente esa referencia interna con fixtures explícitos.
Los seis atributos son enteros, excluyendo bool; solo se limita su representación
al rango técnico del IntegerField del backend, sin rangos funcionales nuevos.
Los códigos son siete cadenas únicas no vacías de hasta 32 caracteres, ordenadas
por Prehistoria, Griega, Romana, Renacentista, Contemporánea, Siglo XX y Actual.
La correspondencia viene de configuración, nunca se deriva del catálogo validado.

Dentro de una sola transaction.atomic(), antes de leer estado mutable:

1. Verificar existencia del User y buscar su perfil.
2. Si es una creación nueva, validar configuración y catálogos completos con
   validate_level_catalog y validate_evolution_stage_catalog sobre filas del alias.
3. Crear UserProfileEcomotor con XP histórica 0, nivel 1, código de la etapa
   ordinal 1 (Prehistoria validada), active_specialization_code=None.
4. Crear CharacterStats con los seis enteros confiables y available_points igual
   a LevelThreshold.stat_points_awarded del nivel 1; devolver created=True.

No crear XPEvent, EvolutionEvent, UserSpecializationProgress, RewardEvent,
Wallet, Ducky, inventario ni recompensas. Sin signals, seeds ni migraciones.

## Reintentos y estados existentes

Si hay perfil y CharacterStats estructuralmente válidos, devolver sus mismos IDs
y created=False sin escritura. Validar campos conforme a su estructura de modelo,
sin recalcular XP/nivel/etapa, exigir catálogos/configuración inicial actuales ni
reinterpretar referencias lógicas históricas. Conservar especialización, seis stats
y puntos aunque hayan cambiado. No reconceder puntos iniciales.
Un perfil sin estadísticas, campos legacy ausentes o valores estructuralmente
inválidos provocan InconsistentInitializationStateError; no completar ni reparar.
M-01 sigue vigente; la conservación/migración legacy necesita acuerdo de Core.

## Transacciones y límites

D-19: SQLite transaction_mode=IMMEDIATE, timeout=5. BEGIN IMMEDIATE es la garantía
de serialización de escritores de toda la BD; no hay bloqueo por fila real de
select_for_update(). atomic() precede a lecturas de User/perfil/configuración de
catálogo; OneToOne y constraints completan la integridad. Transacciones cortas,
sin I/O remoto ni ATOMIC_REQUESTS. Un fallo revierte perfil y stats conjuntamente.
Dos llamadas concurrentes al mismo User deben dejar una única pareja; la segunda
recupera el resultado o comunica error de BD con rollback si no obtiene el lock.
Las pruebas deben usar SQLite file-backed y conexiones independientes, además de
TransactionTestCase. No prometen garantías multidominio, entre aliases o servicios.

S2-A no concede XP, evoluciona ni selecciona especialización; S3/Rewards, identidad
y provisionamiento global de Core, conservación y contratos compartidos siguen
pendientes. La ausencia de configuración autorizada bloquea creación real, no la
recuperación idempotente de una pareja completa ya existente.
