# S11-A · Selección inicial de especialización V1

## Procedencia y estado

Arquitectura general y precisiones S11-A-01/S11-A-02 aprobadas internamente por
Jaime/Parte A en «02B · Arquitectura y repositorio · Continuación». Implementación
sobre develop `37cbbd748dfb8bff75aa0bf0d264cefb51c8af95`, en rama para revisión.
S11-A solo se considerará terminado después de revisar y fusionar su PR.
No constituye aprobación de Óscar/Core, nuevo requisito literal de DAR3 ni cierre
de P7. V2-A19 contempla selección en Actual; V2-A24 define el catálogo estable y
V2-A25 el progreso mínimo. Este servicio implementa únicamente la primera elección.

> S11-A-01: En una primera elección, la elegibilidad depende de la configuración confiable de etapas, EvolutionStage y coherencia XP histórica–etapa, siguiendo S7-A. El nivel persistido se valida estructuralmente, pero no se exige LevelThreshold ni coherencia calculada XP–nivel. Esta elección es una decisión técnica local, no una regla atribuida a DAR3.

> S11-A-02: Una repetición del mismo código con perfil, CharacterStats, especialización y progreso persistidos coherentes devuelve la selección existente sin escrituras y sin reevaluar catálogos, configuración o elegibilidad actuales. Los estados inconsistentes se rechazan sin reparación. Es idempotencia basada en estado, no un historial de selección.

## Interfaz pública

`select_initial_specialization(profile, specialization_code)` en specialization_service.py.

- Perfil: UserProfileEcomotor persistido, existente e inicializado, alias de BD
  conocido. Su PK local debe ser un entero positivo representable, sin bool.
  El servicio no consulta User ni presupone el formato de su PK canónica.
- Código: str no vacía, máximo 32 caracteres conforme a los campos existentes,
  coincidencia exacta. Sin strip, cambio de mayúsculas, alias ni conversiones.
  Debe corresponder a una fila Specialization, sin crear catálogos automáticamente.

Devuelve `SpecializationSelectionResult`, dataclass frozen con `profile_id`,
`specialization_id`, `specialization_code`, `progress_id` y `created`.
`created=True` significa primera selección confirmada dentro de la transacción del
servicio; `False`, recuperación de la misma selección persistida. Sin datos de
User ni efectos de Rewards. Como los servicios locales anteriores, si el consumidor
abre una transacción exterior, su rollback puede revertir los cambios interiores.

## Estado y orden de validación

Dentro de transaction.atomic(using=alias), antes de lecturas mutables:

1. Recargar perfil y CharacterStats desde el alias. Validar identidades locales,
   propietario de stats, enteros estrictos (sin bool/conversión) y rangos de los
   campos/backend, XP no negativa, nivel positivo, seis atributos con signo,
   puntos no negativos y códigos estructurales. No recalcular progresión.
2. Leer las filas UserSpecializationProgress del perfil. Si la selección activa
   es NULL, debe no haber progreso. Si existe código activo, debe haber exactamente
   una fila compatible: propietario correcto, identidad/referencia persistidas,
   Specialization existente con código coincidente y domain_xp_total entero no
   negativo representable. Progreso adicional/incompatible o ausente es inconsistencia.
3. Selección coherente del mismo código: devolver IDs originales, conservando XP
   de dominio incluso positiva. Sin escrituras de negocio, configuración, catálogos
   de etapas/niveles ni comprobación de Actual actual.
4. Selección coherente de otro código: SpecializationConflictError, sin cambios,
   incluso si la configuración actual ya no está disponible.
5. Sin selección: aplicar S11-A-01. INITIAL_CONFIGURATION debe ser de tipo
   InitializationConfiguration y contener siete códigos únicos no vacíos de hasta
   32 caracteres. Solo se necesita esta correspondencia, no validar seis atributos
   iniciales S2-A. Leer EvolutionStage, validar campos e invariantes mediante el
   validador existente, usar StageDefinition y resolve_stage de S1, comprobar
   concordancia con la etapa persistida y exigir el código de ordinal 7 (Actual).
   No importar, consultar ni validar LevelThreshold.
6. Buscar Specialization por código exacto y validar sus campos persistidos.
   Actualizar únicamente active_specialization_code y crear una única fila de
   progreso con domain_xp_total=0, confirmados o revertidos juntos.

Un progreso ajeno no satisface la selección propia. Referencias inexistentes,
valores legacy incompatibles y estados parciales se rechazan sin borrar, reparar,
normalizar, completar estadísticas o reinicializar XP de dominio. La integridad
estructural no equivale a autorización global de un consumidor externo.

## Errores públicos

| Tipo | Situación |
| --- | --- |
| InvalidSpecializationProfileError | Perfil de entrada inválido/no persistido o desaparecido |
| InvalidSpecializationCodeError | Código de entrada inválido o especialización solicitada inexistente en primera selección |
| InvalidSpecializationConfigurationError | Configuración/catálogo de etapas inválidos o ausentes para elección nueva |
| IneligibleSpecializationStageError | Perfil coherente en etapa anterior a Actual |
| SpecializationConflictError | Selección coherente existente de otro código; no se implementa cambio |
| InconsistentSpecializationStateError | Perfil/stats/progreso/catálogo de especialización parciales o inválidos, o XP–etapa incoherentes |
| SpecializationDatabaseError | Fallo real de BD, bloqueo o escritura; causa original preservada |

No se capturan excepciones arbitrarias de programación. No hay reparación,
retry automático ni conversión de errores de BD a éxito/repetición aparente.

## Atomicidad y concurrencia

D-19: transaction.atomic usando el alias del perfil, SQLite BEGIN IMMEDIATE antes
de lecturas mutables y timeout configurado de cinco segundos. Sin cambios de
settings, select_for_update como supuesto bloqueo por fila ni I/O externo.
La unicidad existente (profile, specialization) sigue siendo defensa persistente.
Dos elecciones iguales serializadas producen una creación y una repetición;
dos diferentes producen una selección y un conflicto. El perfil y su progreso no
quedan parcialmente confirmados. Los errores permiten retry explícito posterior
en una nueva transacción. No se promete atomicidad entre bases independientes.

## Límites y pendientes

No se crean User, perfiles, stats, eventos ni migraciones. No hay XP histórica o
de dominio positiva, rangos, cambio/reinicio, varias selecciones activas, efectos
estadísticos, puntos, web, REST, JWT, configuración oficial, inventario o economía.
S2-A/S3/S4-A/S7-A, Rewards y módulos de otros equipos permanecen intactos.

P7 sigue abierto para códigos canónicos, obligatoriedad y acceso adicional,
cambios/reinicios, fuentes e idempotencia de concesiones positivas de dominio,
rangos Junior/Middle/Senior/Maestro e integración con juegos/Rewards. Core conserva
identidad/autorización, conservación/legacy y contratos globales pendientes.
Rewards v0 continúa candidato y F2-A bloqueada para persistencia.

## Verificación ejecutada

- test_specialization_service: 37 tests correctos (incluido alias SQLite temporal).
- test_specialization_concurrency: 4 tests correctos, conexiones independientes
  file-backed, solapamiento real, BEGIN IMMEDIATE antes de SELECT, timeout 5 s,
  invisibilidad de escritura no confirmada, rollback y retry en nueva transacción.
- Regresiones test_initialization, test_xp_service, test_stat_allocation y
  test_progress_queries: 154 tests correctos.
- Suite completa: 611 tests correctos, cero fallos y cero errores.
- manage.py check sin incidencias; makemigrations --check --dry-run sin cambios;
  git diff --check correcto. Sin alteraciones de las SQLite o archivos de demo.

Configuraciones, códigos y valores de prueba son sintéticos, no datos oficiales.
