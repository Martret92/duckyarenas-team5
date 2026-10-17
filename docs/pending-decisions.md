# Decisiones pendientes · Consolidación V2 y Rewards v0

## 1. Marco vigente

D-20/D-21 registran el reparto y apps objetivo acordados internamente el 08/10.
No queda abierta la pregunta antigua sobre Jaime/Félix/Henry: D-13 se conserva
como antecedente. D-14…D-16 siguen sin aprobación técnica conjunta automática.
D-17, D-18 y D-19 continúan vigentes; no se reabre la política SQLite.

[Arquitectura](architecture.md) concentra requisitos documentales y conclusiones
de las dailys del 06, 07, 08, 09 y 13/10/2026, con su categoría y estado.
[Rewards v0](contracts/rewards-v0.md) es base técnica provisional, no contrato
global aprobado. El [ERD de Parte A](erd/ecomotor.md) conserva el antecedente V2
de ocho entidades y V2-A1…V2-A29 internas condicionadas; el esquema local integrado
añade StatAllocationEvent (S7-A, PR #32). No hay aprobación global del ORM compartido.

### 1.1. Criterio de clasificación y procedencia

Se recupera selectivamente la trazabilidad de
`feature/part-a-ecomotor-day4:docs/pending-decisions.md` (`c78be74`), preservando
los acuerdos posteriores de PR #21. Las referencias a PDFs siguientes proceden
de ese registro histórico; esta recuperación no supone una nueva consulta directa.
DAR3 conserva su autoridad principal; los acuerdos internos y ejemplos se distinguen
de sus requisitos y de los contratos externos todavía pendientes.

- **D:** definido documentalmente, indicando fuente y ámbito.
- **E:** ejemplo o propuesta no vinculante, sin parámetros oficiales por defecto.
- **X:** contradicción normativa o ambigüedad funcional real que requiere aclaración.
- **C:** coordinación externa con Core, propietarios o consumidores afectados.
- **I:** decisión interna resoluble sin modificar contratos ni código ajenos.
- **F:** fase o alcance de entrega, sin eliminar el requisito global.

Un punto puede tener varias categorías. Dos ejemplos diferentes no constituyen
necesariamente requisitos incompatibles. Estas etiquetas no crean decisiones D
ni aprueban alternativas; P1–P8, R1–R8 e I1–I9 conservan sus identificadores.
R1–R8 de Rewards no son los mismos identificadores que R-01…R-14 del ERD global.

### 1.2. Ejemplos técnicos y preguntas residuales

| Referencia | Evidencia histórica y categoría | Qué falta acordar / relación |
| --- | --- | --- |
| E-F1 · Redondeo XP | E: DAR_DuckyClash p. 18 ilustra 20,7 → 21; DAR_formulas p. 15 usa `math.floor(total_xp)`. Son variantes ilustrativas. | Política de redondeo antes de premios reales y coordinación si afecta al contrato; I/C, vinculada a I9/R8. No se escoge una variante. |
| E-F2 · Rapidez y VEL | E: DAR_formulas pp. 2 y 7 describe umbrales temporales/rapidez; su snippet de p. 14 suma `VEL*0.01`. No prueba dos mandatos incompatibles. | Precisar efecto sobre tiempos o multiplicadores, escala, límites e intervalos; I/C, I9/R8. No se adopta el multiplicador del ejemplo. |
| E-N1 · Umbrales de nivel | E: tabla de ejemplo de DAR_DuckyClash p. 23 frente a `1 + XP//10000` de DAR_formulas p. 27. | P8: valores/configuración oficiales. LevelThreshold y S1 siguen parametrizables; no se fija 10.000 XP por nivel. |
| E-N2 · Puntos por nivel | E: frecuencias ilustrativas de DAR_DuckyClash pp. 23–24 y +1 por nivel en DAR_formulas pp. 12 y 27. | P2/P8: cantidades y frecuencia oficiales; `stat_points_awarded` configurable, sin convertir +1 en regla. |
| E-I1 · Modalidad de Escape | D: DuckyEscape p. 1 describe juego individual. E: DAR_DuckyEscape__modelos pp. 1–10 propone estructura extensible con sesiones/equipos. | I1: confirmar versión integrada y contrato parcial/final; multijugador es posible ampliación F/C, no modalidad adoptada ni bloqueo del caso individual. |

Los auxiliares históricos X-F1/X-F2/X-N1/X-N2/X-I1 pasan a E-F1/E-F2/E-N1/E-N2/E-I1
porque describen ejemplos o extensiones. Esta trazabilidad no reabre V2-A21:
siete etapas aceptadas internamente, sin resolver globalmente su adaptación a
las nueve épocas de DAR3. P1 (XP externa), P2 (aplicación de stats) y P4/D-17
(User/auth) conservan sus ambigüedades o contradicciones reales y responsables.

## 2. Aclaraciones prioritarias con Óscar / Core

Óscar es también interlocutor de Core. Una respuesta parcial no cierra el diseño
físico ni autoriza el servicio afectado; los parámetros configurables no bloquean
por sí solos toda la revisión conceptual.

| ID | Evidencia / estado | Pregunta de cierre | Validadores e impacto |
| --- | --- | --- | --- |
| P1 · XP externa | Daily del 09/10/2026: rectificación funcional, en tensión con Ecomotor pp. 1–2 y 6 | ¿XP solo juegos afecta a histórica o también dominio? ¿Qué actividades externas conservan monedas, objetos o puntos? ¿Desde cuándo, qué ocurre con usuarios/recompensas existentes y cómo configurar nuevas actividades? Confirmación escrita sin borrados, recálculos ni conversión automática de todas las actividades externas a premios sin XP. | Óscar, Jaime/Core; bloquea elegibilidad definitiva y migración afectada, no el contrato conceptual. |
| P2 · Stats | Daily del 09/10/2026: stats por rol antes de Actual y distribución/edición en Actual, aclaración parcial. S7-A integrado (PR #32) resuelve internamente asignación solo en Actual, coste 1:1 e historial idempotente; no es aprobación global del profesor. | Siguen abiertos iniciales, tabla/presupuesto, límites, redistribución, efectos al especializarse y demás condiciones funcionales. No adoptar todos a 5, tabla de Clash o suma de 45 como defaults oficiales. | Óscar, Jaime, Henry y juegos; S2-A/S7-A locales existen, parámetros y límites funcionales siguen pendientes. |
| P3 · Cursos | Daily del 09/10/2026: ejemplos de objetos y puntos; bonificación diaria de XP propuesta, no confirmada. Daily del 13/10/2026: corrección automática en LMS, insignias y posible relación futura con Bank; euros/cotización mencionados sin especificación | ¿Qué premios, condiciones, efectos/consumos, cantidades y cobertura V1? ¿Cómo conceder puntos sin ascenso de nivel ni XP? LMS/Bank es una expectativa futura: sin premios, cantidades, XP, conversión económica, contratos o alcance V1 definidos; no resuelve P1. | Óscar y A/B/C; reglas, puntos e integración externa. |
| P4 · User/auth | Sin respuesta nueva; conflicto PR07/D-09/D-10 bajo D-17 | User estándar/CustomUser, autenticación/JWT, origen autorizado, permisos e integración común. No crear auth paralela. | Óscar/Core y Equipo 5; exposición externa y migraciones. |
| P5 · Conservación | Pendiente; M-01 fail-closed interno preservado | Retención, anonimización/eliminación de User, perfiles, stats, Rewards y movimientos; referencias, borrado y tratamiento legacy. | Óscar/Core y A/B/C; FKs/on_delete y migraciones definitivas. |
| P6 · Vestimenta/Museo | DAR3 contempla progreso y misiones y conservación de progresos y conjuntos anteriores; arquitectura y ERD global consolidados por PR #21. | R-01 sigue mixto/pendiente: separar adquisición de piezas y posibles variantes comprables, concesión/posesión, equipamiento automático y selección de apariencia. Acordar condiciones al saltar etapas, compatibilidad, Museo y adaptación de nueve épocas a siete etapas V2 provisionales. La selección libre de apariencias completas desbloqueadas es propuesta a Óscar, no política adoptada; no se rebaja la conservación prevista en DAR3. | Óscar, Henry y Fernando, con Jaime para evolución; ERD consolidado y vertical. |
| P7 · Especializaciones | Actual aclarado; selección/rangos parciales | Obligatoriedad, acceso, cambios/reinicio/nueva elección no aprobados, XP de dominio y rangos Junior/Middle/Senior/Maestro. Normalizar Sistemas/AdminSys, Data/Data & IA y códigos sin adoptar ejemplos. | Óscar, Jaime y juegos; catálogos y servicios. |
| P8 · Umbrales/configuración | Invariantes V2-A20/A21 y carga JSON/diagnóstico S6-A ya implementados localmente; INITIAL_CONFIGURATION sigue ausente. | Valores autorizados, instalación real por proceso y cambios históricos prospectivos/retroactivos sin rebajar progreso ni reconceder puntos silenciosamente. S6-A no activa el servidor ni aprueba producción. | Óscar/Jaime y Core si afecta a migración; administración y reconciliación. |

### Integración pendiente con Core y servicios económicos comunes

Dailys del 06, 07 y 09/10/2026: se habló de funciones anteriores de recompensas,
puntos y monedas. Daily del 13/10/2026: el controlador antiguo sencillo descrito
para incrementar DuckyCoins no es de reutilización obligatoria ni debe esperarse
para avanzar. Esta aclaración no declara desaparecidos todos los componentes
anteriores de recompensas, puntos o economía.

- **Aclarado:** el controlador antiguo no bloquea el desarrollo de nuestros servicios.
- **Pendiente:** acordar con Óscar/Core, Jaime, Fernando, Henry y consumidores
  Wallet/saldo canónicos, identidad, autorización, movimientos contables,
  idempotencia, concurrencia, punto común de concesión y contratos A/B/C/juegos.
  Reconciliar modelos y migraciones A/C antes de integrar; no se resuelve aquí
  el conflicto conocido de versiones de `ecomotor.0001_initial`.
- **Opcional:** consultar código anterior si resulta útil, sin condicionar el avance
  a recibirlo ni asumir firmas o modelos no verificados.

La autonomía expresada permite continuar y trasladar dudas a Óscar, sin dar por
cerrados esos contratos ni validar las ocho interfaces propuestas por Henry.
No se aprueba una segunda Wallet, otro saldo canónico ni la integración económica.
D-21 y Rewards v0 conservan su estado interno/candidato y validación conjunta pendiente.

## 3. Validación conjunta de Rewards v0

Los principios están aceptados provisionalmente como propuesta, no como decisión
D nueva ni ORM. Las preguntas siguientes concretan el contrato; no reabren
por sí solas la autoridad funcional de Ecomotor, Bank o Duckies.

DAR3 pp. 49 y 52–53 ya describe un intercambio mínimo y protección funcional
contra duplicados. Lo pendiente es el contrato técnico compartido completo:
huella canónica (R2), estados APPLIED/NO_REWARD y ORM de trazabilidad (R3), y una
transacción exterior compartida (R4) son mecanismos candidatos, no requisitos
físicos impuestos por esos mínimos. La conformidad conceptual Jaime–Henry de
R-05/R-08 del ERD global no ratifica esos detalles con Fernando/Core/juegos.

| ID | Decisión técnica pendiente | Validadores / condición |
| --- | --- | --- |
| R1 · Identidad y autorización | Origen autorizado, hecho y destinatario; estabilidad, unicidad, clases de hechos y rechazo de emisor/identidad no verificados. | Jaime, Óscar/Core y juegos antes del contrato externo. Un header por sí solo no autoriza. |
| R2 · Huella y conflictos | Canonicalización, contenido validado incluido, algoritmo y diferencias compatibles; relación entre claves globales y locales. | A/B/C/Core/juegos antes del ORM de trazabilidad y reintentos. |
| R3 · Resultado y reglas | Representación persistente de resultado/motivo, versión reproducible, referencias a efectos, APPLIED/NO_REWARD y recuperación de duplicados. ¿Cómo se representan reglas configurables sin aprobar RewardRule como tabla? | Jaime, Henry y Fernando; FKs y estados físicos no aprobados. |
| R4 · Transacción exterior | Validar misma BD y conexión/alias, ausencia de commits independientes y cobertura de evaluación/límites/efectos/registro. Si no se cumple, acordar recuperación antes del flujo afectado. | A/B/C y Core; propuesta de monolito modular, D-19 no implica atomicidad global. |
| R5 · Premios sin XP | Servicio independiente de puntos, objetos y monedas; referencias causales; no duplicar puntos de nivel y premio directo; trazabilidad de dominio sin reutilizar XPEvent histórico. | Jaime, Henry y Fernando; no añadir novena entidad al ERD mínimo automáticamente. |
| R6 · Límites temporales | Training: juego, día/zona horaria, instante de actividad o registro, hechos tardíos y competencia entre actividades distintas. | Jaime y Training/Óscar; una moneda por juego/día no equivale a deduplicar una partida ni a limitar intentos. |
| R7 · Correcciones/incidentes | Hechos corregidos, NO_REWARD final, ajustes, devoluciones y reintentos tras fallo; política ante cambio de reglas. | A/B/C/Core/Óscar; no reescribir resultados previos ni convertir fallos en NO_REWARD. |
| R8 · API documentada | Adaptación a calculate-action/commit-rewards: significado de cantidades/stats, validación y respuesta; atomicidad de batch y resultados por destinatario. | Jaime, Core y juegos; conservar referencias de DAR_formulas, no aprobar otra API incompatible. |

La referencia de R5 al ERD mínimo corresponde al antecedente de ocho entidades:
S7-A ya añade StatAllocationEvent, que registra gasto/asignación de puntos locales,
no concesión de puntos como premio ni trazabilidad global Rewards. R1–R8 siguen
abiertos; S2-A/S3/S7-A no aprueban por inferencia sus mecanismos compartidos.

## 4. Juegos, compras y alcance V1

| ID | Evidencia / asunto pendiente | Validadores y siguiente paso |
| --- | --- | --- |
| I1 · Escape | Daily del 09/10/2026: XP válida de stages completados conservada y premio final independiente; PDF local contempla penalización provisional. Stage y habitación son distintos; sin moneda por stage no se eliminan automáticamente premios por habitación. Versión consolidada más reciente no identificada. | Óscar y Escape/Jaime: obtener versión, acordar cuándo consolidar parciales/finales, identidad y penalizaciones sin descontar XP histórica. |
| I2 · Training | PDF y reunión reiteran XP repetible y moneda diaria. Acceso gratuito/membresía sigue parcialmente ambiguo. | Training/Óscar: aclarar acceso separado del contrato de premios; no adoptar moneda única para toda la vida propuesta por participantes. |
| I3 · Clash/apuestas | Daily del 09/10/2026: reserva de ambas apuestas al aceptar. DAR3 p. 42 no exige apuestas en primera entrega. | Fernando, Clash y Óscar: confirmar V1 y reserva, liberación, liquidación, cancelación, timeout, claves y saldo disponible/reservado. |
| I4 · Compra | Ecomotor pp. 4–5 participa en comprobaciones; Shop proceso comercial, Bank fondos y Duckies entrega. | A/B/C: fijar coordinador, validaciones, claves y frontera transaccional/recuperación de compra, sin duplicar saldo ni aprobarlo por Rewards v0. |
| I5 · Objetos y equipo | Catálogo mínimo, efectos/consumos, precios, caducidad, roles y vestimenta sin cerrar; compra por rol es preferencia de Óscar. Daily del 13/10/2026: recursos gráficos publicados en Classroom, localización comunicada internamente por Henry; no es aprobación funcional. | Henry/Fernando con Jaime/juegos/Óscar: inspeccionar materiales, separar imágenes compuestas y normalizar tamaños; acordar catálogo y compatibilidad. Los gráficos no fijan códigos, precios, efectos, duraciones, consumos ni V1. No confundir tipos de combate con productos Shop. |
| I6 · REST/realtime/RPG | DAR_formulas documenta REST y sockets de Ecomotor; cobertura y ownership realtime pendientes. DukiStats 2.0 es propuesta de participante. | Óscar/Core, Equipo 5 y juegos: productores/consumidores, infraestructura, permisos y alcance V1 sin descarte unilateral. |
| I7 · Evaluación PR07 | ERD/diccionario antes de ORM, CRUD, permisos/tests/evidencias. Daily del 06/10/2026: plan diario aclarado como guía, no calendario literal obligatorio. | Óscar y Equipo 5: CRUD evaluable y planificación. El 19/10 se vincula a exámenes/prácticas, no a entrega final confirmada. |
| I9 · Quiz | Daily del 09/10/2026: tiempo, aciertos, stats y resultados intervienen en el cálculo, sin cifras obligatorias de ejemplo. | Jaime, Quiz y Óscar: validar resultado, datos de cálculo y contrato conjunto. |
| I8 · Cobertura | Demo DAR3, historiales/Museo, integraciones externas y pedidos físicos por priorizar. | Óscar y Equipo 5: vertical mínima y contenido V1. No reducir obligatoriamente a Quiz por debate de participantes. |

## 5. Trabajo interno y verificación

D-20 fija responsables; D-21 apps objetivo. Siguen por revisar detalles de catálogo
objetos/comercial de D-15 y política de datos provisionales D-16; el acuerdo de
organización no los confirma por extensión.

- Revisar conjuntamente contrato Rewards y diseños B/C antes de integrar la rama
  de Fernando; esta consolidación no modifica ni valida esa rama.
- Consolidar ERD/diccionarios A/B/C y borrado acordado antes del ORM compartido
  afectado. Conservar la trazabilidad V2 de ocho entidades y reconocer la novena
  integrada por S7-A; M-01, V2-A20/A21 y conservación siguen vigentes.
- S1/S1.1, modelos/migraciones de Día 4 y Admin de Día 5 ya están integrados
  (PR #22–#25). Las funciones puras y pruebas aisladas de Parte A pueden avanzar
  sin esperar la integración global; no se inventan parámetros ni seeds oficiales.
- R-12 y S2-A1/S2-A2 ya se materializan en S2-A (PR #27): inicialización local
  atómica e idempotente de perfil/stats para User existente, sin signals, con
  configuración confiable. No sustituye alta global Ducky/Wallet, conservación
  legacy, identidad/auth o contratos Core.
- S3 (#28) ya concede XP histórica/puntos de nivel/evolución; S4-A (#29) consulta
  progreso e historial; S5-A (#30) ofrece lectura personal local; S6-A (#31) carga
  JSON y diagnostica sin instalar; S7-A (#32) gasta puntos 1:1 solo en Actual e
  historiza con idempotencia. Configuración funcional e instalación real pendientes.
- Parte A puede diseñar/probar elegibilidad y reglas de Rewards con funciones puras
  o fakes. Estos servicios locales no resuelven XP externa P1, APIs, trazabilidad
  global, concesión directa de puntos sin XP ni contratos económicos. Integrar
  Fernando exige reconciliar migraciones y fuente canónica, sin saldo paralelo.
- Hay tests locales de replay/conflictos, rollback, migraciones, permisos HTTP y
  concurrencia SQLite file-backed S2-A/S3/S7-A. La última regresión comunicada es
  de 407 tests correctos; DOC-1 no los ha reejecutado. Premios sin XP, límites diarios
  multidominio y contratos siguen pendientes de implementación/integración.
- Admin y consulta personal están integrados; S8-A GET/POST de asignación está
  aprobado internamente por Jaime y pausado, sin implementar. CRUD evaluable,
  especializaciones/XP de dominio, historiales/Museo global y evaluación PR07 siguen
  abiertos. P1, P3–P7 y R1–R8 no se cierran por estos avances locales.
  [Plan de trabajo](team5-work-plan.md) concentra hitos y responsables.

El cierre de una pregunta requiere evidencia y actualización del registro cuando
corresponda. Publicar una propuesta no equivale a validación conjunta.

## 6. Aclaraciones parciales DOC-2 · 18/10/2026

Fuentes y categorías en la [matriz canónica de integración](contracts/integracion-equipo5-v0.md#0-matriz-de-procedencia-y-acuerdos--doc-2).
Se conservan los identificadores y preguntas anteriores; esta sección precisa
su cierre residual sin declarar integraciones globales por avances locales.

| Referencia vigente | Información incorporada | Qué permanece abierto |
| --- | --- | --- |
| P1 / P3 | E5-04 no fija recompensas. Training comunica reglas locales y no confirma extras de inventario V1; explicación básica gratuita. | XP externa, cursos/LMS, premios directos sin XP y cobertura; S7-A asigna saldo disponible, no concede premios externos. |
| P2 / P7 | S7-A resuelve asignación local en Actual, 1:1 e historial; el catálogo propone capacidades de maleta y reglas por rango. | Iniciales, presupuesto/límites, redistribución, especializaciones, XP de dominio y relación de rangos con Core; no adoptar rangos antiguos por una tabla de maleta. |
| P4 / P5 | CORE-01–06 siguen pendientes; E5-03 plantea Bank único para toda la plataforma. | Identidad, permisos/autorización, membresías, fuente física de saldo, retención y legacy. No crear Wallet/saldo paralelo ni modificar User. |
| P6 / I5 | E5-02 afirma vestimenta completa y autoequipamiento; catálogo D-F-07 trata transformación y variantes. | Conflicto DAR3/seis piezas/nueve épocas frente a V2/siete etapas; adquisición, entrega, equipamiento y apariencia sin cierre. Transformación/variantes requieren Henry/Jaime/Fernando. |
| P8 | S6-A carga/diagnostica; catálogo tiene parámetros internos y precios candidatos. | Valores autorizados, activación real y política histórica; ninguna decisión de la hoja se instala como configuración oficial. |
| R1 / R2 | E5-01/E5-05 y kit proponen hecho estable/origen/destinatario, adaptadores y recuperación del duplicado. | Firma, versión, transporte, autorización Core, huella canónica y conflictos; sin API aprobada. |
| R3 / R4 | R-05/R-08 tienen conformidad conceptual previa; E5-03 condiciona rollback a conexión/BD compartidas. | RewardEvent/RewardRule/ItemGrant, estados y campos físicos, reglas, referencias y recuperación remota; D-19 no da atomicidad global. |
| R5 / R6 / R7 / R8 | Respuestas externas distinguen intentos, parciales/final y límites; S3/S7-A cubren sus operaciones locales. | Premios directos/dominio, zona/ciclo y límites compartidos, correcciones, batch y compatibilidad REST; no ratificar ejemplos del kit. |
| I1 | Escape elige funcionalmente C mixta: room en curso, XP al cierre, bonus solo al completar; inicio sin mínimo de DC. | Contrato parcial/final y acuses, sin doble pago; documentos y servicios consolidados por verificar. E-01 sigue sin aprobar importes. |
| I2 | Training comunica 2 XP Free / 5 Plus-Pro, una DC primera finalización por juego/día y cinco intentos; son respuestas locales. | Reconciliar propuesta T-01, evento estable, topes adicionales, reglas globales y membresías; no confundir intento con recompensa duplicada. |
| I9 | Quiz responde sobre ranking/cierre y viabilidad táctica, con casos límite y cifras contradictorias. | Score→XP/DC, pago en GET, uno/dos participantes, abandonos, podio, SHA, soporte real y consumo; Q-01 no ratificado. |
| I4 / I5 / I8 | Catálogo atribuye objetivo seis tácticos Shop V1 al usuario, condicionado a Quiz; marcos V2+; demo interna 4/3/4 DC. | Acuerdo funcional con Equipo 1/Core, compra/cobro/entrega, reservas y producción; 4/3/4 no es tarifa de venta pública. |
| I1 / I4 | Preferencia 3/5/8 DC y alternativa 2/4/6; Escape acepta cobro único/relectura gratuita pero mantiene penalizaciones. | Ninguna tarifa aprobada. Conflicto D-F-10/E-07: separar coste y penalizaciones con Escape/Óscar sin eliminar campos o efectos por inferencia. |
| I3 / I6 / I7 | La nueva coordinación no resuelve Clash, integración REST/realtime ni evaluación. | Apuestas condicionales, ownership realtime, contratos globales y entregables PR07 continúan pendientes. |

E5-01…E5-05 son IDs del documento de respuestas, no nuevas decisiones D.
Las hojas atribuyen decisiones al usuario; no acreditan ratificación A/B/C o de
los consumidores. S8-A sigue pausado. No se modifican servicios ni datos reales.
