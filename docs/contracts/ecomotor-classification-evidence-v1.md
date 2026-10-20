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

## 8. A3.6.2 · Contrato conceptual del lector transaccional V1

A3.6.2-READER-01, INPUT-01, RESULT-01 y ERROR-01, aprobadas internamente por
Equipo 5 en 02C, documentadas el 20/10/2026 sobre develop
`1c03e6493ae871e08243eccbcfe154b724a106a9`. Desarrollan A3.6/A3.6.1; DAR3 sigue
principal, sin atribuir decisiones técnicas o ratificación a Óscar/Core o Henry.
[Registro](../decisions.md#a362--contrato-del-lector-transaccional-v1--20102026)
y [pendientes](../pending-decisions.md#22-a362--detalle-del-lector-y-dependencias).
**Contrato conceptual, lector no implementado y sin API Python definitiva.**

### 8.1. Responsabilidad transaccional · A3.6.2-READER-01

El futuro servicio de clasificación controla la transacción D-19. El lector
trabaja dentro de esa misma frontera: no abre, confirma o cierra una transacción
propia, no sale del alias confiable ni invoca servicios capaces de escribir.
No modifica perfiles/eventos/catálogos/stats, no invoca A3.2 anidado y no hace
I/O externo. Operación nueva verifica evidencia antes de confirmar política/evento.

Mismo alias autorizado, SQLite BEGIN IMMEDIATE, timeout 5 segundos, rollback
conjunto y aislamiento frente a operaciones concurrentes de la misma BD.
La lectura participa en una transacción que puede bloquear temporalmente escritores;
no es promesa de lectura gratuita ni de bloqueos de fila por select_for_update.
No hay garantía de atomicidad entre bases/conexiones independientes.

**in_atomic_block por sí solo no acredita una frontera confiable**: mecanismo
para asegurar que el contexto corresponde a la transacción controlada por el
servicio todavía pendiente. No equiparar cualquier transacción exterior con esa
frontera. A3.2 mantiene sus protecciones y su extracción previa separada.

### 8.2. Entradas mínimas · A3.6.2-INPUT-01

| Entrada conceptual | Garantía requerida / límite |
| --- | --- |
| Identidad local del perfil | Perfil a examinar, sin permitir acceso a perfiles ajenos por conocer su ID. |
| Alias de BD | Validado y autorizado por el servicio; lector no consulta otro alias. |
| Plan de comprobaciones | Elegido por lógica confiable del servidor según operación; cliente no elige qué verificaciones omitir. |
| Contexto transaccional | Permite asegurar la ejecución en la transacción correcta; representación y mecanismo de acreditación pendientes. |

No fijar parámetros, credenciales/tokens, tipos Django o clases definitivas.
Identidad del operador y autorización pertenecen al servicio y siguen condicionadas
a A3.5/Core. El lector observa/diagnostica: no decide qué transición está permitida,
no autoriza, clasifica o confirma operaciones.

### 8.3. Resultado conceptual · A3.6.2-RESULT-01

Proponer resultado **inmutable** que identifique perfil examinado y ámbito de BD,
grupos solicitados, comprobaciones realmente realizadas, cobertura efectiva,
limitaciones y resultados/diagnósticos correspondientes. Conservar las categorías
A3.6.1: comprobación superada, evidencia insuficiente e incoherencia detectada.
No crear enums Python/TransitionState ni convertir éxito local en V1_VERIFIED.

Una lectura parcial conforme a un plan explícito debe declarar su alcance; no es
cobertura universal. Consulta fallida, truncada o incompleta nunca representa
cobertura total ni un grupo superado. Evitar verified=True global o cualquier
indicador que aparente autorización/certificación completa. Valores históricos
sensibles y operation_key no se exponen indiscriminadamente en errores, logs o
respuestas; solo información necesaria y autorizada, sin historiales ajenos.
Formato del resultado, detalle de diagnósticos y política de exposición pendientes.

### 8.4. Fallos frente a diagnósticos · A3.6.2-ERROR-01

| Categoría conceptual | Distinción que debe conservarse |
| --- | --- |
| Perfil inválido o inexistente | No fabricar evidencia de un perfil válido ni confundir ausencia de perfil con datos leídos correctamente. |
| Alias/contexto inválido o no confiable | Rechazar lectura en ese contexto, sin consultar fuera del ámbito autorizado. |
| Error de BD/timeout o lectura truncada | Fallo técnico que obliga a abortar la lectura; servicio garantiza rollback. No convertirlo en vacío, éxito o cobertura completa. |
| Acceso indebido/referencias cruzadas | Acceso fuera de autorización obliga a abortar. Una contradicción causal observada con datos mínimos autorizados debe distinguirse del acceso indebido; solo es diagnóstico si se puede representar una comprobación completa sin exponer terceros. Si no puede garantizarse la lectura, abortar, sin ampliar permisos. |
| Evidencia insuficiente | Puede ser diagnóstico tras comprobación completa que constate falta de información histórica; no significa corrupción ni fallo técnico encubierto. |
| Incoherencia verificable | Contradicción observada representable con alcance suficiente; no reparar datos ni clasificar automáticamente. |

Queda por definir el detalle de representaciones y fallos según cada comprobación;
no jerarquía definitiva de excepciones Python o códigos HTTP. Ausencia de
información no equivale a corrupción demostrada. Ningún diagnóstico sustituye
las condiciones de rechazo de A3.6-GATE-01 o las autorizaciones externas.

### 8.5. Integración con A3.3 y límites de cobertura

1. Servicio valida identidad, petición y autorización confiable.
2. Abre transacción D-19 en el alias autorizado.
3. Busca evento histórico por identidad de operación.
4. Si existe, comprueba contenido original e integridad y resuelve replay sin
   nueva elegibilidad ni invocar al lector para verificar elegibilidad actual.
5. Solo para operación nueva, comprueba política/revisión vigentes, verifica
   evidencia requerida con el lector A3.6.2 y aplica reglas puras A3.3.
6. Confirma política/evento conjuntamente o revierte.

Replay sigue autorizado y no consulta perfiles ajenos. No alterar las reglas
puras ni confundir evidencia de elegibilidad con integridad histórica del replay.
Se conservan los siete grupos de §7.1: perfil, stats, XPEvent, EvolutionEvent,
progresión, StatAllocationEvent y especializaciones. No son lista obligatoria
universal: el plan servidor debe justificar qué exige cada operación.

No fabricar estados históricos desde catálogo vivo ni reconstruir eventos, XP,
puntos, rangos o especializaciones inexistentes. Siguen abiertas suficiencia
V1_VERIFIED, procedencia confiable y coordinación Duckies/Henry. El lector local
V1 no autoriza catálogo objetivo, migración o condiciones de corte global.

A3.5 mantiene sus cinco preguntas abiertas: identidad, autorización, ciclo de vida,
retención y privacidad. [Consulta Core/P5](ecomotor-classification-core-boundary-v1.md)
intacta, sin aprobación de on_delete/User o participación canónica del operador.
S3 V1 sigue único escritor XP; no activar objetivo ni migración.

### 8.6. Pruebas futuras

Dentro/fuera de transacción; alias autorizado y rechazo de otro alias; perfil
existente/inexistente; comprobaciones parciales/cobertura insuficiente; incoherencia
frente a error de lectura; timeout/rollback sin cobertura falsa; referencias cruzadas
sin datos ajenos; lectura coherente frente a S3 concurrente; replay sin invocar
elegibilidad nueva; ausencia de escrituras, reparaciones, backfill y XP objetivo.
No se implementan ni ejecutan nuevos tests Django en esta PR documental.

## 9. A3.6.3 · Criterios locales necesarios para V1_VERIFIED

A3.6.3-MIN-01, GAPS-01, NATIVE-01 y TIME-01, aprobadas internamente por Equipo 5
en 02C, documentadas el 20/10/2026 sobre develop
`080849ee207c05f844d5ccfd1624ab270d1d5a3a`. DAR3 conserva autoridad funcional;
no son requisitos literales nuevos ni ratificaciones de Óscar/Core o Henry.
[Registro](../decisions.md#a363--criterios-de-suficiencia-v1--20102026) y
[pendientes](../pending-decisions.md#23-a363--suficiencia-lagunas-y-procedencia-pendientes).

Estas condiciones permiten **estudiar** PENDING_REVIEW → V1_VERIFIED, no aprobar
su cobertura final ni confirmar transiciones por sí mismas. El lector y el
servicio persistente siguen sin implementar; no se publica una API o esquema.

### 9.1. Controles locales según aplicabilidad · A3.6.3-MIN-01

| Grupo | Condición local necesaria cuando corresponda |
| --- | --- |
| Perfil | Existencia, identidad y valores representables. |
| Estadísticas | CharacterStats existente, relacionado correctamente y con valores válidos. |
| XP | Coherencia de todos los eventos observados y snapshots, sin afirmar completitud histórica no demostrada. |
| Evoluciones | Referencias, causas XP y pertenencia correctas, incluidos casos de causalidad cruzada. |
| Progresión | Nivel/etapa actuales coherentes con XP y catálogo V1 validado y acreditado como aplicable. |
| Puntos | Coherencia de eventos de gasto disponibles, sin reconstruir saldos históricos inexistentes. |
| Especializaciones | Selección activa/progresos consistentes con reglas aplicables, respetando ausencia de especialización cuando sea válida. |

Controles necesarios **según operación y procedencia**, no lista que certifique
por sí sola V1_VERIFIED. La matriz de §7.1 conserva fuentes y límites del código
existente; §8 conserva el contrato del lector. No introducir reglas que contradigan
V1 ni usar catálogo actual como prueba de hechos históricos sin acreditar su
aplicabilidad histórica. Catálogo válido y catálogo aplicable son requisitos distintos.

No considerar incoherencia por defecto la ausencia legítima de eventos o selección.
En [S11-A](../../apps/ecomotor/specialization_service.py), selección ausente sin
progresos puede ser un estado válido; selección/progresos contradictorios requieren
su comprobación específica. No exigir a cualquier perfil una especialización activa.

### 9.2. Lagunas y decisión de avance · A3.6.3-GAPS-01

| Situación | Alcance y consecuencia para una operación nueva |
| --- | --- |
| Evidencia suficiente | La condición examinada se acredita conforme a criterios aprobados. No significa cobertura final del perfil automáticamente. |
| Evidencia insuficiente | Falta información necesaria para acreditar una condición obligatoria: no confirmar transición a V1_VERIFIED; conservar clasificación previa, sin evento de transición nuevo. |
| Incoherencia detectada | Contradicción observable: tampoco confirmar transición; sin mutación o evento parcial y sin bloqueo automático. |

Son distinciones conceptuales, no nuevos estados/enums ni cambios LegacyAuditStatus.
La ausencia de un evento antiguo no prueba por sí sola corrupción. No fabricar
XPEvent, historia de puntos, snapshots, procedencias o cronología por PK para
completar lagunas. A3.1 COMPATIBLE no acredita suficiencia V1_VERIFIED.

**Pendiente expresamente:** política exacta sobre qué lagunas podrían admitirse
bajo garantías alternativas válidas, si existiese. No se aprueba excepción general
para clasificar perfiles de historia incompleta. Una insuficiencia concreta no
borra el valor de otras observaciones válidas; tampoco habilita avance cuando
falta una prueba obligatoria. BLOCKED es otra operación con incidencia,
autorización y condiciones propias; no se ejecuta automáticamente ante diagnóstico.

### 9.3. Procedencia y creación confiable · A3.6.3-NATIVE-01

- LEGACY_V1 requiere procedencia acreditada y evaluación de historia observable,
  con lagunas tratadas explícitamente.
- NATIVE_V1 requiere alta confiable y verificada conforme a su proceso creador.
  No exigir historia antigua inexistente a un nativo recién inicializado.

No inferir NATIVE_V1 de cero XP, fecha reciente, nivel inicial o historial vacío.
No convertir automáticamente perfiles existentes ni cambiar procedencia confirmada.
[S2-A](../../apps/ecomotor/initialization.py) garantiza aspectos concretos de creación
atómica de perfil/stats y configuración inicial; no es un mecanismo universal de
certificación retrospectiva de procedencia. Acreditación exacta del proceso
creador y sus dependencias **todavía pendientes**. Se mantiene la matriz de altas
A3.3; esta precisión no autoriza clasificaciones reales ni un origen por defecto.

### 9.4. Alcance temporal · A3.6.3-TIME-01

Una verificación confirmada acredita las condiciones requeridas **en el momento
de su transacción**. Una concesión S3 posterior no revoca o altera automáticamente
clasificación, revisión o eventos confirmados. No garantiza coherencia indefinida.
Transiciones posteriores requieren sus propias condiciones de evidencia vigente
y autorización; un diagnóstico posterior no deduce BLOCKED. Bloqueo siempre
mediante operación autorizada con sus condiciones, sin automatismos por recompensas.

Se conserva A3.3: revisión esperada, identidad por clave, evento histórico primero
y replay sin nueva elegibilidad. Para nueva operación, lector dentro de transacción
D-19 controlada por servicio, evidencia actual comprobada en esa misma frontera,
alias confiable/IMMEDIATE/timeout 5 s y política/evento atómicos o rollback íntegro.
A3.2 permanece separado y sin extracción anidada. S3 V1 sigue único escritor XP.

### 9.5. Dependencias y pruebas futuras

Abiertos: cobertura final suficiente V1_VERIFIED; política de lagunas admisibles;
completitud XP y reconstrucción de puntos si falta historia; aplicabilidad histórica
de catálogos/atributos de etapas; historia de dominio/especializaciones/rangos;
procedencia confiable; consultas/contexto del lector; A3.5/Core (identidad,
autorización, ciclo de vida, retención, privacidad y on_delete); Henry/Duckies,
inventario y referencias de integración. [Consulta Core/P5](ecomotor-classification-core-boundary-v1.md)
intacta, sin respuestas o permisos inventados. No se cierra dependencia por inferencia.

Tests futuros: datos locales coherentes y evidencia obligatoria suficiente; XPEvent
antiguos ausentes frente a eventos observados incoherentes; stats ausentes/inválidas;
progreso incompatible con catálogo aplicable; gastos individuales coherentes sin
saldo histórico acreditable; ausencia legítima/inconsistente de especialización;
legacy/nativo con procedencia acreditada; XP posterior a verificación confirmada;
nueva transición con evidencia obsoleta; replay sin nueva elegibilidad; rechazo
sin mutaciones/reparaciones/eventos parciales; regresión S3 V1. No se crean ni
ejecutan nuevos tests Django, modelos, lector o servicio en esta PR documental.

## 10. A3.6.4 · Lagunas históricas y garantías alternativas

A3.6.4-GAP-01, ALT-01, GATE-01 y TRACE-01, aprobadas internamente por Equipo 5
en 02C y documentadas el 20/10/2026 sobre develop
`8790ac7ddd9703d2d3686038e87f01d814358419`. Continúan A3.6.1–A3.6.3.
DAR3 conserva autoridad funcional; estas decisiones técnicas no son requisitos
literales nuevos ni ratificaciones de Óscar/Core o Henry.
[Registro](../decisions.md#a364--lagunas-históricas-y-garantías-alternativas--20102026)
y [pendientes](../pending-decisions.md#24-a364--admisibilidad-y-equivalencias-pendientes).

**Marco conceptual aprobado, no lista concreta de lagunas admisibles ni cierre de
suficiencia V1_VERIFIED.** No se implementan modelos, lector, servicios o clasificación.

### 10.1. Evaluación individual · A3.6.4-GAP-01

Para cada laguna identificar por separado: condición que se pretende acreditar,
información histórica ausente, evidencia directa realmente disponible, posibles
fuentes alternativas existentes o candidatas (distinguirlas) e impacto sobre la
suficiencia de la operación. No extrapolar un diagnóstico a toda la historia.

| Situación conceptual | Distinción y ejemplo |
| --- | --- |
| Ausencia legítima de eventos | Nativo sin recompensas previas, con procedencia acreditada: la ausencia no prueba corrupción. Tampoco acredita por sí sola que sea nativo. |
| Historial incompleto | Legacy con XP anterior a los XPEvent observados: datos actuales no demuestran la cadena completa ni su origen. |
| Evidencia obligatoria insuficiente | Evolución antigua sin versión/atributos históricos del catálogo: si esa información es necesaria para una condición obligatoria, no darla por acreditada usando el catálogo vivo. |
| Contradicción verificable | EvolutionEvent cuya causa XP pertenece a otro perfil: contradicción causal observada, distinta de una mera ausencia de historia. |

Las situaciones se evalúan según condición, alcance y procedencia; no son nuevos
enums o estados. No inferir cronología por PK ni reconstruir eventos no persistidos.
A3.1 COMPATIBLE conserva su alcance limitado y no equivale a V1_VERIFIED.

### 10.2. Equivalencia de garantías · A3.6.4-ALT-01

Una garantía alternativa solo podría sustituir evidencia ausente si acredita
**la misma condición obligatoria** con garantías suficientes y expresamente
admitidas. Evaluar identificación inequívoca del perfil, procedencia confiable,
alcance/cobertura, vigencia o aplicabilidad temporal acreditada, coherencia con
registros observados e independencia probatoria suficiente. No usar circularmente
el estado actual para certificar su propia procedencia. Fuente validada y
autorizada conforme a contratos propietarios aplicables.

**Hipótesis por estudiar, no fuentes históricas constatadas ni equivalencias aprobadas:**

| Laguna | Posible garantía alternativa por estudiar |
| --- | --- |
| XP antigua | Saldo inicial históricamente acreditado y trazabilidad posterior suficiente. |
| Puntos | Saldo inicial autorizado y movimientos posteriores acreditados. |
| Evoluciones | Catálogo histórico verificable y causas de evolución correspondientes. |
| Especializaciones | Pruebas confiables de selección y progreso. |
| Procedencia del perfil | Evidencia del proceso de creación original. |
| Duckies/inventario | Pruebas acordadas con Henry y propietarios de esos datos. |

La tabla no afirma que existan copias históricas, snapshots, versiones de catálogo
o registros confiables. Primero comprobar disponibilidad real, procedencia y
alcance; no aprobar equivalencia por parecido, declaración sin respaldo o solo
estado actual. Definir criterios específicos por condición sigue pendiente.

### 10.3. Puerta de avance · A3.6.4-GATE-01

Para operación nueva hacia V1_VERIFIED:

- Si todas las condiciones obligatorias están acreditadas y se cumple el resto
  de requisitos, la evaluación puede continuar; no es confirmación automática.
- Si una laguna no afecta a ninguna condición obligatoria conforme a política
  aprobada, registrar el límite sin convertirlo automáticamente en impedimento.
- Si falta una condición obligatoria y no hay garantía alternativa expresamente
  admitida y suficiente, rechazar transición. Sin política aprobada para esa prueba
  ausente, rechazo seguro.
- Si hay incoherencia impeditiva, rechazar sin reparación automática.

**No excepción genérica para perfiles de historia incompleta.** La política exacta
de admisibilidad continúa pendiente: este marco no la sustituye. Rechazo conserva
estado, revisión e historial de clasificación sin nuevo evento confirmado.
No crear evento BLOCKED automáticamente: bloqueo es otra operación con incidencia,
autorización y condiciones propias. Sin inventar datos o activar migraciones.

### 10.4. Justificación y trazabilidad · A3.6.4-TRACE-01

Uso futuro de garantías alternativas justificable mediante información conceptual:
condición evaluada, laguna, fuente utilizada/procedencia, alcance, vigencia o
aplicabilidad, resultado motivado y limitaciones restantes. Distinguir evidencia
examinada de decisión autorizada; una fuente aportada no es autorización.

No se aprueban campos, modelos, tablas, firmas, formatos físicos o retención por
esta trazabilidad. Representación técnica, privacidad, conservación e identidad
del operador permanecen sujetas a A3.5/Core. No exponer datos ajenos, claves de
operación o historiales innecesarios.

### 10.5. Vigencia transaccional y dependencias

A3.3 conserva revisión esperada, idempotencia por clave, evento histórico primero
y replay sin nuevas comprobaciones de elegibilidad. Lector A3.6.2 dentro de la
transacción controlada por servicio: alias confiable, D-19/BEGIN IMMEDIATE/timeout
5 s, evidencia vigente en la misma frontera que confirma política/evento, rollback
íntegro y sin I/O externo. A3.2 separado sin anidación; reglas puras intactas.

Fuentes externas potenciales requieren procedimiento de acreditación y vigencia
compatible con esa frontera, aún por concretar con propietarios. No autorizar
consultas externas dentro de transacción ni considerar suficiente cualquier
certificación antigua. No se altera el alcance temporal de A3.6.3-TIME-01.

Abiertos: lista concreta de lagunas admisibles; equivalencias específicas por
condición; fuentes realmente disponibles/confiables; cobertura final V1_VERIFIED;
procedencia acreditada LEGACY_V1/NATIVE_V1; API/consultas del lector; A3.5/Core
(identidad, autorización, ciclo de vida, retención, privacidad/on_delete); evidencia
Duckies/inventario/consumidores con Henry. [Consulta Core/P5](ecomotor-classification-core-boundary-v1.md)
intacta, sin acuerdos inferidos. Las aclaraciones funcionales de PR #61 no
resuelven estas dependencias técnicas. S3 V1 continúa como único escritor XP.

### 10.6. Pruebas futuras

Ausencia legítima; XP antigua incompleta; alternativa equivalente/autorizada frente
a fuente no confiable, circular o insuficiente; cobertura temporal incompleta;
contradicción con datos persistidos; evolución causada por XP ajena; evidencia
obsoleta antes de confirmación; rechazo sin eventos parciales o cambios de
clasificación; replay sin nueva elegibilidad; ausencia de backfill/reparaciones/
migraciones/activación; regresión S3 V1. Casos hipotéticos no ratifican fuentes o
políticas reales. No se implementan ni ejecutan tests Django en esta PR documental.
