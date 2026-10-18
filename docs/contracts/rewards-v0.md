# Rewards v0 · Contrato conceptual candidato

## 1. Estado, fuentes y límite

**Contrato global v0 candidato, pendiente de validación conjunta por A/B/C,
Óscar/Core y equipos emisores.** DOC-3 (18/10/2026) aprueba R1–R8 internamente
por Jaime para orientar Parte A; no ratifica el contrato compartido ni cambia
su versión. Rewards no está implementado. No es un
endpoint oficial ni un ORM aprobado. Fuentes funcionales y notas de las dailys en [architecture.md](../architecture.md); acuerdos internos D-20/D-21 y
D-19 vigente en [decisions.md](../decisions.md).

DAR3 §§9–10 exige identidad/origen, actividad no premiada dos veces, registro
y resumen. Ecomotor especifica reglas configurables y cantidades independientes.
Daily del 09/10/2026: se indicó centralización funcional, sin resolver el contrato técnico.
Las preguntas y condiciones de implementación están en
[pending-decisions.md](../pending-decisions.md).

### Estado técnico DOC-4 · 18/10/2026

[T1–T8](../decisions.md#doc-4--diseño-técnico-rewards-v1--t1t8--18102026) están
aprobadas internamente por Jaime sobre R1–R8 (PR #35). El [diseño técnico §10](#10-diseño-técnico-interno--doc-4)
conserva modelos e interfaz como candidatos; no aprueba migraciones, contratos
propietarios o publicación HTTP. Rewards sigue sin implementar y este archivo
mantiene su nombre, versión v0 y condición de contrato global candidato.

### Alcance de la aprobación interna DOC-3 · 18/10/2026

El [registro R1–R8](../decisions.md#doc-3--arquitectura-rewards-v1--acuerdos-internos-de-parte-a--18102026)
contiene la decisión de Jaime; [pendientes §3](../pending-decisions.md#3-validación-conjunta-de-rewards-v0)
conserva la especificación técnica y aceptación externa residual de cada una.
Los principios de §§3–8 se adoptan internamente en ese alcance, sin aprobación
conjunta de Henry/Fernando/Core/juegos, nuevas tablas o interfaces vinculantes.
«Arquitectura V1» no convierte este documento en rewards-v1 ni habilita servicios.
D-19/D-20/D-21 siguen vigentes; S1–S7-A no cambian y S8-A permanece pausado.

### Contraste histórico DOC-2 · 18/10/2026

La [matriz canónica de integración](integracion-equipo5-v0.md#0-matriz-de-procedencia-y-acuerdos--doc-2)
traza E5-01…E5-05, decisiones atribuidas al usuario en el catálogo y respuestas
externas 15–16/10. Guía v0.1 y kit v0.3 siguen siendo propuestas; este contrato
**conserva la versión v0 candidata**, sin aprobación de nuevas tablas o firmas.

Training comunica importes/reglas locales distintos de T-01; Quiz mezcla baremos
con liquidación por score; Escape prefiere C mixta sin aceptar E-01. No se fijan
cantidades, límites o endpoints por estas respuestas. Cobro único de pistas y
relectura gratuita no prueban integración Bank; la eliminación de penalizaciones
sigue en conflicto E5/Escape. T-01/Q-01/E-01 y precios 3/5/8 o 2/4/6 sin ratificar;
los 4/3/4 DC de tres productos solo se atribuyen a demo interna.

E5-03 declara Bank como única Wallet global, pero CORE-05 no aporta confirmación
de cierre: se conserva pendiente el encaje técnico y fuente física canónica, sin
saldo duplicado. Los diseños de vestimenta/autoequipamiento, variantes y
transformación no están ratificados globalmente. Conformidad conceptual previa
de Henry con ItemGrant/RewardEvent no aprueba sus modelos o contratos físicos.

S3 y S7-A ya están integrados localmente: conceder XP/puntos de nivel y gastar
puntos disponibles son operaciones distintas de evaluar una recompensa global o
conceder puntos directos. La novena entidad local es StatAllocationEvent; no
implica RewardEvent, RewardRule o ItemGrant implementados. S8-A permanece pausado.

## 2. Entrada lógica y propietarios

Rewards es el punto lógico de entrada para **hechos recompensables validados**,
coordinado desde Ecomotor. Puede ser invocado mediante servicios Python internos;
el transporte externo se acuerda separadamente. D-21 no exige otra app.

| Propietario | Efectos bajo su control |
| --- | --- |
| Servicio del juego o plataforma de origen | Valida y registra el hecho en su dominio; proporciona identidad estable y contexto verificable. |
| Rewards / Ecomotor | Evalúa elegibilidad, reglas, condiciones, límites y compatibilidad; coordina la recompensa y su trazabilidad. |
| Ecomotor | XP histórica o de dominio cuando proceda, nivel, evolución, puntos estadísticos y sus historiales. |
| Bank | Créditos de Duki Coins y movimientos; único propietario de wallet/saldo. |
| Duckies | Concesiones/desbloqueos de objetos, identidad, posesión y cantidades. |
| Core / Óscar | Identidad, autenticación/JWT, origen autorizado, permisos, integración y conservación. |

La coordinación utiliza operaciones propietarias; no escribe directamente en
tablas ajenas. Shop/compras y Bank/Clash/reservas tienen contratos distintos:
este documento no los da por aprobados.

### Operaciones mínimas entre propietarios · propuesta conceptual

| Operación | Entrada conceptual | Resultado conceptual |
| --- | --- | --- |
| Ecomotor: concesión de XP histórica | Usuario/perfil, XP positiva, clave idempotente y referencia al evento Rewards. | Evento registrado, XP concedida, nivel/evoluciones resultantes e indicación de operación ya aplicada. |
| Bank: crédito de monedas | Usuario, importe positivo, clave idempotente, origen y referencia Rewards. | Movimiento contable, importe, saldo resultante e indicación de operación ya aplicada. |
| Duckies: concesión de objetos | Usuario, código del objeto, cantidad positiva, clave idempotente y referencia Rewards. | Identificador de entrega, objeto/cantidad e indicación de operación ya aplicada. |

XP de dominio y puntos estadísticos requieren operaciones diferenciadas pendientes
de cerrar. Esta tabla no fija firmas Python, endpoints REST, FKs ni migraciones.
El saldo devuelto por un duplicado corresponde al resultado persistido de la operación.
Daily del 13/10/2026: no es necesario esperar ni reutilizar obligatoriamente el
antiguo controlador sencillo de DuckyCoins descrito por Óscar. La aclaración se
limita a ese componente; consultar otro código anterior puede ser útil.
Sigue pendiente acordar con Core y Fernando la fuente canónica de Wallet/saldo y
el punto común de concesión, identidad/autorización, movimientos, idempotencia,
concurrencia e integración con los propietarios. No se permite un segundo saldo
canónico. Rewards v0 sigue como contrato conceptual candidato: la conformidad
funcional general no aprueba su semántica técnica ni las interfaces de Henry.

## 3. Identidad y contenido validado

R1 aprueba internamente la identidad lógica de una recompensa como terna:

`(origen autorizado, identificador del hecho, destinatario)`

- El origen se verifica con Core y no se confía solo en un nombre enviado por el
  navegador o en X-Client-Game.
- El identificador representa el mismo hecho ante reintentos. Partidas repetidas
  válidas son hechos distintos. Una sesión no identifica por sí sola a todos sus
  destinatarios o premios parciales.
- El destinatario es la identidad User validada con Core. Un mismo hecho puede
  afectar a varios usuarios sin confundir sus recompensas.
- Parcial/final de Escape necesita acordar qué constituye cada hecho y cómo se
  relaciona con sesión/prueba/room para no pagar el mismo logro dos veces.

El mínimo de DAR3 §10 incluye identificador de actividad terminada, usuario,
tipo de juego, resultado validado, fecha/hora y datos necesarios para calcular
la recompensa. Su adaptación a esta identidad candidata requiere acuerdo.
El contenido semántico incluiría tipo de actividad, resultado validado, fecha/hora
del hecho y contexto necesario para evaluar reglas. Identidades, cantidades,
resultado y atributos recibidos requieren validación; el juego no puede imponer
un premio arbitrario. Hay que acordar qué campos son resultado bruto, cálculo
de acción o recompensa propuesta que Ecomotor debe validar.

R2 aprueba internamente guardar una **huella del contenido semántico validado**
para detectar incompatibilidades; su concreción compartida sigue pendiente.
T2 concreta internamente SHA-256 sobre JSON semántico canónico versionado,
claves ordenadas, UTF-8 y fechas normalizadas en UTC. Excluye IDs HTTP, tiempos
de reintento y configuración posterior. Campos semánticos de cada juego,
detalles de serialización y formato exacto de claves requieren especificación
y validación compartida. La unicidad lógica T1 no aprueba aún constraints físicas.
No se decide qué cambios meramente de transporte
generan conflicto ni se incluyen timestamps de reenvío por defecto.
La huella no sustituye autenticación ni prueba la veracidad del hecho.

## 4. Reglas y efectos independientes

R5/R6 aprueban internamente efectos independientes y reglas configurables en
elegibilidad, cantidades, vigencia, repetibilidad, límites y compatibilidad,
por regla, usuario, actividad y periodo, separando límites de XP y monedas.
`RewardRule` es concepto de diseño: su representación como tabla no está aprobada.
R3 acepta internamente conservar la versión o referencia reproducible de las
reglas usadas en la evaluación; su representación técnica sigue pendiente.

Cada premio puede contener efectos distintos e independientes: XP, monedas,
objetos/desbloqueos y puntos estadísticos. **Puede existir recompensa sin XP**.
No se crea XPEvent ficticio para registrar un crédito monetario, objeto o punto.
Los puntos derivados de un ascenso y los concedidos directamente no deben contarse
dos veces. Contrato de puntos, XP de dominio y referencias causales siguen
pendientes, sin añadir entidades físicas a Parte A.

Daily del 09/10/2026: Óscar planteó reservar XP a juegos y monedas a actividades
externas, en conflicto con la XP externa contemplada por DuckyEcomotor.
Alcance sobre XP histórica/de dominio, actividades, vigencia, progreso existente
y configuración de nuevas reglas siguen pendientes. No se elimina XP retrospectivamente
ni se convierten automáticamente todas las actividades externas en premios sin XP.
Objetos y puntos de cursos siguen por concretar; bonificaciones diarias de XP por
cursos fueron propuestas discutidas, sin regla confirmada.

## 5. RewardEvent candidato y resultado

R3 acepta internamente `RewardEvent` como concepto de evidencia persistente de
evaluación y de los efectos de **toda la recompensa**, no un alias de XPEvent.
La información conceptual aceptada es la siguiente; su ORM sigue pendiente:

| Información conceptual | Finalidad |
| --- | --- |
| Origen autorizado, hecho y destinatario | Identidad de deduplicación global de la recompensa. |
| Huella del contenido validado | Comparación ante reutilización incompatible de identidad. |
| Versión de reglas aplicada | Explicar la evaluación sin recalcular con configuración posterior. |
| Resultado persistido y motivo | Recuperar el resultado de negocio y explicar ausencia de premio. |
| Referencias a efectos propietarios | Relacionar eventos de progreso, movimientos Bank y concesiones Duckies sin aprobar FKs físicas. |
| Estado final APPLIED o NO_REWARD | Distinguir aplicación de al menos un efecto y evaluación válida sin efectos. |

El resumen de negocio conserva el mínimo DAR3: XP y monedas concedidas,
pieza/evolución/logro cuando proceda e indicación de ya procesado. Los premios
sin XP y puntos adicionales deben expresarse sin inventar concesiones de XP.
Formato técnico y respuesta de batch quedan pendientes.

T1–T3 y §10 concretan un diseño físico candidato, incluido fact_id hasta 255
caracteres; no aprueban una migración, índices/FKs definitivos ni políticas
CASCADE/PROTECT/SET_NULL o retención. Las referencias propietarias requieren
acuerdo antes de adoptar una representación física.
No se incorpora RewardEvent al esquema integrado
de Parte A; StatAllocationEvent de S7-A es un historial local diferente.

**APPLIED** significa que los efectos acordados quedaron confirmados junto con
el registro final. **NO_REWARD** significa hecho válido evaluado sin efectos,
por condiciones/límites aplicables, con motivo recuperable. Es también final y
deduplicable. Una evaluación con solo monedas u objetos es APPLIED.

Errores de autorización, entrada inválida o fallo de servicio no se convierten
en NO_REWARD. No se aprueban estados intermedios persistentes, FAILED, colas o
reintentos automáticos. El tratamiento de incidentes fuera de la transacción
y las correcciones/devoluciones requiere diseño posterior, sin reescribir historia.

## 6. Duplicados, conflictos y límites

Para la misma identidad y contenido validado compatible, el duplicado devuelve
el resultado persistido y su condición de ya procesado; no recalcula premios con
otra versión de reglas ni repite efectos. Se recupera lo concedido originalmente,
no necesariamente el saldo o estado actual del usuario.

La misma identidad reutilizada con contenido incompatible produce conflicto,
sin nuevos efectos ni reescritura del resultado anterior.
Criterios exactos y representación de errores se validarán conjuntamente;
no se fijan códigos HTTP.

La deduplicación del hecho y los límites de reglas son garantías diferentes.
Dos partidas válidas distintas de Training pueden conceder XP; solo la primera
elegible por juego/día concede una moneda. Revisar ambas bajo concurrencia,
incluida la competencia entre hechos diferentes por el mismo límite.
Training comunica Europe/Madrid y una moneda por primera finalización válida
de cada juego/día como información funcional local. La confirmación técnica de
ciclo/zona, día de actividad o registro, importes, hechos tardíos y contabilización
compartida siguen pendientes; no se ratifica un baremo global por esta información.

Una repetición de NO_REWARD recupera la evaluación anterior. R7 aprueba
internamente recuperar confirmados con su identidad original y registrar
correcciones posteriores como operaciones nuevas trazables vinculadas al premio
original, sin sobrescribir historia ni reutilizar una identidad con otro contenido.
Las políticas concretas de ajuste o retirada de XP, niveles, monedas y objetos
requieren aprobación de cada propietario; no se autoriza reducir XP histórica
por esta decisión. Representación de vínculos, cambios de reglas e incidentes
siguen por especificar; un error técnico nunca es una evaluación sin premio.

## 7. Transacción exterior compartida · R4, aprobación interna condicionada

R4 aprueba internamente que, en el **monolito modular Django**, Rewards coordine
la transacción exterior que abarque evaluación con estado mutable, registro final y efectos
propietarios. Condición necesaria: **misma base de datos y misma conexión/alias
transaccional**, sin commits independientes de los servicios. Transacciones
anidadas solo participan en esa frontera si cumplen esas condiciones.

Flujo conceptual, sin firma Python ni orden físico definitivo de escrituras:

1. Validar origen, destinatario y contenido; preparar la huella sin I/O externo
   dentro de la transacción.
2. Abrir la transacción exterior antes de consultar estado mutable.
3. Resolver identidad/duplicados/conflictos bajo serialización y unicidad persistente.
4. Evaluar reglas y límites con versión reproducible.
5. Solicitar a los propietarios los efectos aplicables.
6. Persistir resultado, referencias y estado final y confirmar todo conjuntamente.

D-19 conserva BEGIN IMMEDIATE, timeout de 5 segundos, constraints e idempotencia;
no cambia su configuración. La protección de la terna y la relación con claves
locales de XP, Bank y Duckies se diseñará antes del ORM.
Un fallo revierte efectos y registro final conjuntamente bajo las condiciones
anteriores. Un retry abre nueva transacción con la misma identidad.
La unicidad local de XPEvent no sustituye la protección de RewardEvent.

No hay HTTP, publicación WebSocket u otro I/O externo en la transacción.
Cualquier notificación futura debe vincularse a la confirmación, con garantía de
entrega aún por acordar; no se aprueba una infraestructura de mensajería.

Si algún servicio usa otra conexión/BD o confirma por separado, esta propuesta
**no ofrece atomicidad global**: detener la implementación afectada y acordar
recuperación/compensación/reconciliación. No se selecciona aquí una estrategia
distribuida ni se atribuye esa garantía a D-19.

## 8. Encaje documental con REST y juegos

R8 sitúa el núcleo de negocio en `apps.ecomotor`, mediante servicios Python
y adaptadores cuando corresponda; no aprueba firmas, JWT, permisos, formatos,
lotes, atomicidad entre destinatarios ni publicación HTTP/WebSockets definitiva.
DAR_formulas pp. 7–12 documenta POST
`/api/v1/ecomotor/calculate-action/`, POST
`/api/v1/ecomotor/commit-rewards/` y `ws/arenas/{room_id}/`.
Se conservan como referencias de arquitectura objetivo a contrastar, no se
descartan ni se reemplazan por rutas nuevas en este contrato.

`calculate-action` calcula una acción/resultado provisional; no equivale por sí
solo a confirmar una recompensa. R8 exige que la confirmación aplique R1–R7, sin
confiar automáticamente en importes enviados por un juego.
`commit-rewards` es referencia para consolidar,
con resultados por sesión/destinatario que deben mapearse a identidad,
trazabilidad y respuesta candidatas. Atomicidad de un batch, validación de
cantidades y stats recibidos y compatibilidad de payloads siguen pendientes.
JWT, permisos y verificación de origen se acordarán con Óscar/Core.
La fuente atribuye sockets a Ecomotor; ownership realtime y cobertura V1 no se
deciden unilateralmente. No se aplaza globalmente RPG por DukiStats 2.0.

| Caso | Condición funcional y pregunta de integración |
| --- | --- |
| Training | XP repetible y una moneda por juego/día: deduplicar cada hecho y aplicar límite monetario independiente. Los límites de acceso, de monedas y la idempotencia por sesión son distintos. |
| Escape | XP por stages completados y recompensa final independiente; una partida incompleta conserva la XP válida de las pruebas realizadas. Stage y habitación no son equivalentes: ausencia de moneda por stage no elimina por sí sola premios por habitación. Versión consolidada más reciente y momento de registro pendientes. |
| Quiz | Tiempo, aciertos, estadísticas y resultados intervienen en el cálculo; cifras de ejemplo no son cantidades obligatorias. Contrato pendiente. |
| Clash | Resultado validado y participantes por destinatario; apuestas, si se incluyen, reservadas por Bank al aceptar. Reserva/liberación/liquidación/cancelación requieren contrato propio y alcance V1. |
| Cursos / otras actividades | Monedas externas y posibles objetos/puntos; elegibilidad y V1 pendientes. No inventar XP para registrar efectos sin XP. |

## 9. Validación conjunta antes de implementar

Concretar y validar conjuntamente formatos de identidad/huella y permisos;
versión de reglas; referencias y conservación
con Óscar/Core; claves locales; límites temporales; servicio de puntos; XP de dominio;
compatibilidad calculate-action/commit-rewards y Escape actualizado.
Revisar capacidad real de compartir transacción con Henry y Fernando.
El antecedente V2 de ocho entidades de [Parte A](../erd/ecomotor.md) se conserva;
el esquema integrado añade StatAllocationEvent por S7-A. No se añaden entidades
de Rewards ni se aprueban decisiones físicas compartidas.

Pruebas futuras de aceptación: duplicados APPLIED/NO_REWARD; conflictos sin
efectos; premios sin XP; rollback ante fallo de cada propietario; misma identidad
concurrente; hechos distintos compitiendo por límite diario; correspondencia
entre resultado y efectos; autorización y batch/parciales una vez acordados.
D-19 exige TransactionTestCase y al menos una ejecución SQLite file-backed.
Este PR documental no implementa ni ejecuta esos tests.

## 10. Diseño técnico interno · DOC-4

Aprobación de Jaime del 18/10/2026, no ratificación de Henry, Fernando, Core o
juegos. El [registro T1–T8](../decisions.md#doc-4--diseño-técnico-rewards-v1--t1t8--18102026)
recoge autoridad y alcance; [validación residual](../pending-decisions.md#7-validación-residual-del-diseño-técnico--doc-4)
conserva las condiciones previas a una implementación posterior. Esta sección
no incorpora tablas, servicios o APIs implementados.

### Identidad y registro candidatos · T1–T3

Destinatario User global vía settings.AUTH_USER_MODEL, no perfil Ecomotor
obligatorio. Identidad (origin_code, fact_id, recipient); origin_code estable,
fact_id opaco no vacío de hasta 255 caracteres y destinatario validado. T2 elige
SHA-256 y JSON semántico canónico versionado, claves ordenadas, UTF-8 y fechas UTC,
sin metadatos HTTP/reintento/configuración posterior. El UTC de la huella no fija
el día de negocio de Training. Campos por juego y detalles de canonicalización
siguen pendientes; una huella equivalente no autentica emisor ni veracidad.

RewardEvent es **modelo candidato en apps.ecomotor**. Agrupa identidad y tipo de
actividad; fechas del hecho/registro; versión/valor de huella y versión de reglas;
APPLIED/NO_REWARD y motivo; snapshot JSON del resultado histórico. Se propone
unicidad compuesta e integridad persistente, sin fijar aún migración, índices,
longitudes restantes u on_delete/conservación. La relación opcional OneToOne con
XPEvent es candidata para XP histórica V1, no garantía para batch, dominio o
extensiones. No crear FKs físicas Bank/Duckies sin sus contratos.

### XP, evaluación y cupos · T4–T6

Reutilizar [S3](ecomotor-xp-v1.md):
`grant_historical_xp(profile, amount, operation_key)`. Rewards comprueba identidad/huella, duplicados y elegibilidad;
S3 mantiene XP, niveles, evoluciones y puntos de ascenso. Solo invocarlo con XP
positiva y perfil ya inicializado; no invocar S2-A automáticamente. Derivar la
clave XP estable mediante SHA-256 de la identidad Rewards, con prefijo reservado
`rewards:v1:`; codificación exacta de esa identidad por especificar.

La transacción exterior del mismo alias cubre concesión y RewardEvent. Conservar
snapshot suficiente para replay y verificar coherencia causal con XPEvent y su
destinatario/perfil; no reconstruir historia con catálogos actuales. S3 no guarda
todos los niveles/puntos históricos y su replay devuelve None en esos campos:
el futuro registro Rewards debe conservar lo necesario del resultado original,
sin inventar valores si falta evidencia. Campos exactos y relación causal se
validarán antes de la fase persistente. No cambiar S3 salvo necesidad demostrada.

RewardDecision conceptual separa evaluación/aplicación: versión, cantidades,
elegibilidad y motivos. APPLIED exige efecto confirmado; NO_REWARD solo evaluación
válida sin premio. Fallos de configuración, autorización o infraestructura son
errores. Comenzar con configuración versionada sin tabla RewardRule, sin habilitar
baremos no ratificados; reglas ficticias únicamente en tests de incrementos futuros.

RewardLimitUsage es **modelo auxiliar candidato**, no tabla integrada: cupo por
usuario, regla, ámbito y periodo; identidad única y comprobación/incremento bajo
la misma transacción. Separar límites XP/monedas y replay/actividad nueva.
SQLite IMMEDIATE de D-19, sin depender de select_for_update. No activar límites
económicos sin contrato Bank. Día efectivo, hechos tardíos y cambios de reglas
pendientes con Training/Core; no prometer atomicidad con bases independientes.

### Entrada, salida y errores · T7

ValidatedRewardFact conceptual contiene origen, hecho, destinatario, tipo,
instante, resultado validado y contexto; requiere además un contexto de
autorización confiable, no una declaración del navegador.
RewardResult conceptual contiene identificador, estado, replayed, versión de
reglas, premios, progresión, motivo y referencias propietarias.

Operación **candidata**, no firma definitiva ni endpoint:
`process_reward(validated_fact, authorized_context) -> RewardResult`.
Distinguir categorías de excepción de entrada, autorización, conflicto,
configuración, precondición, propietario y base de datos. No se fijan nombres de
clases, payloads HTTP, códigos HTTP o semántica de batch.

T8 se desarrolla en el [plan de cuatro fases](../team5-work-plan.md#31-fases-rewards--t8-aprobado-internamente-doc-4),
con PR pequeños y revisión por fase. No modifica S1–S7-A ni reactiva S8-A.
