# A3.4 · Persistencia de clasificación · Dirección arquitectónica v1

## 1. Autoridad y estado

**A3.4-ARQ-01**, aprobada internamente por Equipo 5 en 02C y documentada el
20/10/2026 sobre develop `8b6b0f783b0042e66c53d9b46dfb930edae94f73`.
Aprueba una dirección arquitectónica mínima, no modelos Django definitivos,
migraciones o acuerdos externos. DAR3 conserva su autoridad funcional; no se
atribuye esta elección técnica al profesor, Core/P5 o Henry. Se utiliza la
trazabilidad existente, sin afirmar nueva consulta directa de PDFs.

[Decisión](../decisions.md#a34--dirección-de-persistencia-de-clasificación--20102026),
[arquitectura](../architecture.md#15-a34--dirección-de-persistencia-local),
[ERD candidato](../erd/ecomotor.md#17-a34--dirección-física-candidata-de-clasificación),
[pendientes](../pending-decisions.md#19-a34--puertas-de-persistencia-y-servicio),
[protocolo A3.3](ecomotor-profile-classification-v1.md) y
[consulta Core/P5](ecomotor-classification-core-boundary-v1.md).

Las [reglas puras A3.3](../../apps/ecomotor/profile_classification_rules.py) y
[sus tests](../../apps/ecomotor/test_profile_classification_rules.py) están integrados
por PR #66. No persisten ni autorizan operaciones. S3 V1 sigue como único escritor
XP hasta corte global autorizado; A2.1 solo planifica. No hay tablas o servicio
transaccional de clasificación, backfill, migración o activación objetivo.

## 2. Propiedad y política candidata

ProfileProgressionPolicy y ProfileProgressionPolicyEvent pertenecen a
`apps.ecomotor`, Equipo 5, con referencia conceptual a `users.UserProfileEcomotor`.
No redefinen User, autenticación ni modelos de Core.

ProfileProgressionPolicy: como máximo una política por perfil, OneToOne conceptual.
Datos candidatos: `profile`, `origin`, `transition_state`, `revision`, `created_at`,
`updated_at`. Procedencia explícita e inmutable, transición separada y revisión
**positiva**: primera confirmación 1, transición nueva +1. Sin defaults clasificadores;
sin fila significa perfil no clasificado, no PENDING_REVIEW.

El registro actual no sustituye solicitudes ni snapshots históricos. Modelo,
campos/tipos/longitudes/nulidad/colaciones/relaciones/constraints SQL y on_delete
siguen pendientes de diseño final y acuerdos externos necesarios.

## 3. Evento candidato y reconstrucción exacta

ProfileProgressionPolicyEvent es historial separado e inmutable, asociado
conceptualmente al perfil. Datos candidatos:

| Grupo | Datos candidatos |
| --- | --- |
| Identidad | profile, operation_key |
| Solicitud original | action, origin, target_state, expected_revision, incident_reference, blocking_operation_key |
| Antes | before_state, before_revision |
| Después | after_state, after_revision |
| Confirmación | confirmed_at, referencia al operador autorizado pendiente de Core/P5 |

Esta dirección debe permitir reconstruir **exactamente**, sin consultar el estado
actual para completar historia, los objetos de la API pura integrada:

| Objeto puro | Evidencia persistida necesaria |
| --- | --- |
| ClassificationRequest | profile_id, operation_key y todos los componentes originales de solicitud: acción/origen/destino/revisión esperada/referencia de incidencia/referencia de bloqueo. |
| PolicySnapshot anterior o None | Ausencia real para primera clasificación; en otros casos perfil, procedencia, estado y revisión anteriores. |
| PolicySnapshot posterior | Perfil, procedencia, estado y revisión confirmados por esa operación. |
| ConfirmedClassificationEvent | Request original y before/after originales, no el candidato calculado ni una reconstrucción desde la política actual. |

La procedencia es inmutable: el dato origin solo puede representar los snapshots
de ambos lados si se preserva y valida su igualdad causal con la solicitud. No se
rellenan snapshots desde una política viva o una procedencia inferida.
Primera clasificación: before=None y revisión previa conceptualmente ausente,
**nunca cero inventado**. La representación física de esa ausencia aún no se elige.
Conservar None frente a texto vacío y textos opacos exactos; no normalizar claves.

Un bloqueo conserva inequívocamente el estado anterior. Una recuperación debe
reconstruir el evento de bloqueo referenciado y comprobar su correspondencia
con perfil, procedencia, estados y revisiones mediante la API pura. Bloqueo y
recuperación tienen identidades distintas, conforme a la regla integrada por #66.
No elegir una FK física al bloqueo. La referencia textual propuesta no sustituye
las comprobaciones de integridad histórica ni aprueba su representación definitiva.
Operador/fecha no forman parte de la API pura actual; no inventar su política de
comparación ni confundir una dataclass aportada con prueba de confirmación en BD.

## 4. Unicidad e integridad

**Garantía aprobada:** identidad de clasificación UNIQUE(profile, operation_key),
separada de XPEvent y StatAllocationEvent. La restricción SQL concreta queda por
especificar; debe respetar igualdad exacta de claves, tipos y alcance por perfil.

**Propuesta física adicional, no aprobada definitivamente:**
UNIQUE(profile, after_revision).

| Ventaja propuesta | Límite / consecuencia a evaluar |
| --- | --- |
| Evita dos eventos confirmados para la misma revisión de un perfil. | No garantiza que la secuencia empiece en 1, carezca de huecos o avance exactamente +1. |
| Refuerza correspondencia entre cadena histórica y revisión actual. | No comprueba por sí sola procedencia inmutable, before/after coherentes, contenido original, vínculo al bloqueo o existencia del evento de cada actualización. |
| Puede detectar colisiones de revisiones bajo concurrencia. | Exige evaluar datos/representabilidad antes de adoptarla; no justifica reparar o renumerar historia. No sustituye revisión esperada ni rollback de política/evento. |

Constraints locales podrán evaluarse para revisión positiva y coherencia de
campos, sin fijar SQL definitivo ni prometer CHECK entre tablas. La unicidad y
las demás restricciones no sustituyen reglas puras, evidencia, autorización o
atomicidad. No se crean constraints o migraciones en esta PR.

## 5. Representación física: recomendación y alternativas

**Recomendación provisional:** campos explícitos para solicitud y snapshots
originales, por facilitar validación, consultas y reconstrucción exacta. No es
aprobación de tipos Django o esquema final.

| Alternativa | Ventajas y límites |
| --- | --- |
| Campos explícitos | Facilitan controles y consultas; requieren resolver nulidad, tipos, colaciones y evolución del esquema sin pérdida de contenido original. |
| JSON versionado | Conserva estructura y permite evolución; exige esquema/validación y fidelidad de tipos/ausencia. No hace verificable por sí solo la integridad o la indexación necesaria. |
| Hash del contenido | Puede ayudar a detectar diferencia; solo el hash no reconstruye request/before/after ni justifica igualdad histórica suficiente. No sustituye los datos originales. |
| Reconstrucción exclusivamente desde eventos | Puede derivar política actual de una cadena completa; exige historia íntegra, orden y consistencia verificables. No se adopta como sustituto del registro de política y su actualización conjunta. |

La API pura no introduce máximos físicos especulativos para claves, IDs o
revisiones. Analizar capacidad de enteros, overflow, longitud de texto, colaciones
y comparación exacta frente a esa API antes de fijar límites persistentes. Si un
valor no fuese representable, acordar validación y error explícitos, sin truncar,
normalizar o convertir silenciosamente. No se fijan máximos aquí.

## 6. Frontera transaccional futura

1. Validación estructural y autorización confiable previa del solicitante.
2. Mismo alias y transacción D-19: SQLite BEGIN IMMEDIATE y timeout 5 segundos,
   conforme a la configuración vigente. Sin I/O externo dentro de la transacción.
3. Buscar evento histórico por perfil/operation_key antes de aplicar reglas de
   operación nueva; reconstruir request/snapshots y, si corresponde, bloqueo.
4. Validar integridad y contenido mediante el módulo puro A3.3. Replay compatible
   devuelve resultado histórico sin mutar política/eventos/revisiones, aunque el
   estado actual haya avanzado. Contenido incompatible o historia insuficiente:
   rechazo sin efectos; no reconstrucción por inferencia ni reparación.
5. Solo para nueva operación: comprobar revisión esperada/ausencia, procedencia,
   matriz, estado, autorización y evidencia vigente suficiente. Obtener y validar
   evidencia dentro de la frontera descrita en §7; usar las reglas puras para el
   candidato. Un NEW_CANDIDATE no es una confirmación persistida.
6. Confirmar política y evento juntos, o rollback íntegro. El futuro servicio
   deberá comprobar persistencia e integridad, no solo envolver datos en una
   ConfirmedClassificationEvent.

No afirmar bloqueo efectivo de filas por select_for_update en SQLite ni
atomicidad entre aliases/conexiones independientes. D-19 no aporta permisos
externos ni una activación global. Replays siguen autorizados y su resultado
histórico no es el estado actual. No se implementa el flujo.

## 7. Evidencia vigente y lector interno específico

**Dirección aprobada:** lector interno específico para comprobaciones en la
transacción futura. Su API, consultas y cobertura funcional no se especifican aún.
A3.2 permanece intacto como extractor de inventario previo y rechaza transacciones
exteriores; no se invoca anidado ni se eliminan sus protecciones.

| Evidencia | Uso y límite |
| --- | --- |
| Fotografía previa A3.2 | Útil para diagnóstico A3.1; susceptible de obsolescencia mientras S3 escribe. No autoriza clasificación o migración. |
| Evidencia leída/validada en transacción | Necesaria para decidir operaciones nuevas bajo una frontera coherente; exige comprobar suficiencia, no solo actualidad. |
| Cobertura por transición | Pendiente especificar comprobaciones de V1_VERIFIED, TARGET_PREPARED y TARGET_CONFIRMED, incluidas dependencias fuera de A3.1/A3.2. |

A3.1 COMPATIBLE no certifica toda la coherencia V1, puntos gastados, dominio,
especializaciones o Duckies. No se considera resuelto el protocolo concreto por
proponer un lector transaccional. Autorización, catálogo/causalidad, consumidores,
clasificación y migración conservan controles propios.

## 8. Bloqueos, incrementos y pruebas futuras

[Propuesta Core/P5](ecomotor-classification-core-boundary-v1.md#4-puertas-de-modelos-y-servicio)
distingue dependencias que bloquean modelos/migraciones finales de las que bloquean
el servicio posterior. No se elige on_delete o identidad del operador.

Secuencia orientativa, no calendario aprobado: esta documentación A3.4 → acuerdos
Core/P5 necesarios → protocolo de evidencia/cobertura por transición → modelos y
migraciones sin backfill tras acuerdos → servicio/tests → integración y ensayos
con Core, Henry y consumidores → migración y activación global autorizadas.
Las reglas puras ya integradas no ejecutan ninguno de esos pasos persistentes.

Tests futuros: OneToOne por perfil; unicidad de operación y, si se aprueba, revisión;
constraints/representabilidad; reconstrucción exacta request/before/after; primera
clasificación con ausencia real; replay posterior sin mutar estado vigente;
conflictos; bloqueo/recuperación con historial íntegro; concurrencia inicial y de
revisiones; rollback conjunto/timeout; evidencia obsoleta/insuficiente; aislamiento
de perfiles/aliases; autorización/retención/eliminación conforme a Core; regresión
S3 V1, sin backfill ni concesiones objetivo. No se crean ni ejecutan tests Django.
