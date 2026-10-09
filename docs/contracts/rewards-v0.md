# Rewards v0 · Contrato conceptual candidato

## 1. Estado, fuentes y límite

**Propuesta técnica aceptada provisionalmente como base de trabajo, pendiente
de validación conjunta por A/B/C, Óscar/Core y equipos emisores.** No es un
endpoint oficial ni un ORM aprobado. Fuentes funcionales y notas de las dailys en [architecture.md](../architecture.md); acuerdos internos D-20/D-21 y
D-19 vigente en [decisions.md](../decisions.md).

DAR3 §§9–10 exige identidad/origen, actividad no premiada dos veces, registro
y resumen. Ecomotor especifica reglas configurables y cantidades independientes.
Daily del 09/10/2026: se indicó centralización funcional, sin resolver el contrato técnico.
Las preguntas y condiciones de implementación están en
[pending-decisions.md](../pending-decisions.md).

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
Antes de implementar, revisar el código existente de Óscar y acordar su reutilización,
el propietario canónico de Wallet y el punto común de concesión con Fernando/Core;
no se crea un segundo saldo o sistema de recompensas.

## 3. Identidad y contenido validado

La identidad candidata de una recompensa distingue la terna:

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

Se propone una **huella del contenido validado** para detectar incompatibilidades.
Canonicalización, campos incluidos, algoritmo, formato de claves y alcance de
unicidad quedan pendientes. No se decide qué cambios meramente de transporte
generan conflicto ni se incluyen timestamps de reenvío por defecto.
La huella no sustituye autenticación ni prueba la veracidad del hecho.

## 4. Reglas y efectos independientes

Las reglas son configurables en elegibilidad, cantidades, vigencia, repetibilidad,
límites y compatibilidad. `RewardRule` es concepto de diseño: su representación
como tabla no está aprobada. Se propone conservar la versión o referencia
reproducible de las reglas usadas en la evaluación.

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

`RewardEvent` sería la evidencia persistente de evaluación y de los efectos
de **toda la recompensa**, no un alias de XPEvent. Se propone conservar:

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

No se fijan campos Django, longitudes, índices, FKs, CASCADE/PROTECT/SET_NULL o
políticas de retención. Las referencias podrían tomar distintas representaciones
tras el acuerdo compartido. No se incorpora una novena entidad al ERD mínimo.

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
Identidad del juego, zona horaria, día de actividad/registro, llegada tardía y
contabilización temporal están pendientes.

Una repetición de NO_REWARD recupera la evaluación anterior. Correcciones,
nuevas versiones de un hecho y cambios de reglas no se tratan como reintentos
ordinarios; su política requiere acuerdo, no reutilizar una clave con otro contenido.

## 7. Transacción exterior compartida propuesta para V1

Se propone un **monolito modular Django** donde Rewards abra la transacción
exterior que abarque evaluación con estado mutable, registro final y efectos
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

DAR_formulas pp. 7–12 documenta POST
`/api/v1/ecomotor/calculate-action/`, POST
`/api/v1/ecomotor/commit-rewards/` y `ws/arenas/{room_id}/`.
Se conservan como referencias de arquitectura objetivo a contrastar, no se
descartan ni se reemplazan por rutas nuevas en este contrato.

`calculate-action` calcula una acción/resultado provisional; no equivale por sí
solo a confirmar una recompensa. `commit-rewards` es referencia para consolidar,
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

Acordar identidad/huella y permisos; versión de reglas; referencias y conservación
con Óscar/Core; claves locales; límites temporales; servicio de puntos; XP de dominio;
compatibilidad calculate-action/commit-rewards y Escape actualizado.
Revisar capacidad real de compartir transacción con Henry y Fernando.
Las ocho entidades de [Parte A](../erd/ecomotor.md) conservan su diseño provisional;
las decisiones físicas adicionales requieren revisión separada.

Pruebas futuras de aceptación: duplicados APPLIED/NO_REWARD; conflictos sin
efectos; premios sin XP; rollback ante fallo de cada propietario; misma identidad
concurrente; hechos distintos compitiendo por límite diario; correspondencia
entre resultado y efectos; autorización y batch/parciales una vez acordados.
D-19 exige TransactionTestCase y al menos una ejecución SQLite file-backed.
Este PR documental no implementa ni ejecuta esos tests.
