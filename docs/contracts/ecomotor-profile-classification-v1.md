# A3.3 · Clasificación persistente de perfiles · Contrato conceptual v1

## 1. Autoridad, alcance y estado vigente

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
| A3.3 | Solo arquitectura: sin modelos, tabla, migración, backfill, servicio o clasificación real. |

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
| revision | Contador monotónico no negativo para control de concurrencia. |
| created_at / updated_at | Fechas de creación y actualización del registro. |

No condensar procedencia y transición en un campo de versión. La asociación y
campos anteriores no aprueban tipos Django, constraints físicos, on_delete,
tabla o migración. La política física sigue condicionada a Core/P5.

## 3. Procedencia y estados candidatos

**A3.3-ORIGIN-01:** procedencia explícita, sin default que clasifique automáticamente.
Valores candidatos: `LEGACY_V1`, `NATIVE_V1`, `NATIVE_TARGET`. Una procedencia
confirmada se conserva y no cambia silenciosamente durante una transición.
Nombres definitivos y matriz completa de validez pendientes antes de codificar.

**A3.3-STATE-01:** estados candidatos `PENDING_REVIEW`, `V1_VERIFIED`,
`TARGET_PREPARED`, `TARGET_CONFIRMED`, `BLOCKED`. Son vocabulario de diseño, no
constantes implementadas ni un diagrama de transiciones autorizado por sí solo.
Nombres definitivos, combinaciones procedencia/estado, transiciones válidas y
permisos correspondientes requieren concreción y pruebas antes de servicios.

**Ausencia de registro = perfil no clasificado**, no `PENDING_REVIEW`.
No inferir clasificación por fecha de creación, nivel, XP, época, especialización,
estadísticas o ausencia de `UserPlayableState`. Los perfiles existentes necesitan
auditoría; no se clasifican al leerlos ni mediante defaults/backfill automático.

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
fabricar procedencia de eventos V1. Campos canónicos de comparación y detalle
entre replay y revisión esperada deberán especificarse sin alterar estas garantías.
No se publica una firma definitiva ni un formato HTTP.

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
bajo una frontera transaccional segura. El mecanismo para obtener/verificar esa
evidencia está pendiente: no se presume que pueda invocarse el extractor A3.2
dentro de otra transacción, pues el extractor actual rechaza transacciones exteriores.
No cambiarlo ni eliminar su protección por este diseño. No realizar backfill ni
inventar identidad o procedencia de eventos antiguos.

## 7. Operación futura, atomicidad y errores · A3.3-TX-01

Entradas conceptuales necesarias: perfil, acción, procedencia/estado pertinentes,
clave de operación, revisión esperada, evidencia requerida y contexto autorizado
con alias confiable. No constituyen firma Python o servicio disponible.

Validar identidad/propiedad, autorización, reglas de transición, inmutabilidad de
procedencia, evidencia vigente y revisión esperada. Confirmar **política y evento
juntos**, o ninguno. Repetición compatible no vuelve a mutar; una revisión obsoleta
rechaza cambios. El protocolo preciso de primera creación y orden replay/revisión
requiere concreción previa a implementación, sin prometer transiciones adicionales.

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
| 2 | Reglas puras y validadores de estados/transiciones en 01B, previa concreción de nombres/matriz. |
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
