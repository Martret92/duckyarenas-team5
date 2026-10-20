# A3.6 · Evidencia vigente y condiciones de clasificación · Contrato conceptual v1

## 1. Autoridad, alcance y estado

A3.6-FRESH-01, A3.6-COVERAGE-01 y A3.6-GATE-01 son decisiones aprobadas internamente
por Equipo 5 en 02C, documentadas el 20/10/2026 sobre develop
`bccc6175ee1751073d8f610d28e99c97da1aad05`. Desarrollan A3.4 y el protocolo A3.3.
DAR3 conserva su autoridad funcional; estas decisiones técnicas no se atribuyen
a DAR3, Óscar/Core o Henry. Se usa la trazabilidad existente, sin afirmar nueva
consulta directa de PDFs o respuestas externas.

[Decisiones](../decisions.md#a36--evidencia-vigente-y-condiciones-de-clasificación--20102026),
[arquitectura](../architecture.md#16-a36--evidencia-vigente-y-rechazo-seguro),
[pendientes](../pending-decisions.md#20-a36--cobertura-y-protocolo-de-evidencia-pendientes),
[clasificación A3.3](ecomotor-profile-classification-v1.md) y
[persistencia A3.4](ecomotor-classification-persistence-v1.md).

Reglas puras A3.3 integradas por #66 y arquitectura A3.4 por #67. No hay lector
interno de evidencia vigente, servicio persistente, modelos o migraciones de
clasificación implementados por este contrato. S3 V1 sigue siendo el único escritor
activo de XP. No se activa A2 ni se clasifica o migra ningún perfil.

## 2. Evidencia vigente · A3.6-FRESH-01

Para una operación **nueva**, comprobar los datos necesarios dentro de la misma
transacción que confirma la política y el evento. Una fotografía anterior no
sustituye esa comprobación, aunque el diagnóstico previo fuese COMPATIBLE.

| Plano de evidencia | Garantía y límite |
| --- | --- |
| Diagnóstico previo A3.2/A3.1 | Útil para preparar el análisis; no garantiza vigencia posterior mientras S3 u otros escritores autorizados modifiquen datos relevantes. |
| Verificación dentro de transacción | Necesaria para confirmar una operación nueva; evita decidir solo con una fotografía previa. No acredita suficiencia funcional por sí sola. |
| Suficiencia funcional | Requiere definir qué datos y comprobaciones acreditan cada transición con los propietarios; no se deduce de haber leído datos actuales. |

Dirección aprobada: **lector interno específico** para las comprobaciones del
futuro servicio. API y consultas definitivas pendientes. A3.2 permanece intacto
como extractor previo y rechaza transacciones exteriores; no invocarlo anidado
ni eliminar protecciones. No se implementa un lector en esta PR.

Aplicar D-19: alias confiable común, frontera atómica, SQLite BEGIN IMMEDIATE y
timeout de 5 segundos, confirmación/rollback conjunto de política y evento, sin
I/O externo durante la transacción. No prometer bloqueos de fila efectivos por
select_for_update ni atomicidad entre aliases/conexiones independientes.
La fotografía transaccional y sus costes de concurrencia no resuelven por sí
solos autorizaciones o condiciones externas obligatorias del corte.

## 3. Cobertura por operación · A3.6-COVERAGE-01

**Dirección aprobada, no lista exhaustiva de consultas implementables.** Las filas
fijan condiciones funcionales/técnicas a acreditar; fuentes, consultas, criterios
y cobertura verificable todavía deben concretarse con los módulos propietarios.

| Operación | Evidencia necesaria |
| --- | --- |
| Primera clasificación LEGACY_V1 | Perfil existente y procedencia acreditada por proceso confiable; PENDING_REVIEW no certifica integridad completa. |
| Primera clasificación NATIVE_V1 | Alta V1 confiable y verificada. |
| Primera clasificación NATIVE_TARGET | Alta objetivo válida y activación global autorizada; no disponible actualmente. |
| PENDING_REVIEW → V1_VERIFIED | Verificación suficiente de progresión, XP, referencias, estadísticas e historial V1. |
| V1_VERIFIED → TARGET_PREPARED | Compatibilidad del catálogo, datos objetivo y consumidores afectados. |
| TARGET_PREPARED → TARGET_CONFIRMED | Migración autorizada, verificación vigente y condiciones efectivas del corte global. |
| Bloqueo | Incidencia justificada y autorización, sin exigir que el perfil inconsistente supere verificaciones de avance. |
| Recuperación | Evento de bloqueo íntegro y validación nueva de condiciones correspondientes al estado de recuperación. |
| Replay histórico | Autorización, igualdad del contenido original e integridad histórica; no revalidar elegibilidad actual de la operación original. |

Concretar especialmente la cobertura verificable de V1_VERIFIED, TARGET_PREPARED
y TARGET_CONFIRMED, incluidas dependencias fuera del alcance A3.1/A3.2.
A3.1 COMPATIBLE **no certifica integralmente** historial de puntos, niveles,
especializaciones, rangos o Duckies; no convertirlo automáticamente en V1_VERIFIED.
A3.2 obtiene evidencia limitada y tampoco decide suficiencia por transición.
No inventar atributos, snapshots o datos históricos inexistentes para llenar huecos.
La recuperación conserva la matriz aprobada: solo vuelve al estado anterior al
bloqueo y exige validación nueva, sin borrar el evento original.

## 4. Rechazo seguro y replay · A3.6-GATE-01

Una operación nueva no se confirma si falta evidencia requerida/suficiente,
vigencia de datos, autorización confiable, condiciones externas obligatorias o
coherencia de política, historial o revisión. Rechazar sin efectos ni eventos
parciales; no corregir, inferir clasificación o iniciar migración automáticamente.

El bloqueo no exige verificar avance del perfil inconsistente, pero sí cumplir
sus condiciones propias de autorización, incidencia y coherencia de la operación.
Esto no exime de revisión esperada, integridad histórica o atomicidad.

Replays confirmados mantienen [el protocolo A3.3](ecomotor-profile-classification-v1.md#72-orden-de-procesamiento--a33-replay-protocol-01):
validación inicial/autorización, transacción, evento primero, identidad/contenido
original e integridad histórica. Replay compatible devuelve resultado histórico
sin mutar el estado vigente ni repetir comprobaciones de una operación nueva.
No exigirle superar la cobertura actual de avance, ni tratar historia insuficiente
como igualdad inferida. Un replay de bloqueo tras recuperación no vuelve a bloquear.

TARGET_CONFIRMED no activa el escritor objetivo. S3 V1 sigue como único escritor
activo de XP hasta corte global autorizado; no escritores paralelos, migraciones
automáticas o clasificación automática de perfiles legacy.

## 5. Dependencias abiertas: A3.5 y cobertura verificable

**A3.5 permanece abierto.** [Consulta Core/P5](ecomotor-classification-core-boundary-v1.md)
con cinco preguntas no respondidas/ratificadas: CORE-A3.3-IDENTITY, AUTH, LIFECYCLE,
RETENTION y PRIVACY. No aprobar identidad del operador, permisos, conservación,
privacidad o on_delete. Su participación canónica en comparación sigue pendiente.
Ese documento no se modifica por A3.6.

Parte A y propietarios deben concretar API/consultas del lector, comprobaciones
suficientes por transición y cómo acreditar condiciones externas sin I/O dentro
de la transacción. Henry/consumidores conservan sus dependencias de catálogo,
datos e integración. Formato físico, modelos/migraciones y servicio siguen sujetos
a las puertas A3.4/Core; esta arquitectura no habilita ninguno por inferencia.

## 6. Pruebas futuras del servicio persistente

- Fotografía obsoleta tras concesión S3 y verificación actual dentro de transacción.
- Evidencia incompleta o incoherente: rechazo sin confirmación parcial.
- Bloqueo ante incidencia aunque no pueda verificarse una transición de avance.
- Recuperación con validación nueva y evento de bloqueo original íntegro.
- Replay válido sin repetir verificaciones de operación nueva ni mutar estado actual.
- Concurrencia, rollback, ausencia de eventos parciales y aislamiento de perfiles/alias.
- Regresión S3 V1; sin migración automática o concesiones XP objetivo.

No se crean ni ejecutan nuevos tests Django: esta PR solo documenta garantías y
pruebas pendientes. No modifica A3.1, A3.2, reglas puras A3.3, historial, Core,
Duckies, Bank/Shop, Rewards, modelos, configuración o datos.
