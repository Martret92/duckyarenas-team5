> **Estado al 16/10/2026.** H01–H08 son interfaces candidatas y base documental interna de trabajo, no APIs aprobadas ni implementadas. D-20/D-21 están ratificados por Jaime, Henry y Fernando. R-05/R-08 tienen conformidad conceptual Jaime–Henry, sin ratificación física global. R-12 permite avanzar con la inicialización local de Ecomotor (S2-A1/S2-A2 intactas); el alta global, identidad y permisos siguen pendientes de Core. Las firmas siguientes son ejemplos, no autorización de ORM, migraciones ni transacciones compartidas.

## 0. Matriz de procedencia y acuerdos · DOC-2

Consulta dirigida el **18/10/2026**, sobre develop `33b4e87` tras PR #33.
Se consultaron las versiones nativas de Drive facilitadas por Jaime, no se
verificó identidad binaria con exportaciones Word/Excel. No se copian documentos
completos, comentarios personales, soluciones de juegos ni datos de contacto.

| Fuente | Fecha/versión y uso en esta consolidación |
| --- | --- |
| DAR3 y PR07 | Requisitos y evaluación según el registro documental existente; no se atribuye una nueva consulta directa de los PDF. DAR3 prima en requisitos; PR07 en entregables académicos. |
| Respuestas E5 | Versión disponible del 15/10/2026, E5-01…E5-05 y observaciones. Es respuesta de E5; sus etiquetas de cierre no prueban aprobación de Core o de todos los propietarios. |
| duckyarenas-team5/ | Documento organizativo actualizado el 13/10/2026: árbol objetivo, responsabilidades y ejemplos de contratos; no describe por sí solo el árbol implementado. |
| Coordinación entre equipos · Respuestas de integración (15–16 oct 2026) | Versión disponible actualizada el 17/10: respuestas Training T-00–T-08, Quiz Q-00–Q-07, Escape E-00–E-08; CORE-01–07 y PROF-01–03 pendientes. Hay campos de responsable/fecha/evidencia sin completar. |
| Catálogo visual y funcional · candidato v0.3 · 15-10-2026 | Pestañas 19_Reglas_uso_v04, 20_Reglas_generales_v04, 22_Decisiones_v04, 25_Decisiones_Shop_V1, 27_Acuerdos_Shop_V1, 29_Escape_balanceo y 30_Decisiones_Escape; contienen decisiones atribuidas al usuario, propuestas y auditorías de fixtures. |
| Guía de coordinación y balanceo v0.1 · 15-10-2026 | Borrador económico; T-01/Q-01/E-01 son hipótesis sin ratificar. Las observaciones de repositorios son las de esa fuente, no una nueva auditoría de código externo. |
| Kit de integración Rewards v0.3 para compartir · 15-10-2026 | Propuesta técnico-funcional no aprobada ni implementada: hechos, reintentos, adaptadores, simulaciones y alternativas Escape. No promueve Rewards v0 a V1. |

**Categorías:** requisito DAR3; decisión interna aprobada (o atribuida al usuario
por la fuente); respuesta funcional externa pendiente de integración; propuesta
sin aceptar; conflicto; validación pendiente. Una respuesta o un objetivo de
producto no ratifican firmas, ORM, campos, transacciones o puesta en producción.
Responsables designados no equivalen a firmantes de todas las decisiones.
Los baremos T-01/Q-01/E-01 de la guía corresponden a las preguntas T-04/Q-03/E-03
de coordinación; no se confunden con sus preguntas de repositorio/rama.

### E5-01…E5-05 y responsabilidades

| Referencia | Contenido y categoría | Evidencia / responsable | Estado residual |
| --- | --- | --- | --- |
| DAR3 · recompensas | Requisito: actividad validada identificable, destinatario, protección de duplicados y resumen. | DAR3 §§9–10, trazado en decisions.md; E5 y equipos emisores. | Transporte, autorización y representación técnica pendientes. |
| D-20/D-21 | Decisión interna ratificada: A/Jaime Ecomotor-Rewards, B/Henry Duckies, C/Fernando Bank-Shop; cuatro apps objetivo más users. | Registro de decisiones y contraste 14–16/10; aceptación de los tres. | No se reabre el reparto ni se declara integrada su estructura física completa. |
| E5-01 | Propuesta técnica E5: entrada Rewards en Ecomotor, hechos validados e idempotencia de toda la recompensa; servicio interno o adaptador API según entorno. | Respuestas E5; Jaime, revisión Henry/Fernando. Conformidad conceptual R-08 previa. | RewardEvent candidato; firma, versión, transporte, origen y autenticación Core/juegos sin ratificar. |
| E5-02 · catálogo/consumo | Respuesta E5: Duckies posee objetos/cantidades; Shop ofertas/precios; Ecomotor etapa. Permanentes únicos, consumibles acumulables; preparar no gasta, activación válida sí. | Respuestas E5 y catálogo v0.4; Henry/Jaime/Fernando según dominio. | Identificadores, reservas, consumo, transformación y variantes requieren contrato; no se crean FK ni servicios. |
| E5-02 · vestimenta | Conflicto: la respuesta E5 declara conjunto completo único por etapa, concesión/autoequipamiento, conservación y reutilización tras fase final y especialización, sin venta. | Respuestas E5 frente a DAR3 seis piezas/progreso/misiones y R-01 mixto del registro; Jaime/Henry, Óscar. | No cerrar R-01/P6 ni adoptar autoequipamiento, conjunto como un único Item, prohibición comercial global o adaptación nueve/siete por inferencia. |
| E5-03 · Bank | Posición funcional de E5: una Wallet y Bank como único saldo de toda la plataforma; sin saldos independientes. La fuente lo declara resuelto funcionalmente. | Respuestas E5; Fernando con Óscar/Core y consumidores. | No acredita confirmación técnica de Core ni aceptación conjunta de todas las partes. Fuente física canónica, acceso autorizado y conciliación con perfiles globales pendientes. |
| E5-03 · compras | Propuesta de integración: Shop coordina débito, entrega y registro idempotentes; rollback común solo en misma conexión/BD. | Respuestas E5 y Rewards v0; Fernando/Henry/Jaime. | Si Bank es remoto, confirmación/recuperación por acordar. No se aprueba una arquitectura transaccional global. |
| E5-04 | Pendiente explícito: reglas de Training, Quiz y Escape; score no equivale automáticamente a XP/DC y límites XP/monedas separados. | Respuestas E5, guía y kit; Jaime/Fernando/equipos de juegos. | T-01/Q-01/E-01 no son baremos aprobados; faltan elegibilidad, importes, límites y anulaciones. |
| E5-05 | Propuesta interna: adaptadores y mocks identificados, IDs persistentes y pruebas de error/reintento sin escrituras directas ajenas. | Respuestas E5 y kit; A/B/C y juegos. | Mock no acredita pago, XP, consumo ni integración real. Contrato final pendiente de propietarios y Core. |

### Decisiones de objetos v0.4 atribuidas al usuario

Los identificadores D-F y SHOP siguientes son **de las pestañas del catálogo**,
no nuevos identificadores D del repositorio. Se registra su aprobación funcional
atribuida al usuario el 15/10; no se deduce conformidad de Henry, Fernando, Quiz,
Training, Escape o Core ni se convierten sus parámetros en configuración oficial.

| Referencia del catálogo | Decisión funcional atribuida / diferencia con propuesta | Responsables y validación restante |
| --- | --- | --- |
| D-F-01 · consumo | Preparar no consume; activación válida consume una unidad. Defensa automática al bloquear/proteger; ataque válido interceptado gasta ataque y Firewall, intento inválido no gasta. | Henry y Quiz; transacción, reservas, liberación e idempotencia sin diseño ratificado. |
| D-F-02 · maleta | Capacidad de carga de una partida, no límite total de inventario; la fuente remite a capacidades DAR3 por rango. | Henry/Jaime/Core/Quiz: rango y slots; no se reintroducen rangos antiguos en el modelo A. |
| D-F-03 · ataques | Humo 5 s; Inflador +1 falsa validada; Overclock ×1,2 durante 5 s sobre tiempo servidor. | Quiz valida efecto, fase, objetivo y soporte real. Son concreciones internas, no nuevos valores oficiales DAR3. |
| D-F-04 · defensas | Firewall para Humo/Inflador; Filtro retira una falsa; Slow-Time ×0,8 durante 5 s; Seguro de Racha protege un fallo en partida, máximo uno. Asociación gráfica elixir/botiquín sigue propuesta. | Quiz/Henry y arte; no equiparar una imagen con mecánica implementada. |
| D-F-05 · límites | Un debuff activo por rival, 2 s de inmunidad posterior, un ataque manual por emisor/pregunta y una defensa manual propia; automáticas aparte. | Quiz debe validar límites servidor y compatibilidad de modos. |
| D-F-06 · ayudas | Explicación básica gratuita; extra tras error, relectura gratis; pista Escape con cobro/desbloqueo único por sesión/pista y relectura gratis. | Training no confirma extras en V1; Escape y Bank deben acordar autorización, entrega y recuperación. |
| D-F-07 · épocas | Compra de consumibles históricos de época actual; transformación de unidades no gastadas a nueva época con arte de respaldo. | Decisión adicional atribuida al usuario, no requisito textual DAR3. Henry/Jaime/Fernando: variantes, cantidades, valor y transformación sin duplicados pendientes. |
| D-F-08 · relojes | Overclock y Slow-Time son objetos distintos, con cantidades independientes y diseño histórico compartido distinguible. | Henry/arte/Quiz; identidad y contrato sin aprobar. |
| D-F-09, SHOP-04/07 | Objetivo interno de seis tácticos generales en Shop V1 público, condicionado a efectos reales verificados en Quiz. | Cambio de prioridad respecto al MVP de DAR3; coordinación Equipo 1/Core y validación funcional pendientes. No prueba venta operativa ni incluye automáticamente habilidades especializadas. |
| D-F-10 | Decisión interna: comprar pista solo cuesta DC, sin descuento extra de tiempo/score por comprar. | Conflicto con postura de Escape E-07, que mantiene penalizaciones propias. Óscar/Escape/E5 deben acordar separación; no se elimina lógica ni campos ajenos. |
| SHOP-01 | Marcos aplazados a V2+, sin tarifa aprobada. | Arte y condiciones futuras; no bloquea el objetivo V1. |
| SHOP-03 | Tres productos solo para demo interna: escudo 4 DC, elixir 3 DC y botiquín 4 DC. | Importes de simulación, no tarifas públicas, productos integrados ni promesa de efectos Quiz. |
| SHOP-02/08, 30_Decisiones_Escape | 3/5/8 DC es preferencia de negociación; 2/4/6 alternativa. Fixtures, tiers y clasificación editorial no son tarifas. | Fernando/Escape y economía de recompensas: ninguna escala aprobada para facturación. No se publican textos de pistas o soluciones. |

### Respuestas externas y conflictos de integración

Estas son posiciones documentales recibidas en coordinación el 15–16/10,
con síntesis actualizada al 17/10. No se ha reejecutado ni auditado aquí el código
de los juegos; faltan metadatos o evidencia en varias respuestas.

| Equipo / referencia | Respuesta funcional recibida | Conflicto o validación pendiente |
| --- | --- | --- |
| Training · T-02–T-06 | Finalización validada; cinco intentos por juego/día, Europe/Madrid; 2 XP Free / 5 XP Plus-Pro y 1 DC primera finalización válida de cada juego/día; repetición puede dar XP. Free tres juegos diarios, Plus/Pro catálogo de diez. | Son reglas locales comunicadas, distintas de T-01 candidato E5. ID canónico, reintentos, acuse Rewards/Bank, topes adicionales y membresías globales pendientes. No aprobar un premio por completar el cupo. |
| Training · T-08 | Explicación básica tras error gratuita; no hay extras de inventario confirmados en V1. | D-F-06 no impone Explicación Expandida o Seguro de Racha a Training. Estado real de integración y sus incidencias por acreditar. |
| Quiz · Q-01–Q-07 | Main como rama indicada, un participante mínimo, desempate score/aciertos/entrada; cierre manual/automático. Declara viabilidad conceptual de tácticos. | SHA y soporte real pendientes; respuestas mezclan podio con baremos alternativos y liquidación score→XP/DC desde GET. Contradicción explícita sin adoptar importes ni considerar is_settled integración Rewards/Bank. |
| Quiz · casos límite | Respuestas complementarias plantean XP sin DC para uno/dos participantes, pero también describen abonos por score tras abandono o cierre anticipado. | Reconciliar elegibilidad, XP fuera del podio, desconexión, cierre y reparto antes de fijar contratos. Q-01 económico no es la pregunta Q-01 de coordinación. |
| Escape · E-02/E-03 | Inicio con 0 DC sin mínimo acordado; prefiere liquidación C mixta: monedas por room completada, XP neta válida consolidada al cierre, bonus solo COMPLETED; parciales conservados según su respuesta. | Respuesta funcional del Equipo 4, no importes E-01 aprobados ni servicios integrados. Acordar tiempos/causas y no volver a pagar room/stage al cierre. |
| Escape · E-04/E-05 | Identidades propuestas por sesión/hito/destinatario, compra contextual de Hint, reintento y consulta posterior. | UniqueConstraint o HintUsage por sí solos no prueban cargo bancario único ni atomicidad con Bank. Firmas award_stage_xp/award_room_rewards/finalize_escape_rewards y claves son solicitudes candidatas, no contratos aceptados. |
| Escape · E-06/E-07 | Admite cobro único y relectura gratis; prefiere negociar 3/5/8, sin tarifa final. Mantiene penalizaciones de tiempo/score aunque los importes del fixture sean de prueba. | Conflicto con D-F-10. Distinguir precio económico, efectos del juego y XP provisional; nunca descontar XP histórica consolidada. No cerrar penalizaciones ni editar Escape por inferencia. |
| Óscar/Core · CORE-01–07 | Identidad, autorización del emisor, membresías, roles, saldo global, integración y épocas/apariencia siguen sin respuesta de cierre en el documento. | Profesor: PROF-01 baremos, PROF-02 alcance tácticos V1, PROF-03 pistas/penalizaciones. No confundir admin, plan de pago y especialización; P1 XP externa permanece abierto. |

## 0.1. Relación con lo integrado y próximos acuerdos

S1–S7-A locales están integrados según [arquitectura](../architecture.md);
S3 concede XP y puntos de nivel, S7-A gasta puntos disponibles: no sustituyen
Rewards ni el servicio de premios directos sin XP. El esquema vigente de A tiene
nueve entidades, incluida StatAllocationEvent, no RewardEvent/RewardRule/ItemGrant.
S8-A sigue aprobado y pausado. No se implementa ninguna de estas propuestas.

[Pendientes](../pending-decisions.md) conserva P1–P8, R1–R8 e I1–I9.
Para cerrar contratos: responsables confirman evidencia/fecha, hechos/identidades,
reglas y tarifas; Core valida permisos/fuente de saldo; A/B/C acuerdan servicios,
frontera transaccional y recuperación antes del ORM o adaptador afectado.

## 1. Tabla de soluciones y responsables

| **Integración**      | **Solución propuesta**                                                                                   | **¿Por qué conviene?**                                                                                       | **Responsable**                                      |
| -------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Ecomotor → Duckies   | Proponer `unlock_stage_items()` para coordinar desbloqueos; concesión y equipamiento pendientes en R-01. | Jaime controla la evolución y Henry el inventario. Evita duplicar piezas y conserva las anteriores.          | Henry implementa; Jaime define etapas y condiciones. |
| Shop → Duckies       | Crear `grant_item()` para entregar al inventario los objetos comprados.                                  | Centraliza las entregas, valida cantidades y niveles y evita duplicados. También sirve para Rewards.         | Henry implementa; Fernando integra.                  |
| Duckies → Shop       | Crear `get_item_ownership()` para consultar si el usuario ya posee un objeto.                            | Evita ofrecer compras innecesarias de objetos permanentes y permite consultar el inventario sin modificarlo. | Henry implementa; Fernando utiliza.                  |
| Shop → Bank          | Crear `debit_coins()` para descontar monedas y registrar el movimiento.                                  | Centraliza los gastos, comprueba fondos y evita cobros duplicados.                                           | Fernando implementa ambas partes.                    |
| Ecomotor → Bank      | Crear `credit_coins()` para conceder monedas por actividades recompensadas.                              | Ecomotor decide el premio y Bank controla el saldo. Evita acreditar dos veces la misma recompensa.           | Fernando implementa; Jaime integra.                  |
| Bank → Perfil global | Hacer que Bank opere sobre el saldo oficial del perfil, sin crear otro saldo independiente.              | Mantiene las DuckyCoins sincronizadas con toda la plataforma `notodoescodigo.com`.                           | Fernando + Óscar/Core.                               |
| Juegos → Ecomotor    | Crear `process_game_result()` para recibir resultados de partidas validados por el servidor.             | Centraliza XP y recompensas e impide que el cliente se conceda premios arbitrarios.                          | Jaime implementa; equipos de juegos integran.        |
| Juegos → Duckies     | Crear `consume_item()` para validar y descontar objetos utilizados en partidas.                          | Evita consumos duplicados, controla cantidades y registra el historial de uso.                               | Henry implementa; equipos de juegos integran.        |

**En las siguientes soluciones propuestas para cada contrato que queda por resolver para el equipo 5. Los códigos que se muestran en cada solución son solo ejemplos de lo que debería implementar el miembro al que le corresponda.**

## Contrato 1. Ecomotor → Duckies

Propuesta lista para aprobar

Responsables: Jaime define las etapas y confirma la evolución; Henry implementa la entrega de piezas.

Solución candidata: Ecomotor notifica la transición confirmada; Duckies controla la entrega y el equipamiento. El ejemplo `unlock_stage_items()` no presupone concesión automática aprobada: desbloquear, conceder/poseer, equipar y elegir apariencia son operaciones distintas.

```python
unlock_stage_items(
    user=user,
    stage_code="grecia",
    operation_key="evolution-15-grecia",
 )
```

| **Elemento**       | **Acuerdo propuesto**                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| **Entrada**        | Usuario, código de etapa, clave de operación                                       |
| **Validación**     | Etapa confirmada por Ecomotor, piezas configuradas y ausencia de entrega duplicada |
| **Acción**         | Se propone conceder piezas mediante grant_item(); condición y automatismo pendientes en R-01 |
| **Respuesta**      | Piezas entregadas, piezas ya poseídas y estado de operación                        |
| **Errores**        | Etapa inválida, operación no autorizada, conflicto de clave                        |
| **Regla especial** | DAR3 exige conservar piezas anteriores; equipamiento manual propuesto, sin cierre de R-01 |

Por qué: Ecomotor sigue siendo responsable de la evolución y Duckies de la propiedad de los objetos. Se evita almacenar inventarios paralelos.

Para cerrarlo: Jaime y Henry deben acordar códigos y contratos, adquisición, entrega y equipamiento. DAR3 contempla nueve épocas, seis piezas principales por época mediante progreso y misiones y conservación de progresos y conjuntos anteriores; la Parte A V2 utiliza siete etapas provisionales. El 15–16/10 ambos acordaron proponer a Óscar seleccionar libremente apariencias completas de cualquier época desbloqueada; no es una política aprobada. La entrega automática sin equipamiento sigue siendo una propuesta ERD, no un cierre aceptado.

## Contrato 2. Shop → Duckies

Propuesta lista para aprobar

Responsables: Henry implementa; Fernando utiliza.

Solución: Shop entrega objetos exclusivamente mediante grant_item().

```python
grant_item(
    user=user,
    item_code="escudo",
    level=2,
    quantity=1,
    source="shop",
    operation_key="purchase-527-line-1",
    reference_id="527",
 )
```

| **Elemento**     | **Acuerdo propuesto**                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| **Entrada**      | Usuario, objeto, nivel, cantidad, origen, referencia y clave                 |
| **Validación**   | Objeto válido, nivel compatible, cantidad positiva, propiedad y autorización |
| **Acción**       | Actualizar InventoryItem y registrar la concesión                            |
| **Respuesta**    | ID de entrega, cantidad y already_applied                                    |
| **Errores**      | Objeto inexistente, nivel inválido, objeto permanente ya poseído, conflicto  |
| **Idempotencia** | Registrar cada concesión con una identidad única persistente                 |

Por qué: centraliza las entregas y permite que Shop y Rewards utilicen la misma lógica.

Para cerrarlo: aprobar la firma del servicio y el registro persistente de concesiones, por ejemplo ItemGrant.

## Contrato 3. Duckies → Shop

Propuesta lista para aprobar

Responsables: Henry implementa; Fernando utiliza.

Solución: crear una consulta de propiedad que Shop pueda utilizar antes de vender un objeto.

```python
get_item_ownership(
    user=user,
    item_code="casco-romano",
    level=None,
 )
```

Respuesta ilustrativa candidata:

```python
{
    "owned": True,
    "quantity": 1,
    "is_consumable": False,
}
```

| **Elemento**        | **Acuerdo propuesto**                                    |
| ------------------- | -------------------------------------------------------- |
| **Entrada**         | Usuario, objeto y nivel opcional                         |
| **Validación**      | Usuario y objeto válidos                                 |
| **Acción**          | Consultar inventario sin modificarlo                     |
| **Respuesta**       | Propiedad, cantidad y si es consumible                   |
| **Errores**         | Objeto inexistente, nivel inválido, acceso no autorizado |
| **Regla de compra** | Permanentes no duplicables; consumibles acumulables      |

Por qué: Shop no necesita conocer las tablas internas de Duckies y puede mostrar correctamente qué objetos tiene el usuario.

Para cerrarlo: Fernando debe aceptar que esta consulta es informativa y que la validación definitiva se realiza durante la entrega transaccional.

## Contrato 4. Shop → Bank

Propuesta lista para aprobar

Responsable: Fernando, tanto en Shop como en Bank. Henry participa en las pruebas de compra y entrega.

Solución: Shop solicita a Bank el cargo correspondiente.

```python
debit_coins(
    user=user,
    amount=150,
    source="shop",
    operation_key="purchase-527-payment",
    reference_id="527",
 )
```

| **Elemento**       | **Acuerdo propuesto**                                           |
| ------------------ | --------------------------------------------------------------- |
| **Entrada**        | Usuario, importe, origen, compra y clave                        |
| **Validación**     | Fondos, importe positivo, autorización y operación no duplicada |
| **Acción**         | Descontar saldo y registrar movimiento                          |
| **Respuesta**      | ID del movimiento, importe, estado y already_applied            |
| **Errores**        | Fondos insuficientes, importe inválido, conflicto               |
| **Regla especial** | Cargo y entrega deben ser consistentes                          |

Por qué: Bank controla los movimientos económicos y Shop no modifica directamente el saldo.

Para cerrarlo: Fernando debe definir purchase_item() como coordinador del cargo y la entrega. Si las operaciones comparten una base de datos, utilizar una transacción común; si no, definir estados de compra y recuperación ante fallos.

## Contrato 5. Ecomotor → Bank

Propuesta lista para aprobar

Responsables: Jaime define recompensas; Fernando implementa el crédito.

Solución: Rewards solicita a Bank la concesión de monedas.

```python
credit_coins(
    user=user,
    amount=10,
    source="rewards",
    operation_key="reward-quiz-854-coins",
    reference_id="quiz-854",
 )
```

| **Elemento**     | **Acuerdo propuesto**                                            |
| ---------------- | ---------------------------------------------------------------- |
| **Entrada**      | Usuario, importe, origen, referencia y clave                     |
| **Validación**   | Recompensa autorizada, importe positivo y operación no duplicada |
| **Acción**       | Acreditar monedas y registrar movimiento                         |
| **Respuesta**    | ID del movimiento, importe y estado                              |
| **Errores**      | Recompensa no autorizada, importe inválido, conflicto            |
| **Idempotencia** | Una recompensa concreta solo puede acreditarse una vez           |

Por qué: Ecomotor controla las reglas de recompensas y Bank la economía. Ningún juego modifica directamente el saldo.

Para cerrarlo: Jaime y Fernando deben acordar cómo se construye el identificador único de cada recompensa.

## Contrato 6. Bank → Perfil global

Requiere confirmación de Core

Responsables: Fernando + Óscar/Core.

Solución: Bank utiliza la fuente oficial de DuckyCoins de notodoescodigo.com, sin almacenar un segundo saldo independiente.

Si Core confirma que el saldo oficial sigue siendo Profile.ducky_coins, se propone:

```text
BANK
├── get_balance()
├── credit_coins()
└── debit_coins()
        │
        ▼
Profile.ducky_coins
```

| **Elemento**         | **Acuerdo propuesto**                                |
| -------------------- | ---------------------------------------------------- |
| **Fuente del saldo** | Profile.ducky_coins, pendiente de confirmación       |
| **Lectura**          | get_balance(user)                                    |
| **Escritura**        | Operaciones autorizadas de crédito y débito          |
| **Registro**         | Movimientos contables de Bank                        |
| **Wallet**           | Puede existir como envoltorio, sin saldo duplicado   |
| **Seguridad**        | Acceso controlado y operaciones concurrentes seguras |

Por qué: las monedas pertenecen a toda la plataforma, no solamente al juego. Un único saldo evita inconsistencias.

Para cerrarlo: Óscar debe confirmar si Bank accederá mediante ORM o mediante un servicio global existente, y qué garantías transaccionales ofrece.

Este contrato no debería aprobarse definitivamente sin esa respuesta.

## Contrato 7. Juegos → Ecomotor

Propuesta lista para aprobar

Responsables: Jaime implementa; equipos de juegos integran.

Solución: los juegos envían resultados validados por el servidor a Ecomotor.

```python
process_game_result(
    user=user,
    game_code="quiz_battle",
    session_id="battle-854",
    result_id="result-854",
    score=850,
    correct_answers=8,
    total_questions=10,
 )
```

| **Elemento**     | **Acuerdo propuesto**                                         |
| ---------------- | ------------------------------------------------------------- |
| **Entrada**      | Usuario, juego, partida, resultado y métricas validadas       |
| **Validación**   | Partida legítima, finalizada y no procesada anteriormente     |
| **Acción**       | Registrar progreso, calcular XP y evaluar recompensas         |
| **Respuesta**    | Resultado procesado, XP aplicada y referencias de recompensas |
| **Errores**      | Resultado inválido, origen no autorizado, conflicto           |
| **Idempotencia** | Cada resultado se procesa una única vez                       |

Por qué: centraliza las reglas de progresión y evita que cada juego conceda directamente XP o monedas.

Para cerrarlo: Jaime y los equipos de juegos deben aprobar un formato común de resultados y las reglas de verificación.

## Contrato 8. Juegos → Duckies

Propuesta lista para aprobar

Responsables: Henry implementa; equipos de juegos integran.

Solución: los juegos solicitan el consumo de objetos a Duckies, que valida propiedad y cantidad.

```python
consume_item(
    user=user,
    item_code="turbo-preguntas",
    level=2,
    quantity=1,
    operation_key="battle-854-use-1",
    source_game="quiz_battle",
    session_id="battle-854",
 )
```

| **Elemento**       | **Acuerdo propuesto**                                            |
| ------------------ | ---------------------------------------------------------------- |
| **Entrada**        | Usuario, objeto, nivel, cantidad, juego, partida y clave         |
| **Validación**     | Propiedad, cantidad, nivel, autorización y operación no repetida |
| **Acción**         | Descontar inventario y registrar ItemUsage                       |
| **Respuesta**      | ID de consumo, cantidad y estado                                 |
| **Errores**        | Sin existencias, objeto inválido, uso no permitido, conflicto    |
| **Regla especial** | Coordinar consumo con aplicación del efecto                      |

Por qué: Duckies controla el inventario y los juegos únicamente aplican los efectos permitidos.

Para cerrarlo: Henry y los equipos de juegos deben definir cuándo se confirma el uso y cómo se recupera una operación si falla el juego.
