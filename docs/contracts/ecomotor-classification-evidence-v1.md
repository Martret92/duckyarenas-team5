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

## 7. A3.6.1 · Verificaciones locales V1

**A3.6.1-V1-LOCAL-01**, aprobada internamente por Equipo 5 en 02C y documentada
el 20/10/2026 sobre develop `959b102a608883373b7dd0f8e62a65dffe5c7df4`.
Concreta parcialmente A3.6-COVERAGE-01, no su cobertura final suficiente para
V1_VERIFIED. DAR3 conserva autoridad funcional; esta delimitación técnica no se
atribuye al profesor o a Core. Se han revisado los archivos enlazados, sin ejecutar
sus servicios o tests ni afirmar una nueva consulta directa de PDFs.
[Decisión](../decisions.md#a361--verificaciones-locales-v1--20102026) y
[pendientes](../pending-decisions.md#21-a361--límites-de-verificación-local-v1).

### 7.1. Matriz de evidencia, código existente y límites

Fuentes comunes: [modelos Ecomotor](../../apps/ecomotor/models.py) y
[perfil Users](../../apps/users/models.py). Las constraints y campos persistidos
aportan garantías concretas, no prueba de completitud histórica. Las comprobaciones
siguientes son locales a V1; no aplican nomenclatura/catálogos objetivo a datos V1.

| Grupo | Qué comprueba ya el código existente / fuentes | Posible con datos actuales, aún no implementado en lector A3.6 | Qué no acredita completamente |
| --- | --- | --- | --- |
| Perfil | [A3.2](../../apps/ecomotor/legacy_inventory_reader.py) verifica ID/alias y existencia al extraer; [A3.1](../../apps/ecomotor/legacy_transition_audit.py) comprueba representación de XP total/nivel/códigos. [S2-A](../../apps/ecomotor/initialization.py) comprueba User existente y estructura de pareja perfil/stats; [S3](../../apps/ecomotor/xp_service.py) vuelve a leer perfil y valida estructura en su operación. | Verificar existencia e identidad local, pertenencia/alias, valores de XP total, nivel y etapa en la misma transacción de clasificación; distinguir inexistencia de perfil de datos inválidos. | Fecha, XP o estado actual no prueban procedencia LEGACY_V1/NATIVE_V1. La relación con User no sustituye identidad/autorización Core ni garantiza cómo se creó el perfil. |
| Estadísticas | A3.2 observa CharacterStats o ausencia; A3.1 comprueba ausencia observada, pertenencia y valores representables del subconjunto V1. S3 y [S7-A](../../apps/ecomotor/stat_allocation.py) validan estructura; S7-A comprueba rangos del backend para su operación. | Verificar existencia, perfil propietario y representabilidad de seis atributos V1 y available_points bajo el alias elegido. Ausencia observada no es fallo de lectura; datos no representables se distinguen de base funcional desconocida. | No hay prueba general de las bases históricas autorizadas ni del origen/gasto íntegro de puntos. No imponer positividad ficticia a todos los atributos IntegerField ni sustituir log_stat/spe por atributos objetivo. |
| XPEvent | A3.1 detecta IDs/claves duplicados en la evidencia, propietario incorrecto, importes/snapshots inválidos, xp_after superior al total y total sin extremo observado suficiente. Constraints fijan unicidad por perfil/clave y suma de cada evento. Replay S3 valida el evento solicitado y su relación con el total; no audita todo el historial. | Examinar todos los eventos observados del perfil, identidad/claves exactas, importes positivos y coherencia xp_after=xp_before+amount; evaluar relaciones observables con el total sin inferir cronología por PK. | Llegar al total observado no demuestra completitud. Concesiones antiguas ausentes impiden acreditar toda la cadena; no sumar eventos como prueba universal ni inventar los faltantes. XPEvent no guarda versión, nivel/etapa o puntos como snapshots. |
| EvolutionEvent | A3.1 comprueba referencias a etapa/XP y pertenencia en snapshots; A3.2 y S3 detectan causalidad cruzada en ambos sentidos. Existe unicidad perfil/etapa; S3 crea eventos causales para etapas cruzadas en una concesión nueva. | Examinar referencias/casos ausentes y propietario de cada causa, incluidas evoluciones ajenas que referencien XP propia, con información mínima sin exponer historiales de terceros. | EvolutionEvent referencia EvolutionStage actual, sin conservar sus atributos originales. No reconstruir nombres/umbrales/ordinales históricos con el catálogo vivo ni asumir que están registrados todos los cambios antiguos. |
| Progresión | [S1](../../apps/ecomotor/progression.py) resuelve nivel/etapa y transiciones sobre definiciones validadas. S3 compara nivel/etapa actuales con XP y catálogo V1 para una concesión nueva; S7-A y [S11-A](../../apps/ecomotor/specialization_service.py) contrastan etapa y elegibilidad de sus operaciones. A3.1 no deriva niveles ni valida esta correspondencia integral. | Con catálogo V1 completo/válido y correspondencia confiable de códigos, resolver nivel/etapa para XP actual y comparar con perfil. Separar configuración ausente/inaplicable de contradicción observable frente a configuración válida aplicable. | Un catálogo vigente no prueba qué catálogo regía antiguamente ni reconstruye nivel/etapa históricos sin snapshots. No convertir un cambio de configuración en prueba automática de corrupción histórica ni usar siete épocas objetivo para reinterpretar V1. |
| StatAllocationEvent | S7-A valida identidad, clave, propietario, atributo V1, importes representables y snapshots del evento solicitado en replay; constraints verifican gasto positivo, aumento 1:1 y ecuaciones de saldo/atributo. Operación nueva valida etapa Actual, fondos y actualización conjunta. A3.1/A3.2 no incluyen estos eventos en su cobertura actual. | Leer y comprobar los eventos disponibles por perfil: identidad/claves, gasto, incremento, saldo antes/después y atributo antes/después. Diagnosticar contradicciones locales sin ejecutar allocate_stat_points o escribir. | Snapshots individuales no reconstruyen todo el origen/gasto de puntos si falta historia; tampoco bases antiguas o puntos concedidos por niveles sin snapshot. No exigir que la suma observada explique todo el saldo ni ordenar globalmente por PK para fabricar un ledger. |
| Especializaciones | S11-A valida selección activa, catálogo, pertenencia/identidad de UserSpecializationProgress, referencias, duplicados y dominio representable en las filas que examina; la selección activa debe tener progreso compatible. Unicidad perfil/especialización y dominio no negativo constan en modelos. A3.1/A3.2 no cubren integralmente este dominio. | Examinar código activo, Specialization referenciada y progresos observables del perfil, coherencia de selección/posesión y valores representables, sin invocar selección o cambiar estado. | Estado actual no prueba historial completo de selecciones/cambios, concesiones de dominio o rangos. No inventar DomainXPEvent ni inferir rangos persistidos a partir de un evaluador puro. |

No reutilizar servicios de escritura como auditores: ensure_ecomotor_initialized,
grant_historical_xp, allocate_stat_points y select_initial_specialization pueden
escribir en sus operaciones propias. Sus validaciones describen comportamiento
implementado, no una API de lectura integral. El lector A3.6 sigue sin existir;
esta matriz no aprueba sus consultas finales ni modifica esos servicios.

### 7.2. Resultados conceptuales de cada comprobación

| Categoría conceptual | Alcance |
| --- | --- |
| Comprobación superada | Datos examinados cumplen las reglas aplicables a esa comprobación, con su alcance y evidencia identificados. |
| Evidencia insuficiente | Faltan datos o garantías para acreditar la condición; no se supone coherencia ni se inventa historia. |
| Incoherencia detectada | Se observa una contradicción verificable, diferenciada de una mera ausencia de información. |

No son valores nuevos de TransitionState, enums Python o cambios de LegacyAuditStatus.
No existe conversión automática de estas categorías o de COMPATIBLE a V1_VERIFIED.
Una comprobación superada no certifica el perfil entero; evidencia insuficiente
sobre una parte no invalida injustificadamente las observaciones válidas de otras.

### 7.3. Vigencia, dependencias y pruebas futuras

A3.6-FRESH-01 permanece íntegra: las comprobaciones exigidas para una operación
nueva se ejecutarán dentro de la transacción que confirme política y evento,
mismo alias confiable, D-19/BEGIN IMMEDIATE/timeout 5 s y rollback íntegro, sin
I/O externo. Una fotografía previa no acredita por sí sola vigencia. No anidar
A3.2 ni cambiar sus protecciones; API/consultas del lector siguen pendientes.
Replay histórico mantiene A3.3 sin revalidar elegibilidad actual.

Pendientes: completitud de XP antigua; origen/gasto íntegros de puntos si falta
historia; atributos históricos de etapas no persistidos; historia de especialización/
dominio/rangos; referencias Duckies/inventario con Henry; procedencia confiable
sin inferencias; cobertura final V1_VERIFIED; A3.5 identidad/autorización/retención/
privacidad/on_delete con Óscar/Core. No crear XPEvent, historiales o procedencias
para subsanar huecos ni autorizar migración por estas comprobaciones parciales.

Tests futuros del lector/servicio: perfil correcto/inexistente; stats ausentes o
inválidas; XPEvent duplicado/incoherente; evolución con causa XP ajena; nivel/etapa
actuales incompatibles con XP/catálogo aplicable; gasto coherente frente a historia
insuficiente; selección/progreso incompatibles; cambios S3 entre diagnóstico y
verificación; replay sin nueva elegibilidad; ausencia de escrituras, reparación,
backfill o activación XP objetivo. No se crean ni ejecutan tests Django aquí.
