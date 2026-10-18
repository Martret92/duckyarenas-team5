# Arquitectura del Equipo 5 · Estado integrado y Rewards v0 candidato

## 1. Estado y fuentes

**Actualización DOC-S14-A:** develop
`e401c33045b4f1b4c8621c54c21757483769b56b` integra S13-A1 puro (#47).
El [cambio de especialización S14-A](contracts/ecomotor-specialization-switch-v1.md)
está aprobado internamente en 02B, sin implementar: una activa, progresos de las
cinco conservados, primera activación en cero, retorno sin reset y cambio en Actual
sin alterar XP histórica, nivel, etapa, stats o recompensas. Servicio candidato
transaccional separado de S11-A, estado esperado y D-19; sin evento físico ni
replay histórico completo. Antes de implementar debe precisarse la compatibilidad
de S11-A con múltiples progresos coherentes y la repetición frente al estado esperado.
S13-A2/persistencia de rangos pendientes; no evaluación para conceder ascensos.
La recompensa tardía de una especialización ya inactiva requiere revisar S12-A-02
y evidencias con Rewards/Core, sin excepción aprobada. P5/P7 y conservación
siguen abiertos; DomainXPEvent conceptual y Rewards F2-A bloqueado.
Los cortes anteriores sin implementación de S13-A1 son antecedentes documentales.

**Actualización DOC-S13-A1 · 18/10/2026:** base develop
`5d36778449e7c796e2770ddfdb97f25e8f8b280f`, con DOC-S12-A integrado (#45).
La [arquitectura de rangos y contrato candidato del evaluador puro](contracts/ecomotor-ranks-evaluator-v1.md)
registra S13-A-01…07 y precisiones S13-A1 aprobadas internamente por Jaime/02B,
sin implementación. Evaluar el siguiente rango no confirma un ascenso; políticas
versionadas y evidencias verificadas no equivalen a autorización global.
Se conserva el progreso de las cinco especializaciones al alternar y se adoptan
importes independientes de XP general/dominio (opción B), sin baremos oficiales
ni servicio de cambio. Las referencias previas a S13-A sin diseño son antecedentes.
S11-A sigue implementado; S12-A conceptual, persistencia de rangos/DomainXPEvent,
autorización, cambio de especialización y recompensas tardías siguen pendientes.
P5/P7 abiertos, Rewards F1-A implementado, F2-A bloqueado y Rewards v0 candidato.
No se modifica el esquema físico ni se aprueban nuevas relaciones/on_delete.

**Actualización DOC-S12-A · 18/10/2026:** develop
`84f809df43c7db9b438a6541a298214ce8d97b50` incluye S8-A (#40), UI-A (#41),
S9-A (#42), S10-A (#43) y S11-A (#44). S11-A implementa selección inicial, no
concesión positiva de dominio. [S12-A](contracts/ecomotor-domain-xp-v1.md) está
aprobado conceptualmente por 02B, sin implementación ni persistencia autorizada.
Rewards F1-A está implementado (#38); F2-A sigue bloqueado por DOC-6 y Rewards v0
continúa candidato global. Las pausas/revisiones de los cortes anteriores son
antecedentes históricos, no estados vigentes. Esta PR solo actualiza documentación.

**Corte DOC-6 · 18/10/2026:** develop `5a4e079` incluye Fase 1 Rewards por
[PR #38](https://github.com/Martret92/duckyarenas-team5/pull/38):
[tipos](../apps/ecomotor/reward_types.py),
[identidad/huella](../apps/ecomotor/reward_identity.py) y
[evaluación pura](../apps/ecomotor/reward_rules.py), sin ORM ni efectos reales.
Jaime aprueba internamente la [arquitectura persistente local F2-A](decisions.md#doc-6--arquitectura-persistente-rewards-f2-a--18102026),
**sin implementación** ni ratificación de Core/Henry/Fernando/juegos. Los cortes
DOC-1…DOC-4 siguientes son antecedentes fechados; sus menciones a Rewards sin
implementar no describen el núcleo puro ya integrado. El contrato global v0
permanece candidato; F2-A y process_reward todavía no existen.

DOC-4 (18/10/2026), sobre develop `be9e7aa` tras PR #35, registra
[T1–T8 aprobadas internamente por Jaime](decisions.md#doc-4--diseño-técnico-rewards-v1--t1t8--18102026)
y el [diseño técnico candidato](contracts/rewards-v0.md#10-diseño-técnico-interno--doc-4).
SHA-256/canonicalización, integración futura S3 y tipos de evaluación se distinguen
de RewardEvent/RewardLimitUsage físicos candidatos. El contrato global sigue v0;
[conservación, contratos y transporte](pending-decisions.md#7-validación-residual-del-diseño-técnico--doc-4)
condicionan las fases posteriores. No se implementa Rewards ni se modifica S1–S7-A;
S8-A continúa aprobado y pausado.

DOC-3 (18/10/2026), sobre develop `9495bda` tras PR #34, registra los
[principios R1–R8 aprobados internamente por Jaime](decisions.md#doc-3--arquitectura-rewards-v1--acuerdos-internos-de-parte-a--18102026).
Orientan Parte A; el [contrato Rewards v0](contracts/rewards-v0.md) conserva su
versión y estado global candidato, con [validaciones residuales](pending-decisions.md#3-validación-conjunta-de-rewards-v0).
No hay ratificación conjunta A/B/C/Core/juegos ni implementación de Rewards;
S1–S7-A no cambian y S8-A sigue aprobado y pausado.

DOC-2 (18/10/2026), sobre develop `33b4e87` tras PR #33, añade la
[matriz de procedencia y acuerdos](contracts/integracion-equipo5-v0.md#0-matriz-de-procedencia-y-acuerdos--doc-2)
y el [índice común ERD/diccionarios PR07](ERD.md). El corte de implementación
§2.1 sigue vigente: DOC-2 no integra funciones ni cambia los contratos S1–S7-A.
Las fuentes adicionales aportan respuestas y decisiones atribuidas, no aprobación
global: permanecen abiertos R-01, fuente física del saldo con Core, tarifas,
penalizaciones Escape y contratos compartidos. Rewards v0 continúa candidato y
S8-A aprobado y pausado. La matriz identifica diferencias de fecha/autoridad;
los antecedentes de las dailys siguientes no se reinterpretan retrospectivamente.

Consolidación documental de los acuerdos internos del 08/10/2026 y las aclaraciones
del 09/10 y 13/10. Óscar expresó conformidad verbal general con el documento
funcional leído, sin identificar su versión exacta ni aprobar diseños técnicos
detallados. **Rewards v0 sigue siendo una propuesta técnica aceptada provisionalmente
como base de trabajo, pendiente de validación conjunta.** No hay aprobación global
de Óscar, Core, B/C o juegos del ERD V2, la estructura física de D-21 o los contratos.

| Fuente | Procedencia y autoridad |
| --- | --- |
| `DAR3_ (1).pdf`, §§9–10, pp. 48–53 | Consulta directa del alcance general, servicio común de recompensas y mínimo de intercambio. DAR3 no asigna individualmente A/B/C. |
| `11201_PR07_proyecto Ducky Arenas.pdf`, pp. 4–5, 10–11 y 17 | Consulta directa de proceso/evaluación: diseño antes del ORM, cardinalidades, borrado, permisos, tests y evidencias Git. Persiste el conflicto User/auth bajo D-17. |
| `DuckyEcomotor.pdf`, pp. 1–7 | Consulta directa: gestor central, reglas configurables, Bank/Shop, siete etapas y especializaciones en Actual. Su XP externa entra en tensión con la rectificación verbal del 09/10. |
| `DAR_formulas.pdf`, pp. 7–12 y 18 | Consulta directa de cálculo de acciones, consolidación, REST/WebSockets y ejemplo de stats; no se adoptan automáticamente fórmulas, código u ORM. |
| `DAR_DuckyClash.pdf`, p. 8; `DuckyTraining.pdf`, p. 1; `DuckyEscape.pdf`, pp. 1–2 | Consulta directa de tabla de stats por rol, repetibilidad/límite diario y premios parciales/finales. El Escape local no se identifica como la nueva versión consolidada mencionada en la reunión. |
| Dailys del 06, 07, 08 y 09/10/2026 | Notas y conclusiones: aclaraciones del profesor, propuestas de participantes y asuntos pendientes; no aprobación global de modelos o contratos. |
| Acta de la daily del 13/10/2026 y aclaraciones verificadas comunicadas por Jaime | Solo los puntos contrastados de conformidad, controlador antiguo, autonomía, LMS/Bank y recursos gráficos; las demás notas no se elevan a acuerdos. |
| Acuerdos internos comunicados del 08/10 | Reparto y organización objetivo registrados en D-20/D-21; no se infieren de comentarios de la reunión. |
| [Decisiones](decisions.md), [ERD](erd/ecomotor.md) y [Rewards v0](contracts/rewards-v0.md) | Se distinguen decisiones D vigentes, aceptación interna condicionada de Parte A y contrato candidato. |

DAR3 es la fuente principal de requisitos y responsabilidades. PR07 es guía de
desarrollo, metodología, evidencias y evaluación: en la daily del 06/10/2026 se
aclaró que su plan diario era una guía, no un calendario literal obligatorio.
Los PDFs posteriores amplían o precisan especificaciones; las aclaraciones
explícitas de las dailys pueden rectificarlas. Ante contradicción se documenta
el conflicto antes de fijar una interpretación. La documentación del repositorio
no constituye aprobación del profesor. Las cantidades ilustrativas no son
valores oficiales.

Se distinguen requisitos documentales, aclaraciones/rectificaciones del profesor,
propuestas de participantes, acuerdos internos, propuestas técnicas candidatas
no aceptadas conjuntamente y decisiones pendientes de validación.

## 2. Decisiones vigentes y organización objetivo

D-20 fija Jaime/A, Henry/B y Fernando/C. D-21 acuerda cuatro apps de dominio,
conservando `apps.users`. D-13 permanece como propuesta histórica de otro reparto;
D-14…D-16 no quedan confirmadas automáticamente.

En la mini daily del 06/10/2026 se propuso la organización de apps y quedó
pendiente de revisión. En la daily del 08/10/2026 Óscar indicó una revisión
por encima del documento y que faltaba examinarlo con más detalle. D-20/D-21
fueron aceptados por Jaime, Henry y Fernando para organizar el trabajo. No se
reabre ese reparto: siguen pendientes la revisión física de apps, las interfaces
A/B/C y los requisitos de Óscar/Core y de los equipos consumidores.

**Antecedente del 16/10/2026 (`05d65f2`, PR #25):** el corte tras S1/S1.1,
Día 4 y Admin aún no incluía S2-A–S7-A. Esa descripción queda superada por §2.1;
no se reescriben las decisiones de aquellos incrementos. D-21 conserva cuatro apps
objetivo, sin acreditar integración de Duckies, Bank o Shop. D-18 mantiene
rutas/labels y D-11 la ubicación de perfiles. Conservación, contratos físicos y
reconciliación de migraciones A/C siguen pendientes.

D-05/D-09/D-10/D-17 conservan User estándar y ausencia de autenticación local.
Se utiliza `settings.AUTH_USER_MODEL`. **Óscar es el interlocutor de Core/Equipo 0**
para User, autenticación, JWT, integración y conservación; no se da por resuelto
el conflicto de PR07 ni se atribuye una política de borrado a ejemplos del PDF.

| Área / app objetivo | Responsable interno | Autoridad y límite |
| --- | --- | --- |
| Parte A · `apps.ecomotor` | Jaime | XP histórica, nivel, etapas, evolución, especializaciones, stats/puntos e historiales. Coordina Rewards y reglas; solicita efectos a sus propietarios. |
| Rewards · capacidad de Ecomotor | Jaime, con revisión A/B/C | Entrada lógica de hechos recompensables, evaluación, deduplicación y trazabilidad completas; no exige otra app. |
| Parte B · `apps.duckies` | Henry | Duckies, identidad de objetos, posesión, cantidades, concesiones, consumos, avatar, compatibilidad y equipamiento. Inventory y Equipment son capacidades de Duckies. |
| Parte C · `apps.bank` | Fernando | Única fuente de verdad de wallet, saldo y movimientos auditables de Duki Coins. Créditos, débitos y reservas si se incluyen apuestas. |
| Parte C · `apps.shop` | Fernando | Catálogo comercial, precios, disponibilidad y compras; coordina cargo con Bank y entrega con Duckies. |
| `apps.users` / integración Core | Equipo 5 con Óscar/Core | Perfiles actuales; identidad global, autenticación y JWT pertenecen a Core. |
| Juegos y otros emisores | Sus equipos | Validan hechos/resultados en su dominio; no son autoridad sobre XP, monedas o stats canónicos. |

El catálogo comercial de Shop se distingue de la identidad/posesión de objetos de
Duckies. Cada servicio escribe su estado; la coordinación no autoriza escrituras
directas en modelos de otra parte.

### 2.1. Estado vigente de implementación · DOC-1

Corte verificado el 18/10/2026: `origin/develop` en
`b42cb5fdd5c4509670a337c1c79e260714c78c9f`. PR #32 es la última integrada;
las PR de la tabla están fusionadas y sus commits pertenecen a esta baseline.
Esto acredita implementación local, no aprobación externa ni integración global.
El corte DOC-1 se conserva como antecedente. La baseline actual de S9-A es
`b1b25cd8d67f45ede8de6b6642cb2eae29b6c1e8`: S8-A está integrada mediante
PR #40 y UI-A mediante PR #41; el historial S9-A se incorpora en su rama para revisión.

| Incremento | PR integrada | Implementación y contrato local |
| --- | --- | --- |
| S1/S1.1 | [#22](https://github.com/Martret92/duckyarenas-team5/pull/22) | [progression.py](../apps/ecomotor/progression.py): resolve_level, resolve_stage y calculate_progression puros, sin ORM; [contrato S1](decisions.md#s1--cálculos-puros-de-progresión--aceptación-interna-provisional), trazado por [#26](https://github.com/Martret92/duckyarenas-team5/pull/26). |
| Día 4-A/B | [#23](https://github.com/Martret92/duckyarenas-team5/pull/23), [#24](https://github.com/Martret92/duckyarenas-team5/pull/24) | Catálogos, perfil, stats, XPEvent, EvolutionEvent y progreso de especialización; [ERD y migraciones](erd/ecomotor.md#11-integración-estructural-vigente--día-4). |
| Día 5 | [#25](https://github.com/Martret92/duckyarenas-team5/pull/25) | Admin solo para superusuarios; catálogos editables únicamente sin perfiles, progreso/historiales de consulta y borrados prohibidos. S7-A añade su evento como consulta. |
| S2-A | [#27](https://github.com/Martret92/duckyarenas-team5/pull/27) | [Inicialización](contracts/ecomotor-initialization-v1.md) atómica e idempotente de perfil/stats para User existente, sin signals ni reparación legacy. |
| S3 | [#28](https://github.com/Martret92/duckyarenas-team5/pull/28) | [Concesión XP](contracts/ecomotor-xp-v1.md): cálculo S1, puntos de niveles nuevos y todas las evoluciones en una transacción; replay histórico local. |
| S4-A | [#29](https://github.com/Martret92/duckyarenas-team5/pull/29) | [Consultas](contracts/ecomotor-progress-queries-v1.md) de progreso e historial persistidos, solo lectura; sin snapshot único entre consultas concurrentes. |
| S5-A | [#30](https://github.com/Martret92/duckyarenas-team5/pull/30) | [Web personal](contracts/ecomotor-progress-web-v1.md) GET/HEAD, login_required e identidad desde request.user; URL local ecomotor:progress, sin montaje en config/urls.py. |
| S6-A | [#31](https://github.com/Martret92/duckyarenas-team5/pull/31) | [Configuración/diagnóstico](contracts/ecomotor-configuration-v1.md): JSON explícito y check_ecomotor_readiness; no activa el candidato ni configura el servidor. |
| S7-A | [#32](https://github.com/Martret92/duckyarenas-team5/pull/32) | [Asignación](contracts/ecomotor-stat-allocation-v1.md) solo en Actual, coste 1:1, evento/snapshots idempotentes y migración 0005 aditiva protegida. |

El esquema local de Parte A tiene **nueve entidades**: las ocho del V2 histórico
más StatAllocationEvent. Sus modelos están en apps.ecomotor (ocho) y apps.users
(UserProfileEcomotor); UserProfileBank no forma parte de ese recuento.
La primera selección de especialización S11-A está integrada (#44). No hay servicio
de XP de dominio positiva, coordinación transaccional Rewards, economía, objetos
o juegos integrado en este corte de Parte A. Fase 1 pura sí está integrada
por PR #38, según el corte DOC-6 de §1. Las flechas de §5 representan arquitectura
objetivo candidata.

INITIAL_CONFIGURATION continúa en None. Existen carga JSON y diagnóstico técnico,
pero faltan valores autorizados, instalación real y política histórica de cambios
(P8/V2-A28). TECHNICALLY_READY no equivale a aprobación funcional. La consulta básica
S4-A/S5-A no depende de configurar nuevas concesiones.

S8-A está **integrada mediante PR #40**: adaptador web GET/POST para asignar
puntos exclusivamente mediante S7-A, autenticación Django, CSRF, request.user
e idempotencia. UI-A (PR #41) comparte plantilla base y CSS local entre páginas.
Véase el [contrato S8-A](contracts/ecomotor-stat-allocation-web-v1.md).

El repositorio contiene tests de modelos/migraciones, Admin, servicios, consultas,
HTTP y concurrencia SQLite file-backed. Regresión histórica comunicada en DOC-1:
**407 tests correctos**. DOC-1 revisa código, contratos y procedencia Git, sin volver a ejecutar
la suite ni comprobar instalaciones o datos reales.

## 3. Requisitos funcionales y límites de V2

La XP histórica es acumulativa y no decreciente. Resultado o XP provisional de
partida, recompensa evaluada y XP consolidada son magnitudes distintas.
Penalizaciones de una partida no descuentan XP histórica ya concedida.

Las nueve épocas iniciales de DAR3 son antecedente del diseño posterior de
siete etapas, mantenido como dirección V2 candidata sin aprobación global de
sus modelos, umbrales o constraints.
Las siete etapas son **Prehistoria, Griega, Romana, Renacentista, Contemporánea,
Siglo XX y Actual**. Nivel y etapa son conceptos distintos. Umbrales, recompensas
y desbloqueos son configurables; evolución automática no implica equipamiento
automático. Las especializaciones actuales son **Developer, Ciberseguridad,
Sistemas, Data y Gamer**, dentro de Actual. Data / Data & IA y los códigos
técnicos requieren normalización con los consumidores.

Los stats son **ATK, DEF, LOG, SPE, VEL e INT**. Parte A distingue base persistente,
puntos disponibles y valores efectivos. El ERD V2 histórico aceptó ocho entidades,
niveles independientes y transiciones múltiples; [erd/ecomotor.md](erd/ecomotor.md)
distingue ese antecedente del esquema vigente de nueve entidades tras S7-A.
Ningún ejemplo del PDF aprueba iniciales,
límites o tablas nuevas.

DAR3 describe seis piezas principales por época obtenidas mediante progreso y
misiones, diferenciadas de complementos estéticos, y conserva progresos y conjuntos
anteriores tras evolucionar. Mantiene inventario, compatibilidad, historiales y
Museo Ducky. Su adaptación de nueve épocas a las siete etapas V2 provisionales
requiere contraste; no impone seis campos físicos por etapa.

**Antecedente R-01 · 15–16/10/2026.** Desbloquear, conceder/poseer, equipar
y elegir apariencia son operaciones distintas. R-01 sigue en estado mixto:
Jaime recordó entrega y equipamiento
automáticos; no consta aceptación inequívoca de Henry del autoequipamiento.
La entrega automática sin equipamiento del ERD global es una propuesta, no un
cierre aceptado. El 15–16/10 Jaime y Henry acordaron proponer a Óscar seleccionar
libremente apariencias completas de cualquier época desbloqueada; no adoptaron
esa política. Obtención, variantes comprables y comportamiento al saltar etapas
siguen pendientes en [pendientes](pending-decisions.md).
La lista de nueve épocas de DAR3 no se sustituye por una propuesta interna;
el mínimo local V2 conserva siete etapas provisionalmente. INITIAL del V1 no
se convierte en invariante actual. UserSpecializationProgress sin rank conserva
XP de dominio independiente; fuentes, rangos y obligatoriedad sin validación global.

### 3.1. Vestimentas históricas · Propuesta DOC-5

Criterio propuesto por E5 el 18/10/2026, recogido en CORE-07, E5-02 y B-06 del
documento compartido y en el [registro DOC-5](decisions.md#doc-5--criterio-funcional-propuesto-de-vestimentas-históricas--18102026).
Es posterior a R-01: lo precisa como propuesta, sin cerrar su aceptación técnica
ni convertirlo en aprobación del profesor.

| Concepto | Comportamiento funcional propuesto / autoridad |
| --- | --- |
| Evolución | Ecomotor determina la transición; evolución automática por umbral no implica por sí sola adquisición o equipamiento. |
| Adquisición | E5 propone obtener el conjunto completo de la nueva época al evolucionar, pendiente de compatibilidad con progreso/misiones DAR3. |
| Posesión | Duckies conservaría todos los conjuntos completos anteriores ya obtenidos. No se decide si conjunto equivale a uno o varios objetos. |
| Equipamiento | E5 propone equipar automáticamente el conjunto nuevo; no consta aprobación de Óscar ni aceptación técnica inequívoca de Henry de todos sus detalles. |
| Selección de apariencia | El usuario podría volver a equipar cualquier conjunto anterior obtenido, incluso en épocas intermedias; no conjuntos de épocas futuras todavía no alcanzadas. Duckies controla equipamiento/apariencias. |

DAR3, pp. 3 y 48, conserva las seis piezas principales por época, obtención por
progreso y misiones, conservación del progreso/conjuntos y nueve épocas incluida
Era Espacial. Debe aclararse cómo encajan esos requisitos con las siete etapas
provisionales y la propuesta de conjuntos completos; no se eliminan piezas ni
se adopta una lista oficial nueva. CORE-07, B-06, P6 y R-01 siguen pendientes con
Óscar; identidades, idempotencia, adquisición, equipamiento y recuperación deben
acordarse con Henry antes de implementar. [Preguntas y bloqueos](pending-decisions.md#8-vestimentas-históricas--propuesta-doc-5).
No hay implementación, modelos nuevos o contratos definitivos en DOC-5.

## 4. Notas y conclusiones de las dailys

| Daily / tema | Contenido y categoría | Estado y tratamiento |
| --- | --- | --- |
| 06, 07 y 09/10/2026 · código común | Se habló de funciones existentes para recompensas, puntos y monedas, de compartir código y de evitar duplicar funcionalidades. | Antecedente de coordinación. El 13/10 se aclaró que el controlador antiguo sencillo de DuckyCoins no debe esperarse ni reutilizarse obligatoriamente; Wallet/saldo canónicos, autorizaciones y contratos siguen pendientes. No conocemos firmas ni modelos verificados del código anterior. |
| 09/10/2026 · Ecomotor | Óscar indicó centralización funcional de recompensas y estadísticas; el emisor valida su actividad. | Aclaración funcional, no aprobación de modelos, funciones o payloads. |
| 09/10/2026 · XP externa | Óscar planteó reservar XP a juegos y monedas a actividades externas, rectificando la dirección anterior. | Conflicto con Ecomotor pp. 1–2 y 6: falta confirmar XP histórica/de dominio, actividades, vigencia, usuarios/recompensas existentes y configuración futura. No se autoriza borrar XP ni convertir automáticamente todas las actividades externas en premios sin XP. |
| 09/10/2026 · stats | Antes de Actual se habló de estadísticas determinadas por rol; en Actual se planteó distribuir o editar puntos. | Aclaración parcial: iniciales, presupuesto y límites pendientes. No adoptar todos a 5, tabla de Clash o suma de 45 como valores oficiales; tampoco cambios/reinicio de especialización. |
| 09/10/2026 · cursos | Se desarrollaron ejemplos de objetos temáticos y posibles puntos adicionales. | Dirección apoyada, no regla cerrada. Condiciones, cantidades, efectos y V1 pendientes. Bonificaciones diarias de XP por cursos fueron propuestas discutidas, no confirmadas. |
| 09/10/2026 · Training | Se reiteraron XP por repeticiones válidas y una moneda por juego/día. | Conforme al PDF; acceso, límite de monedas e idempotencia por sesión son cuestiones distintas. Moneda para toda la vida fue propuesta de participante no aceptada. |
| 09/10/2026 · Escape | Se indicó XP por stages completados que se conserva aunque no termine la partida y premio final independiente. | Stage no equivale a habitación. La ausencia de monedas por stage no elimina necesariamente premios por habitación. Versión consolidada posterior y consolidación parcial/final pendientes. |
| 09/10/2026 · Quiz | Tiempo, aciertos, estadísticas y resultados participan en el cálculo. | Aclaración funcional; cantidades ilustrativas no son premios obligatorios y el contrato sigue por validar. |
| 09/10/2026 · Clash | Resultado validado y participantes; Bank reserva fondos de ambos al aceptar un duelo con apuesta. | Instrucción condicional a apuestas. DAR3 p. 42 contempla primera entrega sin ellas; V1, liberación/liquidación y cancelación pendientes. |
| 09/10/2026 · evaluación | Se vinculó el 19/10 a exámenes/documentación práctica y se planteó codificar la semana siguiente. | Orientación formativa, no fecha final de todo DuckyArenas ni autorización del ORM. |
| 13/10/2026 · conformidad funcional | Óscar confirmó lectura y valoración general favorable del documento enviado por Jaime. | La vinculación con el criterio funcional enviado el 07/10 es razonable por contexto, sin versión exacta identificada. No aprueba ERD V2, D-21 física, Rewards v0, modelos, migraciones ni interfaces. |
| 13/10/2026 · controlador antiguo | Óscar describió un controlador sencillo para incrementar DuckyCoins y aclaró que no es necesario esperar ni reutilizarlo obligatoriamente. | Aclaración limitada a ese componente, no desaparición de todos los servicios anteriores. Consultar código previo es opcional; Core, Wallet/saldo canónicos, movimientos, autorización, idempotencia, concurrencia y contratos económicos siguen abiertos. |
| 13/10/2026 · autonomía | Óscar dejó margen de implementación y pidió comunicar dudas; el equipo expuso avances y coordinación pendiente. | Se puede continuar desarrollando, sin validación técnica detallada. Las ocho interfaces de Henry siguen como propuestas pendientes de consenso A/B/C. |
| 13/10/2026 · LMS/insignias/Bank | Óscar mencionó corrección automática en LMS, insignias, euros, cotización de DuckyCoins y posible relación futura con Bank. | Expectativa de integración futura, sin fórmula, conversión, cantidades, XP externa, reglas, modelos, endpoints ni inclusión obligatoria en V1. P1 no queda resuelta ni reabierta. |
| 13/10/2026 · recursos gráficos | Óscar mostró y publicó en Classroom materiales de ataques, escudos, relojes, botiquines, pócimas y comida. Henry comunicó internamente haberlos localizado. | Disponibilidad, no aprobación del catálogo. Inspección pendiente; algunas imágenes requieren separar objetos y normalizar tamaños. Códigos, precios, efectos, duraciones, consumo, compatibilidad y V1 no están decididos. |

Cambio de rol por pago/objeto, freemium, reducción a Quiz y DukiStats 2.0 son
propuestas de participantes. No justifican aplazar globalmente RPG o WebSockets,
ni prueban aprobación del ERD. La revisión superficial comentada por Óscar en
la daily del 08/10/2026 no equivale a aprobación detallada.
La preferencia de compra por rol comentada en la daily del 09/10/2026 no es una
restricción comercial definitiva.

## 5. Flujos y Rewards v0 candidato

```mermaid
flowchart LR
    Core["Core / Óscar: identidad y JWT"] -. autorización .-> Eco["Ecomotor / Rewards"]
    Games["Juegos: hechos validados"] -->|actividad y destinatario| Eco
    External["Actividades externas"] -->|alcance pendiente| Eco
    Other["Otros módulos"] -->|consulta progreso y stats| Eco
    Eco -->|crédito| Bank["Bank"]
    Eco -->|concesiones y desbloqueos| Duck["Duckies / Inventory"]
    Shop["Shop"] -->|débito| Bank
    Shop -->|entrega| Duck
    Avatar["Avatar / Equipment"] -->|posesión| Duck
```

Las flechas no fijan HTTP interno ni despliegues independientes.
[Rewards v0](contracts/rewards-v0.md) concentra la semántica candidata para evitar
duplicarla en el ERD: identidad origen/hecho/destinatario, huella validada, versión
de reglas, resultado persistido, referencias a efectos y APPLIED/NO_REWARD.
Los premios son independientes: monedas, objetos o puntos no requieren XPEvent.

Se propone un monolito modular Django y una transacción exterior de Rewards
solo si todos sus servicios usan la misma BD y conexión transaccional.
Ecomotor controla XP/evolución/puntos; Bank monedas; Duckies objetos. Un fallo
revierte efectos y registro final conjuntamente bajo esa condición.
No se aprueba automáticamente ORM de RewardEvent, tabla RewardRule ni FKs.

Shop coordina compra, validación de fondos y entrega mediante los propietarios.
Ecomotor pp. 4–5 también le atribuye comprobaciones de condiciones/saldo;
el reparto exacto con Shop debe acordarse, consultando a Bank sin duplicar saldo.
Rewards v0 no cierra automáticamente el contrato de compras o reservas.

### 5.1. Persistencia y XP histórica local · F2-A (DOC-6)

La [sección técnica F2-A](contracts/rewards-v0.md#12-f2-a--persistencia-y-xp-histórica-local--doc-6)
desarrolla Fase 1 y [S3](contracts/ecomotor-xp-v1.md), sin cambiarlos.
Fase 1 produce RewardDecision; el futuro coordinador validaría autorización,
identidad/huella y efectos soportados, aplicaría S3 con XP positiva y perfil
persistido, y guardaría RewardEvent y el resultado histórico confirmado.
NO_REWARD solo representa evaluación válida sin efectos, incluso para User sin
perfil si no requiere XP. Efectos no soportados se rechazan por completo.

RewardEvent es **modelo físico candidato bloqueado hasta Core**, con identidad
única origen/hecho/User, huella/versiones, snapshot reward-result-v1 y vínculo
XPEvent opcional. La clave S3 rewards:v1: deriva de la identidad, no de la huella
semántica del contenido. Replay recupera el resultado original, sin reevaluar
reglas/catálogos; incoherencias causales u XPEvent huérfano son errores sin reparación.
D-19 rige la transacción exterior local del mismo alias, con rollback completo,
retry explícito y sin I/O externo. No implica atomicidad entre conexiones/BD.

Core debe confirmar User/PK canónico, conservación/anonimización/eliminación,
on_delete y relaciones con XPEvent/perfiles, y autorización **antes de la tabla
y migración**. Configuración válida de evolución y reglas autorizadas condicionan
los premios reales. Bank, Duckies y juegos no bloquean este diseño local, pero
siguen fuera, junto con monedas, inventario/vestimenta, dominio, puntos directos,
cupos, REST/WebSockets y batch. [Bloqueos F2-A](pending-decisions.md#9-bloqueos-de-persistencia-rewards-f2-a--doc-6).
No se implementa Rewards global, ni se modifica el ERD ni se reactiva S8-A.

## 6. REST, cálculo de acciones y tiempo real

DAR_formulas pp. 7–12 documenta estas interfaces objetivo, todavía sin contrato
de integración aprobado por el Equipo 5:

| Referencia documental | Encaje a validar |
| --- | --- |
| POST `/api/v1/ecomotor/calculate-action/` | Cálculo servidor de acción/XP provisional, daño y efectos; distinguirlo de otorgar progreso o monedas definitivamente. |
| POST `/api/v1/ecomotor/commit-rewards/` | Consolidación final con Bank y progresión; adaptar hechos, destinatarios y respuesta al contrato candidato sin sustituir esta referencia unilateralmente. |
| `ws/arenas/{room_id}/` y eventos de combate | La fuente sitúa sincronización en Ecomotor; infraestructura, ownership realtime, productores/consumidores y alcance V1 requieren contraste con Óscar/Core/juegos. |

La fuente incluye JWT, X-Client-Game, stats y cantidades en ejemplos de payload.
Un header declarado no acredita por sí solo el origen; deben acordarse permisos,
validación de datos y obtención de stats canónicos con Core. La forma de expresar
batch de resultados y los efectos parciales de Escape siguen pendientes.
No se aprueba una API nueva incompatible ni se descartan estas rutas o eventos.
REST y RPG completo permanecen en el objetivo; su cobertura V1 y WebSockets no
se resuelven mediante propuestas de participantes.

## 7. Integridad y concurrencia

D-19 continúa vigente íntegramente en [decisions.md](decisions.md):
`transaction.atomic()` antes de leer estado mutable, `BEGIN IMMEDIATE`,
timeout de 5 segundos, constraints e idempotencia persistente.
SQLite tiene un único escritor efectivo para toda la BD, sin bloqueo por fila
real de `select_for_update()`. Transacciones cortas sin I/O externo; timeout
implica rollback y retry en nueva transacción con la misma clave.

D-19 no garantiza atomicidad entre conexiones, bases de datos o transacciones
independientes. La transacción exterior de Rewards v0 es una propuesta adicional
condicionada, no una reinterpretación de D-19. Recuperación distribuida, compras,
reservas, correcciones y devoluciones requieren contrato específico.

## 8. Pendientes y siguiente entrega

### S4-A: consultas locales de progreso e historial integradas · PR #29

[S4-A V1](contracts/ecomotor-progress-queries-v1.md), aprobado internamente por
Jaime, consulta perfiles inicializados sin escrituras ni llamadas a S2-A/S3.
El overview conserva datos básicos aunque falte configuración; sus objetivos de
nivel y etapa se validan independientemente. El historial muestra snapshots XP e
IDs de evoluciones persistidos, sin reconstruir niveles, puntos o códigos históricos.
No utiliza atomic()/IMMEDIATE para lectura ni promete un snapshot único entre
consultas concurrentes. No incorpora HTTP, autenticación de vistas ni CRUD PR07;
Core, conservación, configuración oficial y contratos compartidos siguen pendientes.

### S3 V1: concesión local de XP histórica integrada · PR #28

[S3 V1](contracts/ecomotor-xp-v1.md), aprobado internamente por Jaime bajo
V2-A12/A22/A23 y D-19, concede XP solo sobre perfiles ya inicializados. Valida
catálogos y correspondencia interna de etapas, usa exclusivamente S1 y persiste
XPEvent, todas las EvolutionEvent y puntos nuevos dentro de una transacción.
El replay es histórico: snapshots e IDs persistidos, campos no almacenados None;
no recalcula contra catálogos actuales ni modifica eventos. No inicializa S2-A,
concede objetos/monedas, modifica atributos base ni resuelve Rewards/Core.
El esquema existente no guarda niveles/puntos/códigos históricos completos;
esa limitación forma parte explícita del contrato. La configuración de códigos
autorizados sigue ausente, por lo que las concesiones nuevas reales permanecen
bloqueadas hasta disponer de ella. Este incremento no cambia modelos/migraciones.

### S2-A local: inicialización integrada · PR #27

Parte A ya implementa [S2-A](contracts/ecomotor-initialization-v1.md), aprobado
internamente por Jaime bajo V2-A13/D-19/R-12. Inicializa conjuntamente perfil y
estadísticas de un User existente, con configuración confiable, catálogos validados
y puntos del nivel 1. La configuración de atributos y códigos queda ausente hasta
su autorización; los fixtures de tests no son configuración de producción.
La idempotencia conserva progreso existente; estados parciales/legacy se rechazan.
No sustituye el provisionamiento global Core ni implementa XP/Rewards/inventario.
S2-A se integró sin alterar modelos ni migraciones; la baseline vigente está en §2.1.
Conservación, contratos compartidos y parámetros oficiales
permanecen pendientes, sin aprobación global de Óscar.

El contraste interno hasta el 16/10 distingue conformidad conceptual de integración:
Henry aceptó conceptualmente el 14/10 las propuestas de Jaime R-05 (ItemGrant,
entregas y deduplicación) y R-08 (RewardEvent, trazabilidad e idempotencia completa).
No ratifica campos, ORM, migraciones ni contratos físicos con Fernando/Core/juegos.
El ERD global y H01–H08 son base documental interna de trabajo, no APIs aprobadas
ni implementadas. Fernando aceptó revisar la reubicación de Bank/Shop; el traslado
y la reconciliación de migraciones A/C siguen abiertos.

El acuerdo local R-12 de Jaime y Henry del 13/10 permite avanzar con el inicializador
Ecomotor. S1 y S2-A locales no quedan bloqueados por el diseño físico de Rewards
ni por la aprobación externa de Core. S2-A1/S2-A2 permanecen intactas: perfil y
stats atómicos e idempotentes, sin signals ni nuevo User; seis stats y puntos desde
configuración confiable. La creación global de User y la orquestación final de
Ducky/Wallet, legacy y autorizaciones siguen bajo coordinación de Core.

[Pendientes](pending-decisions.md) concentra preguntas y validadores;
[plan](team5-work-plan.md) asigna trabajo bajo D-20/D-21.
Prioridades: Core, identidad/autorización, conservación y Wallet/saldo canónicos;
contratos Rewards/Bank/Shop/Inventory y consenso de interfaces A/B/C; reconciliar
modelos y migraciones A/C antes de merge; hechos validados y dependencias reales
con los juegos, Escape consolidado, compras e idempotencia/concurrencia.
Se mantiene el conflicto de XP externa, stats/cursos, compatibilidad REST,
ownership realtime y alcance evaluable PR07. El controlador antiguo sencillo
no bloquea el avance ni exige reutilización; el resto de la integración sigue abierta.

El [ERD de Parte A](erd/ecomotor.md) conserva el V2 histórico de ocho entidades
y V2-A1…V2-A29 internas condicionadas; el esquema integrado añade StatAllocationEvent.
DOC-1 no cambia ese ORM ni concede aprobación global a Rewards v0 o al ERD compartido.
La demostración DAR3 de actividad, recompensa, compra, equipamiento e historial
sigue como referencia, con alcance final por contrastar. Historiales/Museo,
integraciones externas y pedidos físicos deben priorizarse sin eliminarlos
silenciosamente. Techies y cotización variable quedan fuera de primera entrega
según DAR3.

## S5-A · Adaptador web personal local integrado · PR #30

El [contrato S5-A](contracts/ecomotor-progress-web-v1.md), aprobado internamente
por Jaime/Parte A, adapta S4-A a una plantilla autónoma de lectura GET/HEAD.
login_required utiliza Django; request.user resuelve exclusivamente el perfil propio.
404 para ausencia, 409 para inconsistencia y 503 para BD, sin detalles internos.
Muestra progreso, stats base, objetivos independientes y diez concesiones recientes
sin reconstrucciones históricas. No escribe ni invoca inicialización/concesión.
La URL local ecomotor:progress se prueba mediante URLconf aislada; config/urls.py
no cambia. Montaje, login final, home y plantilla compartida dependen de Core.
No sustituye CRUD PR07 ni resuelve configuración oficial o contratos globales.
Conserva la ausencia de snapshot transaccional conjunto de S4-A.

## S6-A · Carga de configuración y diagnóstico local integrados · PR #31

El [contrato S6-A](contracts/ecomotor-configuration-v1.md) añade lectura explícita
de JSON interno y diagnóstico SELECT de configuración/catálogos. El cargador
devuelve un objeto sin activar la referencia INITIAL_CONFIGURATION; no hay hooks
de arranque ni cambios de settings. El comando comprueba un candidato o el estado
real de su propio proceso, nunca afirma activar el servidor web. Preparación
técnica y aprobación funcional son independientes. S2-A/S3 conservan contratos,
S4-A/S5-A sus consultas básicas. Sin esquema nuevo ni reparación/concurrencia
transaccional añadida. Instalación autorizada, valores oficiales y V2-A28 pendientes.

## S7-A · Asignación local de puntos integrada · PR #32

[S7-A](contracts/ecomotor-stat-allocation-v1.md) añade gasto transaccional 1:1 en
un atributo base, solo en Actual validada por S1/catálogo/códigos confiables.
StatAllocationEvent registra snapshots independientes de XPEvent y replay sin
configuración actual. D-19 serializa S3/S7-A; solo atributo elegido y saldo cambian
junto al evento. Admin de consulta y 0005 aditiva con reversión protegida.
S1–S6-A y otros equipos intactos; conservación CASCADE provisional, configuración
funcional y contratos globales pendientes. La interfaz posterior es S8-A (PR #40).

## S8-A · Interfaz de asignación local integrada · PR #40

Jaime reactiva [S8-A](contracts/ecomotor-stat-allocation-web-v1.md) después de
DOC-6; las referencias anteriores a su pausa describen sus cortes históricos.
Adaptador GET/POST con login/CSRF Django y perfil exclusivo de request.user.
S4-A muestra datos; S7-A recibe el formulario válido sin prevalidación de
elegibilidad, preservando replay. Clave segura por GET, conservación en POST y
PRG con mensajes distintos. Sin transacciones propias ni escrituras de negocio.
Ruta namespaced local, sin config/urls.py ni integración global Core. Rewards F1
y arquitectura F2-A intactas; F2-A sigue bloqueada para persistencia. No activa
configuración funcional ni resuelve contratos compartidos.

## S9-A · Historial web de asignaciones V1 · implementado para revisión

El [contrato S9-A](contracts/ecomotor-stat-allocation-history-web-v1.md) añade
consulta específica de StatAllocationEvent y página GET/HEAD personal de lectura.
Perfil desde request.user, alias de BD persistido y snapshots validados sin
catálogos actuales ni claves idempotentes en el resultado público. Paginación por
PK descendente exclusiva, diez entradas web, resultados frozen y errores seguros.
Reutiliza UI-A (#41) con navegación compartida; no modifica S4-A/S7-A, modelos,
migraciones, servicios de escritura ni montaje global. Solo SELECT, sin promesa
de snapshot concurrente único. Implementado y probado en rama feature, pendiente
de revisión/merge; no aprobación externa de Core. F2-A mantiene su bloqueo.

## S11-A y S12-A · estado vigente tras PR #44

[S11-A](contracts/ecomotor-specialization-v1.md) está integrado: selección inicial
en Actual, perfil/progreso atómicos, dominio inicial cero y repetición coherente
sin escrituras ni catálogos actuales. No supone autorización global ni cierre P7.
Las expresiones de revisión anteriores conservan su contexto histórico.

[S12-A](contracts/ecomotor-domain-xp-v1.md) registra alternativa C y S12-A-01…06:
Ecomotor propietario del efecto positivo de dominio; Rewards coordinador global;
perfil inicializado, especialización/progreso coherentes y Actual para concesión
nueva; identidad origen–hecho–perfil, repetición/conflictos y atomicidad conceptual.
DomainXPEvent es un concepto separado de las nueve entidades físicas integradas.
No se aprueban ORM, campos/FKs, migración u on_delete. Core debe resolver
conservación/anonimización/eliminación antes de persistir; emisores, vínculo confiable
hecho–destinatario y reglas requieren acuerdos antes de premios reales.
ValidatedRewardFact no autoriza por sí solo. No se desbloquea F2-A.

La firma grant_domain_xp y DomainXPGrantResult son candidatos, no servicios
disponibles. Detalles técnicos, reglas y rangos siguen pendientes. No se modifica
V2-A25/A26 ni DOC-6 retrospectivamente; S13-A no tiene arquitectura aprobada.
