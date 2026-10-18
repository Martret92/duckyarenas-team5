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
| P5 · Conservación | Pendiente; M-01 fail-closed interno preservado. S12-A solo acepta DomainXPEvent conceptual. | Retención, anonimización/eliminación de User, perfiles, stats, Rewards y movimientos; referencias, borrado y legacy. DomainXPEvent físico y sus relaciones requieren acuerdo previo de conservación, anonimización/eliminación y on_delete; sin copiar CASCADE provisional. | Óscar/Core y A/B/C; FKs/on_delete y migraciones definitivas. |
| P6 · Vestimenta/Museo | DAR3 conserva seis piezas por época obtenidas por progreso/misiones y conjuntos anteriores. DOC-5 (18/10) concreta la propuesta E5: conjunto completo por época, adquisición/autoequipamiento al evolucionar y reutilización de anteriores obtenidos también en épocas intermedias; futuras no alcanzadas excluidas. | CORE-07, B-06 y R-01 abiertos: Óscar debe aclarar piezas diferenciadas/composición de conjuntos, entrega automática frente a progreso/misiones, aprobación de adquisición/autoequipamiento y reutilización, y nueve épocas (Era Espacial incluida) frente a siete etapas provisionales. Mantener compatibilidad, saltos y Museo pendientes; no asumir un único Item por conjunto. | Óscar para aclaración funcional; Henry/Jaime para identidades, idempotencia, adquisición/equipamiento y recuperación; Fernando si afecta a comercio. |
| P7 · Especializaciones | S11-A integrado (#44), S12-A conceptual (#45), S13-A1 puro integrado (#47) y S14-A-01…07 aprobados internamente, sin servicio de cambio implementado. | Abiertos códigos canónicos, obligatoriedad/acceso adicional, concreciones de cambio y compatibilidad S11-A, reinicios, fuentes/importes de dominio, autorización de evidencias, persistencia/confirmación de rangos y recompensas tardías. No cerrar P7 ni activar baremos. | Óscar, Jaime y juegos; [S11-A](contracts/ecomotor-specialization-v1.md), [S12-A](contracts/ecomotor-domain-xp-v1.md), [S13-A1](contracts/ecomotor-ranks-evaluator-v1.md) y [S14-A](contracts/ecomotor-specialization-switch-v1.md), sin ratificación global Core. |
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

**Estado DOC-3 · 18/10/2026:** Jaime aprobó internamente R1–R8 para orientar
Parte A, conforme al [registro de acuerdos](decisions.md#doc-3--arquitectura-rewards-v1--acuerdos-internos-de-parte-a--18102026).
No es ratificación A/B/C ni aceptación de Óscar/Core/juegos; el contrato compartido
sigue en v0 candidato. Ninguna fila queda cerrada completamente. DOC-4 concreta
T1–T8 internamente; la tabla incorpora ese avance sin cerrar validaciones
compartidas, detalladas también en [§7](#7-validación-residual-del-diseño-técnico--doc-4).
Fase 1 está integrada por PR #38; DOC-6 concreta persistencia/XP local internamente
en [§9](#9-bloqueos-de-persistencia-rewards-f2-a--doc-6), sin cerrar R1–R8 ni autorizar
la tabla o migración. La serialización pura de §7 ya tiene implementación local;
campos por juego, mapeo User y aceptación compartida siguen pendientes.

DAR3 pp. 49 y 52–53 define el intercambio mínimo y la protección funcional contra
duplicados. Los mecanismos internos elegidos no se atribuyen como nuevos requisitos
físicos del profesor. La conformidad conceptual previa Jaime–Henry de R-05/R-08
no aprueba los detalles restantes con Fernando/Core/juegos.

| ID | Aprobado internamente por Jaime · DOC-3 | Pendiente técnico / externo | Validadores / condición |
| --- | --- | --- | --- |
| R1 · Identidad y autorización | Terna origen autorizado/hecho estable/destinatario; reintento conserva identidad y emisor/resultado se validan en servidor. | T1/T2 fijan User vía AUTH_USER_MODEL, terna lógica y fact_id opaco de 1–255 caracteres. Pendientes códigos/clases por origen, unicidad física, mapeo User y autorización con Core/juegos. | Jaime, Óscar/Core y juegos; un header declarado no autoriza. |
| R2 · Huella y conflictos | Huella semántica validada; equivalencia recupera resultado previo e incompatibilidad genera conflicto sin nuevos efectos. | T2 elige SHA-256/JSON canónico versionado, claves ordenadas, UTF-8 y fechas UTC. Fase 1 concreta la serialización pura; pendientes campos semánticos por juego y su aceptación compartida. T4 fija SHA-256 de identidad y prefijo XP rewards:v1:, no su codificación exacta. | A/B/C/Core/juegos antes del esquema de trazabilidad y adaptadores. |
| R3 · Resultado y reglas | RewardEvent conceptual persistente global, identidad/huella/versionado/resultado/motivo/efectos; finales APPLIED/NO_REWARD, errores técnicos excluidos. | T3 esboza RewardEvent y OneToOne XPEvent opcional candidatos; T5 plantea RewardDecision y configuración versionada. Pendientes esquema definitivo, índices, FKs/on_delete, snapshot/causalidad y conservación; sin tabla RewardRule ni migración aprobada. | Jaime, Henry, Fernando y Core para conservación; sin migraciones aprobadas. |
| R4 · Transacción exterior | Cubre evaluación, límites, efectos y registro si comparten BD, conexión/alias y frontera transaccional; respeta D-19. | T4 coordina RewardEvent/S3 bajo transacción exterior del mismo alias; T6 propone cupo en esa frontera. Confirmar participación real y ausencia de commits independientes. Con Bank/Duckies remotos, recuperación distribuida pendiente. | A/B/C y Core; D-19 no garantiza atomicidad global o entre destinatarios. |
| R5 · Premios sin XP | Efectos independientes, sin XPEvent ficticios, servicios propietarios y separación de puntos de nivel/directos. | T4 reutiliza S3 solo con XP positiva, sin inicialización; T5 separa evaluación/efectos. Servicio de puntos directos, dominio, referencias causales y contratos Bank/Duckies pendientes; no confundir con gasto S7-A. | Jaime/Henry/Fernando; ninguna nueva entidad física aprobada por esta decisión. |
| R6 · Límites temporales | Repetición/límites configurables por regla, usuario, actividad y periodo; XP/monedas separados; protección concurrente. | T6 propone RewardLimitUsage, unicidad y cupos concurrentes separados para XP/monedas, sin activar límites económicos antes de Bank. Día efectivo, hechos tardíos, cambios de regla e importes pendientes; Europe/Madrid/primera DC diaria son información local de Training. | Jaime, Training y Óscar/Core según ámbito; validar contrato técnico de límites sin ratificar T-01. |
| R7 · Correcciones/incidentes | Fallo técnico nunca NO_REWARD; recuperar confirmados con identidad original; corregir mediante operación nueva vinculada, sin sobrescritura silenciosa. | Políticas de ajuste/retirada de XP, niveles, monedas u objetos; representación de vínculos, incidentes y devoluciones. No se autoriza reducir XP histórica por inferencia. | Cada propietario y Core/Óscar para consecuencias compartidas y conservación. |
| R8 · API documentada | Negocio en apps.ecomotor y adaptadores; calculate-action no concede premio definitivo; commit-rewards aplica R1–R7 y valida cantidades. | T7 propone ValidatedRewardFact/RewardResult y process_reward, no firma definitiva. JWT/permisos, formatos/versiones, excepciones concretas, batch, atomicidad entre destinatarios, WebSockets y publicación HTTP pendientes. | Jaime, Core y juegos; conservar ambas rutas DAR_formulas sin inventar endpoints oficiales. |

S7-A añade StatAllocationEvent al esquema local de nueve entidades: registra gasto
de puntos, no premios directos ni evaluación global Rewards. R1–R8 siguen abiertos
en su validación residual; S2-A/S3/S7-A no ratifican esos contratos por inferencia.

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

Este apartado conserva el contraste DOC-2 anterior a la aprobación interna DOC-3;
para el estado actualizado de R1–R8 prevalece §3, sin cerrar sus pendientes externos.
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

## 7. Validación residual del diseño técnico · DOC-4

Aprobación interna de Jaime del 18/10/2026: [T1–T8](decisions.md#doc-4--diseño-técnico-rewards-v1--t1t8--18102026).
No es contrato de Core/Henry/Fernando/juegos ni autorización de migraciones.
P1–P8 e I1–I9 no cambian; R1–R8 conservan sus validaciones residuales de §3.

| Fase / diseño | Pendiente que condiciona el avance | Responsables |
| --- | --- | --- |
| Núcleo puro · T2/T5/T7 | Integrado por PR #38: tipos/validaciones, JSON canónico versionado, huella y evaluador puro. Pendientes semántica por juego, autorización y configuración real; reglas ficticias de tests no activan premios. | Jaime, revisión de cada PR; juegos para semántica real. |
| Persistencia/XP · T1/T3/T4 | Esquema candidato, integridad/unicidad, vínculo XPEvent y alcance OneToOne frente a batch/dominio; conservación/on_delete con Core; snapshot y causalidad suficientes, sin reinterpretar S3. | Jaime y Core; propietarios afectados para sus referencias. |
| Cupos · T6 | Esquema RewardLimitUsage e identidad de ámbito/periodo, día efectivo/hechos tardíos/cambios de regla y pruebas concurrentes bajo D-19. Nada económico se activa sin contrato Bank. | Jaime, Training/Core y Fernando en economía. |
| Propietarios/transporte · T7/T8 | Contratos físicos Bank/Duckies, fuente económica, autorización/JWT, payloads/errores/versiones, lotes, atomicidad por destinatarios, REST/WebSockets y recuperación remota. | Jaime, Henry, Fernando, Core y juegos. |
| Correcciones · R7 | Política de hechos tardíos y ajustes/retirada de XP, niveles, monedas y objetos; vínculos/auditoría, conservación y recuperación entre BD independientes. | Cada propietario y Core; ninguna retirada aprobada por DOC-4. |

No se ratifican T-01/Q-01/E-01, precios Shop, configuración oficial de juegos,
penalizaciones Escape, vestimenta o transformación de inventario. Los modelos
RewardEvent/RewardLimitUsage son candidatos; RewardRule no se adopta como tabla.
S8-A sigue aprobado y pausado; ninguna fase se implementa en este PR.

## 8. Vestimentas históricas · Propuesta DOC-5

Consulta del 18/10/2026 de CORE-07, E5-02 y B-06 en el documento compartido de
coordinación, contrastada con DAR3 pp. 3 y 48. [DOC-5](decisions.md#doc-5--criterio-funcional-propuesto-de-vestimentas-históricas--18102026)
registra procedencia y autoridad; la [arquitectura](architecture.md#31-vestimentas-históricas--propuesta-doc-5)
precisa adquisición, posesión, equipamiento y apariencia. El criterio E5 ya está
formulado: conjunto completo por época, adquisición/autoequipamiento al evolucionar,
conservación y libre reequipamiento de anteriores obtenidos también durante épocas
intermedias, sin permitir futuras no alcanzadas. **No es aprobación del profesor
ni contrato técnico ratificado con Henry.**

**CORE-07, B-06, P6 y R-01 permanecen abiertos.** La duda residual es la validación
de esa propuesta frente a DAR3, no su mera formulación. Óscar debe confirmar:

1. Si las seis piezas principales por época siguen siendo objetos diferenciados
   y cómo se relacionan con una apariencia de conjunto completo.
2. Cómo encaja adquirir automáticamente el conjunto al evolucionar con los
   desbloqueos por progreso y misiones de DAR3.
3. Si aprueba adquisición y equipamiento automáticos y reutilización libre de
   conjuntos anteriores ya obtenidos, también durante épocas intermedias.
4. Cómo se relacionan las nueve épocas DAR3, incluida Era Espacial, con las
   siete etapas provisionales de DuckyEcomotor.

Jaime y Henry acordaron plantear reutilización al profesor; no se atribuye a Henry
aceptación técnica inequívoca de todos los detalles del autoequipamiento. Tras la
aclaración funcional, la futura implementación requerirá acordar con Henry las
identidades de época/conjunto/piezas, idempotencia, adquisición, equipamiento y
recuperación de errores. Nada fija aquí modelos, composición, transacciones o firmas.
Se conserva el R-01 histórico mixto; no se modifica DAR3 ni se cierran compatibilidad,
saltos de etapa, Museo o condiciones comerciales por esta propuesta.
Rewards R1–R8/T1–T8, S1–S7-A y el estado aprobado/pausado de S8-A no cambian.

## 9. Bloqueos de persistencia Rewards F2-A · DOC-6

[DOC-6](decisions.md#doc-6--arquitectura-persistente-rewards-f2-a--18102026),
aprobado internamente por Jaime/Parte A el 18/10/2026 sobre `5a4e079`, desarrolla
R1–R8/T1–T8. Fase 1 está integrada (PR #38), pero **F2-A, RewardEvent y el servicio
transaccional no existen**. El [detalle técnico](contracts/rewards-v0.md#12-f2-a--persistencia-y-xp-histórica-local--doc-6)
resuelve internamente el alcance XP histórica/NO_REWARD, causalidad S3, snapshot
y replay, sin ratificar contratos externos ni autorizar migraciones.

| Puerta de avance | Pendiente / propietario |
| --- | --- |
| Antes de crear RewardEvent y migración | Óscar/Core: confirmar User canónico, representación canónica del PK y mapeo de RewardIdentity.recipient_id. CORE-01/CORE-02 y P4 no se cierran. |
| Antes de persistir físicamente | Óscar/Core: conservación, anonimización/eliminación, on_delete de RewardEvent y relación con XPEvent/perfiles; P5, M-01 y política legacy siguen abiertos. No copiar CASCADE provisional ni decidir por Core. |
| Antes de persistir físicamente | Óscar/Core con Jaime: frontera confiable de autorización para invocar Rewards; origin_code y ValidatedRewardFact no autentican. Sin JWT paralelo ni entradas no autorizadas. |
| Especificación local antes del código | Jaime con el acuerdo de identidad Core: codificación versionada inequívoca de la terna para clave rewards:v1:, esquema físico/constraints candidatos y serialización reward-result-v1; validación causal y rechazo de envolventes transaccionales incompatibles. Sin modificar S3/Fase 1. |
| Antes de activar premios reales | Jaime/Óscar y propietarios funcionales: configuración válida de evolución e instalación real (P8), reglas autorizadas y elegibilidad; P1/XP externa sigue abierto. Fixtures no son baremos oficiales. |
| Fases posteriores | Fernando/Core: Wallet/saldo canónicos, identidad/autorización económica y contratos Bank/Shop; CORE-05 permanece abierto. Henry: objetos/entregas/inventario; juegos: hechos y contratos. No bloquean el diseño local F2-A ni quedan ratificados por él. |

R1/R2 conservan validación del origen, mapeo User y campos semánticos externos;
R3 conserva validación física/conservación; R4 confirma solo una frontera local
condicionada al mismo alias, sin atomicidad remota. R5 permite globalmente efectos
sin XP, pero F2-A rechaza efectos ajenos a XP histórica, sin ignorarlos ni convertirlos
en NO_REWARD; puntos de ascenso S3 no son puntos directos. R6/cupos queda fuera,
R7/correcciones sigue abierto y R8/API/autorización requiere coordinación.
No se cierran P1–P8, R1–R8, I1–I9, CORE-01/CORE-02/CORE-05 ni conservación por
inferencia. Bank/Duckies/juegos, dominio, puntos directos, RewardLimitUsage,
RewardRule como tabla, REST/WebSockets/batch y recuperación distribuida siguen
pendientes. DOC-5/CORE-07/B-06/P6/R-01 no cambian; S8-A permanece pausado.

## 10. XP de dominio S12-A · arquitectura aprobada, implementación bloqueada

Baseline `84f809d`: S11-A integrado (PR #44) selecciona y crea progreso en cero,
sin servicio de concesión positiva. [S12-A](contracts/ecomotor-domain-xp-v1.md)
registra alternativa C y seis decisiones internas de 02B, sin tablas ni migraciones.

| Puerta pendiente | Responsabilidad / condición |
| --- | --- |
| DomainXPEvent físico | Core con Jaime: conservación, anonimización/eliminación y on_delete del evento y sus relaciones. P5 y legacy siguen abiertos; no copiar CASCADE provisional. |
| Contrato técnico implementable | Jaime/02B con los interlocutores correspondientes: firma/tipos, identidad origen–hecho–perfil, huellas, snapshots, resultado, errores y frontera transaccional. No convertir la firma candidata en API vigente. |
| Premios reales | Origen autorizado, asociación confiable del hecho al destinatario y reglas validadas. ValidatedRewardFact aislado no es autorización. Fuentes, cantidades y límites pendientes. |
| Coordinación Rewards/juegos | Contratos y confianza todavía abiertos; S12-A no desbloquea F2-A ni modifica DOC-6. |
| P7 restante | Códigos canónicos, obligatoriedad/acceso adicional, cambio/reinicio, concesión positiva de dominio y sus fuentes/reglas e integración. S13-A era una prioridad sin diseño en este corte; §11 registra la aprobación interna posterior y sus pendientes. |
| Trazabilidad de alternativas | A/B sí constan en 02B, aunque no estaban incorporadas al repositorio ni al contexto documental recibido por Codex. A: servicio local de actualización de XP de dominio, con identidad e idempotencia suficientes y sin depender de F2-A. B: concesión exclusivamente coordinada por Rewards global tras aprobar sus contratos. C: núcleo local seguro e integración posterior Rewards, evitando concesiones inseguras o incompatibles. Solo C fue aprobada internamente; A/B fueron estudiadas, sin añadir motivos de descarte. |

La repetición histórica sin duplicar y los conflictos están aprobados como
principios, no como constraints o payloads concretos. P5/P7 permanecen abiertos;
el bloqueo independiente de Rewards F2-A descrito en §9 sigue íntegro.
Las referencias anteriores a pausas/implementación describen sus cortes históricos.

## 11. S13-A / S13-A1 · arquitectura aprobada, evaluador sin implementar

El [contrato del evaluador](contracts/ecomotor-ranks-evaluator-v1.md) registra las
siete decisiones internas y las precisiones aprobadas por Jaime en 02B.
La secuencia por especialización y la evaluación del siguiente rango están
acordadas; los valores oficiales y la implementación no lo están. Se conserva
progreso de las cinco especializaciones al alternar, sin aprobar cómo cambiarlas.
La opción B separa importes de XP general y dominio, sin cantidades ni conversiones.

| Pendiente | Alcance / interlocutores |
| --- | --- |
| Política funcional oficial | Umbrales, cursos/retos concretos, códigos canónicos, obligatoriedad y acceso adicional; Jaime con Óscar y consumidores afectados. Sin nuevos baremos por ejemplos. |
| Evidencias verificadas | Contratos de identidad, asociación al sujeto/especialización y autorización de proveedores; Core, cursos/juegos y Jaime. Ausencia de evidencia no acredita cumplimiento. |
| Cambio/reinicio de especialización | Condiciones, procedimiento y límites por concretar en 02B; S11-A sigue rechazando cambios. Conservar progreso no autoriza un nuevo servicio. |
| Confirmación e historia de ascensos | Representación física, snapshots, claves idempotentes, conservación, anonimización/eliminación y on_delete por acordar con Core; no modelo ni migración aprobados. D-19 no resuelve la conservación. |
| Recompensas tardías | Atribución de XP/evidencias a especialización, versión de política y momento; sin decidir retroactividad, reasignación o recálculo. Jaime/Core/Rewards y fuentes afectadas. |
| XP de dominio y Rewards | Persisten los bloqueos de S12-A y DOC-6/F2-A. DomainXPEvent conceptual, sin premios reales; Rewards v0 candidato. |

P5/P7 no se cierran. V2-A25/A26 y el ERD mínimo sin rango siguen siendo el estado
físico integrado. S13-A1 no confirma ascensos ni implementa concesiones de dominio.

## 12. S14-A · cambio aprobado internamente, precisiones y bloqueos

[DOC-S14-A](contracts/ecomotor-specialization-switch-v1.md) registra siete decisiones
internas de 02B. S13-A1 ya está integrado (#47); el evaluador no confirma ascensos.
Los estados previos de §11 describen el corte documental anterior a su implementación.

| Pendiente antes de avanzar | Alcance / responsable |
| --- | --- |
| Compatibilidad S11-A con varias filas | Jaime/02B: el ORM admite varios progresos, pero el servicio actual exige exactamente uno. Precisar repetición de la activa y rechazo de otra selección con varias filas coherentes, preservando primera selección y detección de inconsistencias. No cambiar silenciosamente el contrato. |
| Repetición y precondición esperada | Jaime/02B: concretar respuesta si el objetivo ya está activo pero expected_active_code está obsoleto, y validación de Actual/configuración en repeticiones. No inventar excepción al control de concurrencia. |
| Recompensa tardía | Actividad en Developer, cambio a Gamer y recepción posterior. Preferencia funcional: atribuir a la rama original; no excepción operativa aprobada. Revisar S12-A-02, limitado a la activa, y evidencias confiables del estado al realizar la actividad con Rewards/Core. No elegir automáticamente la activa al procesar. |
| Rangos y conservación | S13-A2 pendiente; conservar rangos es decisión funcional, no campo existente. Core/P5 mantiene conservación, anonimización/eliminación y on_delete; no nuevos eventos/tablas. |
| Residual P7 | Códigos/valores oficiales, acceso adicional, reinicios, XP de dominio/fuentes/autorización y contratos externos permanecen abiertos. La aprobación S14-A no implementa estos aspectos. |

S14-A sin evento físico solo ofrece idempotencia por estado; A → B → A no permite
distinguir una solicitud histórica de una nueva si vuelve a coincidir la precondición.
No se añade una política de identidad histórica para resolverlo. S12-A/DomainXPEvent
y DOC-6/F2-A mantienen sus bloqueos; Rewards v0 candidato, sin premios reales.
