# Decisiones pendientes · Consolidación V2 y Rewards v0

## 1. Marco vigente

**Actualización 02C · 20/10/2026:** base develop `8401d46`, S13-A1 (#47) y S14-A
(#50) integrados. Nueva arquitectura jugable aprobada internamente, no implementada;
[§13](#13-pendientes-residuales-de-la-arquitectura-objetivo-02c) distingue decisiones
cerradas de parámetros y coordinación residual. Los cortes anteriores conservan
su valor histórico y no reabren lo aprobado en 02C.

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

La referencia V2-A21 de este antecedente no impide el objetivo posterior 02C:
secuencia histórica actualizada y umbrales alineados a niveles 1–7, sin activación
ni reinterpretación de catálogos/historias V1. P8 conserva parámetros pendientes.

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
| P2 · Stats | Óscar confirmó Ataque, Defensa, Velocidad, Inteligencia, Lógica y Cuak, específicas por época y distribución al alcanzar especialización; consulta de coordinación y confirmación directa de Jaime en 02C. ATR-OBJ-01 resuelve internamente la nomenclatura objetivo: LOG = Lógica y CUACK = Especial / Especialización, atributo numérico distinto de la identidad tecnológica. LOG Logística/SPE se conservan como antecedentes. | Bases por opción, presupuesto autorizado, fórmulas y migración legacy siguen pendientes; 45 puntos no es valor oficial. No convertir SPE histórico a CUACK ni reinterpretar log_stat V1, que conserva Logística. OP-RED-01 y restantes decisiones no afectadas se conservan. Training no mejora atributos/puntos adicionales en V1 objetivo; futuro requiere confirmación/coordinación. | Parte A para concreción interna; Core/P5 y juegos para transición/consumo. Sin cambios de modelos o contratos físicos por esta precisión. |
| P3 · Cursos | Daily del 09/10/2026: ejemplos de objetos y puntos; bonificación diaria de XP propuesta, no confirmada. Daily del 13/10/2026: corrección automática en LMS, insignias y posible relación futura con Bank; euros/cotización mencionados sin especificación | ¿Qué premios, condiciones, efectos/consumos, cantidades y cobertura V1? ¿Cómo conceder puntos sin ascenso de nivel ni XP? LMS/Bank es una expectativa futura: sin premios, cantidades, XP, conversión económica, contratos o alcance V1 definidos; no resuelve P1. | Óscar y A/B/C; reglas, puntos e integración externa. |
| P4 · User/auth | Sin respuesta nueva; conflicto PR07/D-09/D-10 bajo D-17 | User estándar/CustomUser, autenticación/JWT, origen autorizado, permisos e integración común. No crear auth paralela. | Óscar/Core y Equipo 5; exposición externa y migraciones. |
| P5 · Conservación | Pendiente; M-01 fail-closed interno preservado. S12-A solo acepta DomainXPEvent conceptual. | Retención, anonimización/eliminación de User, perfiles, stats, Rewards y movimientos; referencias, borrado y legacy. DomainXPEvent físico y sus relaciones requieren acuerdo previo de conservación, anonimización/eliminación y on_delete; sin copiar CASCADE provisional. | Óscar/Core y A/B/C; FKs/on_delete y migraciones definitivas. |
| P6 · Vestimenta/Museo | Óscar confirmó una imagen de vestimenta completa por época, no seis piezas visuales; durante progresión histórica solo la vigente, tras elegir especialización anteriores desbloqueadas. DOC-5/intermedias más amplia permanece como propuesta histórica no confirmada. Siete épocas hasta Siglo XX y elección nivel 8 ya registradas, no se reabren. | Acotar CORE-07/B-06/R-01 a representación física y contratos: imagen no fija objetos/tablas/FK ni adquisición/autoequipamiento. Acordar con Henry apariencia frente a identidad histórica jugable, condiciones de especialización, posesión/equipamiento, idempotencia, Museo y transición V1 sin reinterpretar eventos. | Henry/Jaime y Óscar para residuales funcionales; Fernando si afecta comercio; sin aprobar esquema Duckies ni reabrir la secuencia de épocas. |
| P7 · Opciones/especializaciones | S11-A (#44), S13-A1 puro (#47) y S14-A (#50) integrados. 02C aprueba elección histórica/tecnológica desde nivel 8, aplazamiento, una activa y conservación independiente de configuraciones/dominio/rangos confirmados. | Códigos canónicos de Developer, Ciber, Sistemas, Data IA, Gamer; XP de dominio autorizada, rangos S13-A2, contratos y transición a selección explícita. No está implementada la nueva elección ni se reinician progresos. Conservar cuestión de recompensas tardías y evidencias S12-A. | Jaime/Equipo 5, Core y juegos; Henry para integración visual. Sin reabrir acceso nivel 8 ni históricos jugables. |
| P8 · Umbrales/configuración | S6-A integrado. 02C fija siete épocas/niveles 1–7 con umbrales coincidentes; nivel 8 abre elección, sin octava época; niveles posteriores continúan y sin puntos nuevos por nivel en objetivo. V1 sigue compatible hasta activación. | Códigos y valores numéricos XP, bases y presupuesto fijo autorizados/versionados, instalación real, compatibilidad de catálogos y política histórica de transición/cambios. No recalcular XP/niveles ni convertir ilustraciones en parámetros oficiales. | Equipo 5/Jaime para candidatos versionados/coordinados; Core/P5 para conservación/migración y activación conjunta. P8 no se cierra por fijar reglas estructurales. |

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
| I2 · Training | Se conservan XP repetible, moneda diaria y acceso local comunicados como antecedentes. CORE-03 y confirmación directa de Jaime recogen User/Free/Plus/Pro y misma XP por misma actividad elegible entre membresías jugables. | Training/E5/Core: conciliar discrepancia explícita 2 XP Free / 5 XP Plus-Pro, sin elegir importe nuevo ni activar reglas. Acceso, límites, día/hechos y contrato de premios siguen separados; extra DC por pago contemplado sin cantidades/fórmulas aprobadas. |
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

**Antecedente fechado:** la consulta y preguntas siguientes reflejan DOC-5 del
18/10. La conciliación posterior de §17 confirma imagen completa y condición de
reutilización tras especialización, no reutilización durante épocas intermedias.
También mantiene la secuencia histórica ya aclarada el 19/10. Los bloqueos solo
permanecen en sus residuales de adquisición/equipamiento/representación/integración;
no se vuelven a presentar esas aclaraciones funcionales como desconocidas.

Consulta del 18/10/2026 de CORE-07, E5-02 y B-06 en el documento compartido de
coordinación, contrastada con DAR3 pp. 3 y 48. [DOC-5](decisions.md#doc-5--criterio-funcional-propuesto-de-vestimentas-históricas--18102026)
registra procedencia y autoridad; la [arquitectura](architecture.md#31-vestimentas-históricas--propuesta-doc-5)
precisa adquisición, posesión, equipamiento y apariencia. El criterio E5 ya está
formulado: conjunto completo por época, adquisición/autoequipamiento al evolucionar,
conservación y libre reequipamiento de anteriores obtenidos también durante épocas
intermedias, sin permitir futuras no alcanzadas. **No es aprobación del profesor
ni contrato técnico ratificado con Henry.**

**CORE-07, B-06, P6 y R-01 permanecen abiertos.** En ese corte se solicitaba validar
la propuesta frente a DAR3, no formularla. Las preguntas históricas fueron:

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

**Antecedente DOC-S13-A1:** el título y preguntas siguientes describen el corte
previo a PR #47. Hoy el evaluador puro está integrado; S13-A2 sigue pendiente.
El cambio tecnológico ya se implementó en #50; nueva elección 02C aún no existe.

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

[DOC-S14-A](contracts/ecomotor-specialization-switch-v1.md) registra S14-A-01…07
y las precisiones S14-A-08/09 aprobadas internamente en 02B sobre develop
`f4c9ce4` (PR #48). S13-A1 ya está integrado (#47); el evaluador no confirma ascensos.
Los estados previos de §11 describen el corte documental anterior a su implementación.

Las preguntas de compatibilidad y precedencia ya están resueltas internamente;
su implementación y compatibilidad S11-A están integradas mediante PR #50.
Las filas de implementación siguientes se conservan como plan histórico ya cumplido,
sin presentar S13-A2, dominio o arquitectura 02C como implementados.

| Pendiente antes de avanzar | Alcance / responsable |
| --- | --- |
| Implementar compatibilidad S11-A · S14-A-08 | Decisión interna cerrada: admitir varios progresos coherentes con integridad validada; repetir activa recupera su progreso sin escrituras/configuración de etapas; otro código sigue en conflicto y primera selección intacta. Pendiente adaptar cuidadosamente servicio/tests, sin reparación ni reset. |
| Implementar precondición S14-A · S14-A-09 | Decisión interna cerrada: comprobar esperado antes de repetición; discrepancia rechazada incluso con objetivo activo. Coincidencia y objetivo activo: recuperación coherente sin escrituras ni reevaluación de etapas/elegibilidad. Cambio efectivo: Actual y D-19. Servicio y tests aún pendientes. |
| Recompensa tardía | Actividad en Developer, cambio a Gamer y recepción posterior. Preferencia funcional: atribuir a la rama original; no excepción operativa aprobada. Revisar S12-A-02, limitado a la activa, y evidencias confiables del estado al realizar la actividad con Rewards/Core. No elegir automáticamente la activa al procesar. |
| Rangos y conservación | S13-A2 pendiente; conservar rangos es decisión funcional, no campo existente. Core/P5 mantiene conservación, anonimización/eliminación y on_delete; no nuevos eventos/tablas. |
| Residual P7 | Códigos/valores oficiales, acceso adicional, reinicios, XP de dominio/fuentes/autorización y contratos externos permanecen abiertos. La aprobación S14-A no implementa estos aspectos. |

S14-A sin evento físico solo ofrece idempotencia por estado; A → B → A no permite
distinguir una solicitud histórica de una nueva si vuelve a coincidir la precondición.
No se añade una política de identidad histórica para resolverlo. S12-A/DomainXPEvent
y DOC-6/F2-A mantienen sus bloqueos; Rewards v0 candidato, sin premios reales.

## 13. Pendientes residuales de la arquitectura objetivo 02C

**Precisión vigente:** [ATR-OBJ-01](decisions.md#atr-obj-01--nomenclatura-de-atributos-objetivo--20102026)
resuelve internamente LOG = Lógica y CUACK = Especial / Especialización tras §17.
LOG Logística/SPE quedan como antecedentes de 02C y V1; no autorizan conversiones
de datos. No se reabren históricos jugables, épocas, nivel 8 o redistribución.

[Acuerdos del 20/10/2026](decisions.md#02c--arquitectura-objetivo-del-ecomotor--20102026)
y [contrato objetivo](contracts/ecomotor-playable-options-target-v1.md) aprobados
internamente por Equipo 5, sin implementación. No son ratificación de Core/juegos
ni una migración autorizada. No se cierran P1–P8 en bloque.

**Cerrado internamente:** siete épocas objetivo (Prehistórico, Griego, Romano,
Medieval, Renacentista, Revolución Industrial, Siglo XX), umbrales correspondientes
a niveles 1–7; elección/aplazamiento desde nivel 8, históricos realmente jugables,
una activa, configuraciones independientes, CUACK Especial / Especialización numérico,
LOG Lógica (ATR-OBJ-01), sin puntos por nivel y OP-RED-01 gratuita/ilimitada. Primera elección
sin guardado parcial; Training no mejora seis atributos/puntos adicionales en V1.
No usar R-01 para redistribución: pertenece a equipamiento histórico.

| Ámbito | Pendiente real / responsable |
| --- | --- |
| Interno · catálogos/parámetros | Equipo 5: códigos técnicos de épocas/tecnológicas, umbrales XP numéricos, seis bases por opción y cantidad del presupuesto fijo. Candidatos versionados/coordinados no son valores oficiales. |
| Interno · contratos/errores | Parte A: firmas Python definitivas, orden entre replay idempotente y revisión obsoleta, caso de redistribución sin cambios y representación de resultados/historia. No trasladar automáticamente precedencia de S14-A a servicios nuevos. |
| Interno · diseño físico | Detalle definitivo de eventos, campos/revisiones y restricciones; modelos solo conceptuales. No confundir unicidad conceptual aprobada con migración. |
| Coordinación · transición | Equipo 5/Core: inventario de datos y clasificación explícita nuevos/legacy, migración y activación conjunta. Ausencia de UserPlayableState no identifica perfil nuevo; evitar doble autoridad con active_specialization_code. |
| Coordinación · Core/P5 | Conservación, anonimización/eliminación, relaciones y on_delete. No borrar/reasignar CharacterStats o historiales ni recalcular XP/niveles sin política aprobada. |
| Coordinación · juegos/dominio/rangos | Consumo de estadísticas efectivas con juegos, concesión autorizada de XP de dominio/evidencias, recompensas tardías y persistencia/confirmación S13-A2. S13-A1 evalúa, no confirma; DomainXPEvent conceptual y sin tabla aprobada. |
| Coordinación · apariencia | Henry/Jaime: integración de selección jugable con apariencia, vestimentas históricas e inventario. DOC-5/CORE-07/B-06/R-01 conservan residuales, no bloquean reconocer internos históricos jugables. |
| Atributos · precisión interna posterior | ATR-OBJ-01 cierra códigos y significados de LOG y CUACK en el objetivo, sin alterar V1. Bases, presupuesto, fórmulas y adaptación legacy siguen pendientes; no se inventan efectos especiales. Mejoras futuras Training siguen fuera de V1 objetivo y requieren confirmación/coordinación. |

P1 y P3–P5, R1–R8/Rewards, Core y economía mantienen sus pendientes ajenos a 02C;
F2-A sigue condicionado por DOC-6. XP de dominio y rangos confirmados se conservan
al cambiar, pero sus servicios positivos/persistencia pendientes no aparecen por
esta aprobación. S1/S2-A/S3/S7-A/S11-A/S13-A1/S14-A están integrados; S3 aún concede
puntos por nivel y S7-A afecta estadísticas globales. Nuevos modelos/servicios
jugables no existen. Implementación posterior en 01B, sin tocar contratos V1.

## 14. A2 · Dependencias para XP histórica objetivo

[Arquitectura A2](contracts/ecomotor-target-xp-v1.md) y
[decisiones](decisions.md#a2--arquitectura-de-xp-histórica-objetivo--20102026)
aprobadas internamente en 02C sobre develop `6a7d1d7`. A1.1/A1.2 están integrados;
servicio A2 y su primer planificador todavía no existen. S3 continúa vigente con
puntos por nivel; no se modifica ni se selecciona versión automáticamente.

**Resuelto internamente:** servicio separado, identidad (profile, operation_key)
sin versión añadida, replay sin catálogos actuales, A1.1/A1.2 para todos los cruces,
sin puntos por nivel y validación según clasificación sin reparación legacy.
A2-CT-01 conserva ese alcance; A3-CT-01 sigue siendo compatibilidad/migración.

| Pendiente / puerta de avance | Responsable y condición |
| --- | --- |
| A3 · clasificación y escritor | Parte A/Equipo 5: definir clasificación persistente de perfiles nuevos/heredados, decisión confiable de versión y activación coordinada. Ni catalog_version ni A1.1 autorizan producción; no inferir versión por estado ausente. Sin dos escritores contradictorios por perfil. |
| A3 · compatibilidad y migración | Inventario de datos reales, política de transición de catálogos y correspondencia de etapas/causas; no renombrar historia, reasignar stats/eventos, recalcular XP/niveles o reparar automáticamente legacy. |
| A3 · resultados/replay entre versiones | Concretar representación y procedencia cuando no están persistidas. XPEvent no guarda versión/nivel/época y EvolutionEvent no guarda atributos originales de etapa. No prometer replay completo; no convertir puntos históricos V1 a cero. Valores 0/None de compatibilidad solo para concesiones objetivo nuevas. |
| A3 · validación de estadísticas | Especificar invariantes por clasificación antes de la futura escritura; no copiar automáticamente exigencias de CharacterStats V1 ni omitir validación por ausencia de fila. |
| Core/P5 | Conservación, anonimización/eliminación, relaciones/on_delete e integración de identidad/autorización siguen pendientes. Este diseño no los resuelve ni autoriza migraciones. |
| Configuración y producción | Valores XP autorizados, instalación real y permiso de uso; snapshot validado no equivale a configuración oficial. P8 continúa abierto. |
| Incremento puro A2 | Parte A puede diseñar y probar un planificador sobre A1.1/A1.2 con entradas explícitas/sintéticas, sin escritura ni activación. Firma/detalle técnico y pruebas se concretarán en su incremento. No se crea target_xp_plan.py en esta tarea. |

La aprobación A2 no desbloquea concesión positiva de dominio, S13-A2, Rewards F2-A,
inventario, selección jugable o contratos externos. P1–P8, R1–R8 y Core conservan
sus cuestiones residuales; A3 es dependencia de persistencia/activación, no excusa
para activar producción desde un planificador puro. Las pruebas transaccionales,
rollback/concurrencia e historia entre versiones son futuras, no ejecutadas aquí.

## 15. A3 · Condiciones de compatibilidad y activación

[Decisiones A3](decisions.md#a3--compatibilidad-histórica-y-activación-coordinada--20102026)
y [contrato](contracts/ecomotor-transition-target-v1.md), aprobación interna
condicionada sobre `7039ae6`. §14 conserva el corte A2 anterior: A2.1 ya está
integrado por #56 como planificador puro, sin servicio de concesión objetivo.

**Dirección resuelta internamente:** registro unívoco por perfil que separa
procedencia/transición; catálogo objetivo separado/versionado/inmutable tras uso;
auditoría sin migración automática; escritor único y preferencia de corte global;
replay histórico primero y resultados sin puntos solo para nuevas concesiones
objetivo. La implementación y sus puertas siguen abiertas:

| Bloqueo / siguiente validación | Responsable y límite |
| --- | --- |
| Clasificación física | Parte A con Core/P5: campos/tipos/constraints del registro de política, identidad/procedencia y transición persistentes; auditoría previa de existentes. No inferir clasificación ni autorización por nivel/época/stats/estado ausente. |
| Catálogo objetivo físico | Parte A: diseño separado, versionado e inmutable tras uso; catálogos/valores autorizados. No renombrar EvolutionStage V1 ni tratar snapshot A1.1 como permiso de producción. |
| Causalidad y PlayableOption | Parte A/Core con Henry: identificar nuevas épocas en EvolutionEvent y adaptar relación histórica de PlayableOption sin perder integridad/historia. Bloqueo físico explícito; sin FK, tabla o migración seleccionada. |
| Procedencia de concesiones nuevas | Parte A/Core: representación persistente inmutable sin cambiar identidad (profile, operation_key). No atribuir versión retrospectiva a XPEvent V1 ni reconstruir snapshots ausentes. |
| Datos y transformación | Equipo 5: inventario de perfiles/XP/niveles/épocas/eventos/stats/especializaciones/Duckies, diagnósticos compatibles/decisión/incoherentes y política autorizada. Diagnóstico no permite migrar ni recalcular/reasignar por inferencia. |
| Core/P5 | Conservación, anonimización/eliminación y on_delete de registros/relaciones; retención y legacy siguen pendientes, sin copiar políticas provisionales o aprobar modelos. |
| Duckies y consumidores | Henry/Parte A y consumidores: EvolutionItem.stage, current_stage_code, ordinales y selección visual; acordar adaptación de referencias/contratos. No cambiar Duckies ni equiparar época, identidad y apariencia. |
| Entrada y activación | Equipo 5: detalle técnico del punto único, suspensión/drenaje, migración autorizada, activación/supervisión/detención y consumidores compatibles. Nunca selección por cliente; sin retorno automático S3 tras XP objetivo. |
| Resultados y pruebas | Interfaz final compartida, compatibilidad V1 y saldo heredado conservados; pruebas de migración, concurrencia, rollback y activación aún necesarias, sin replays completos de información no guardada. |
| A3.1 posterior | Propuesta de auditoría pura; nombres/firmas antes de implementar en 01B. Sin ORM/escrituras/XP o autorización de migración; no se crean archivos Python en esta PR. |

P1–P8 y R1–R8 conservan sus residuales. No se desbloquean Rewards F2-A, dominio
persistente, S13-A2 o economía/inventario por registrar A3. S3 V1 sigue vigente;
las nuevas concesiones objetivo prevén 0/None en campos de puntos compatibles,
sin borrar puntos disponibles ni reinterpretar resultados antiguos.

## 16. A3.2 · Alcance y validaciones pendientes

**Estado vigente para A3.3, base 75177a2:** A3.2 está integrado por PR #60, con
extractor y tests existentes. Las previsiones siguientes corresponden al corte
documental 8024fa7, no a ausencia actual de implementación. Continúan abiertos
los límites de cobertura, autorización, conservación y futura transición.

[Decisiones A3.2](decisions.md#a32--inventario-legacy-de-solo-lectura--20102026)
y [contrato](contracts/ecomotor-legacy-inventory-v1.md), aprobación técnica interna.
Base `8024fa7`: A3.1 integrado por #58, extract_legacy_audit_snapshot todavía
conceptual; S3 V1 sigue activo y no hay migración/activación objetivo. El apartado
A3.1 futuro de §15 conserva la previsión anterior a esa integración.

Cerrado internamente: un perfil por extracción, alias confiable, clases A3.1 sin
modelos/diagnósticos, cobertura íntegra o fallo, causalidad bidireccional y privacidad;
transacción corta IMMEDIATE con materialización y costes de bloqueo explícitos.
Propuesto rechazo de transacción exterior, sin auditoría/migración automática.

| Pendiente / límite | Propietario y alcance |
| --- | --- |
| Implementación A3.2 | Parte A/01B: revisar firma/nombres y detalle técnico de legacy_inventory_reader.py y tests; no crearlos en esta tarea. Errores conceptuales diferenciados, sin excepciones/códigos HTTP definitivos. |
| Autorización y privacidad | Core/operadores/consumidores: autorización de inspección y alias confiable; comprobación causal mínima no amplía permisos ajenos. Claves exactas solo en snapshot, no logs/trazas/exportaciones; sin datos personales Core o endpoint público. |
| Consistencia/cobertura | Verificar todas las lecturas/materialización bajo misma transacción/alias, rechazo propuesto de exterior, timeout/fallo/truncado sin falsa cobertura y causalidad en ambos sentidos. Pruebas futuras TransactionTestCase SQLite con conexiones independientes y cero escrituras. |
| Auditoría integral | StatAllocationEvent, especializaciones/UserSpecializationProgress/dominio/rangos, relaciones completas Duckies y umbrales/puntos históricos quedan fuera. Cobertura completa del extractor no certifica esos dominios o migración. |
| Esquema/transición | Modelo físico de clasificación, catálogo objetivo, relaciones causales, datos reales, migración/activación y contratos Duckies siguen condicionados por A3; una fotografía o COMPATIBLE limitado no los autoriza. |
| Core/P5 | Conservación, anonimización/eliminación y on_delete, además de autorización de operadores/consumidores, permanecen pendientes sin inferencias. |
| Regresión y pruebas | Futura implementación debe cubrir perfiles/alias, vacíos/stats ausentes, cobertura, causas extranjeras y ausentes, consultas fallidas, privacidad, concurrencia, cero escrituras y S3 V1 intacto. No añadidas ni ejecutadas en esta PR documental. |

No se resuelven los residuales P1–P8/R1–R8 ni se desbloquean S13-A2, dominio
persistente, Rewards F2-A o economía/inventario. A3.2 obtiene evidencia; A3.1 evalúa;
clasificación, migración y concesión requieren decisiones y permisos propios.

## 17. Aclaraciones confirmadas de Óscar · pendientes residuales

[Procedencia](decisions.md#conciliación-de-aclaraciones-de-óscar--20102026): documento
compartido de coordinación consultado el 20/10/2026, CORE-03/CORE-07/PROF-04 y
Training, con confirmación directa de Jaime en 02C. Henry tomó notas y Óscar
escribió los atributos en la pizarra según esa confirmación. Marcadores antiguos
en la fuente no niegan esta confirmación ni acreditan cierre técnico de contratos.
DAR3 conserva su antecedente; no se inventa fecha exacta de respuesta o aprobación.

| Aclarado funcionalmente | Pendiente real / interlocutores |
| --- | --- |
| User, Free, Plus, Pro; User acceso visual previo, distinto del modelo Django. XP igual por misma actividad elegible en membresías jugables. | Core/juegos/E5: contrato de categorías/permisos y cambios de membresía; conciliar con Training sus 2/5 XP. No elegir nuevos importes. DC extra por pago contemplado, cantidades/fórmulas y baremos pendientes de Óscar/Fernando/propietarios. |
| Imagen completa por época y uso de la vigente hasta especialización; anteriores desbloqueadas reutilizables después. | Henry/Jaime: adquisición/autoequipamiento, representación en objetos/tablas/relaciones, identidades y contratos. Relación de la condición visual con elección jugable 02C, sin asumir equivalencia. CORE-07/B-06/P6/R-01 tienen aclaración parcial, no cierre global. |
| Seis atributos del profesor: Ataque, Defensa, Velocidad, Inteligencia, Lógica y Cuak; específicos por época y reparto al alcanzar especialización. | ATR-OBJ-01 resuelve posteriormente la nomenclatura objetivo LOG = Lógica y CUACK = Especial / Especialización. Parte A y consumidores deben concretar bases, presupuesto y fórmulas; transición con Core/P5. LOG Logística/SPE se conservan como antecedentes y V1, sin conversión histórica ni séptimo atributo. Ejemplo 45 no oficial. |
| Siete épocas históricas hasta Siglo XX y elección desde nivel 8 ya confirmadas. | Solo normalización técnica/transición con A3 y propietarios; no alterar identidades V1 ni reabrir secuencia. |

DOC-5 y DAR3 se conservan como antecedentes; reutilización visual intermedia no es
comportamiento confirmado. Otros acuerdos internos 02C se mantienen salvo lo que
se marca expresamente pendiente de adaptar; no se cambian servicios/contratos
físicos por la aclaración. Training V1 objetivo sigue sin mejoras de seis atributos
o puntos adicionales; cualquier futuro requiere confirmación funcional/coordinación.
P1, Core/identidad/autorización/conservación, economía, Rewards y restantes contratos
mantienen sus residuales. No se activan reglas, A2 o escritores ni se modifica S3,
A3.1/A3.2, Rewards/Bank/Duckies, datos o modelos.

## 18. A3.3 · Pendientes de clasificación persistente

[Aprobación interna](decisions.md#a33--clasificación-persistente-de-perfiles--20102026)
y [contrato candidato](contracts/ecomotor-profile-classification-v1.md), desarrollo
de A3-CLAS-01. A3.1 (#58) y A3.2 (#60) integrados; clasificación persistente no
implementada. S3 V1 conserva su contrato, incluso sin registro de clasificación.

**Resuelto internamente:** procedencia y transición separadas; ausencia de registro
no clasifica; procedencia confirmada inmutable; revisión monotónica no negativa;
historial inmutable y clave (profile, operation_key) propia de clasificación;
repetición compatible y conflicto incompatible; política/evento atómicos D-19.
Clasificación no autoriza XP ni activa el escritor objetivo.

**Precisión posterior a PR #63:** [matriz, recuperación y revisiones aprobadas](decisions.md#a33--matriz-recuperación-y-revisiones--20102026)
resuelven el grafo permitido, altas por procedencia, recuperación al estado previo,
revision inicial 1 y aumento de 1 por transición nueva; replay no muta ni crea eventos.
[Contrato §3.1–§3.4](contracts/ecomotor-profile-classification-v1.md#31-matriz-aprobada--a33-matrix-01).
No se permiten otras transiciones nuevas ni BLOCKED → BLOCKED; replay de bloqueo
confirmado conserva idempotencia. TARGET_CONFIRMED no activa XP y BLOCKED no
sustituye controles globales. En ese corte aún no estaban implementadas; PR #66
integra ahora las reglas puras, sin permisos externos ni persistencia.

**Protocolo conceptual resuelto tras PR #64:** [A3.3-CONTENT-01, REV-PROTOCOL-01 y REPLAY-PROTOCOL-01](decisions.md#a33--contenido-revisión-y-replay--20102026).
Contenido original comparable estricto, None distinto de 0, evento histórico primero
y revisión actual solo para operación nueva. Replay autorizado conserva resultado
histórico sin mutación, sin exigir elegibilidad actual ni volver a bloquear tras
recuperación. Falta de evidencia de igualdad no permite inferir compatibilidad.
La resolución no aprueba el formato persistente ni la vigencia de evidencia legacy.

| Pendiente | Responsable / límite |
| --- | --- |
| Reglas puras 01B · integrado #66 | profile_classification_rules.py y sus tests ya integrados en 8b6b0f7: matriz, contenido, revisiones y replay sobre datos aportados. No hay persistencia, autorización, evidencia actual de BD o clasificación real. Las previsiones anteriores son antecedentes; este PR no vuelve a ejecutar sus tests. |
| Modelo físico | Parte A/Core/P5: campos/tipos/relaciones/constraints definitivos de ProfileProgressionPolicy y ProfileProgressionPolicyEvent; sin tabla o migración aprobadas. Representación persistente definitiva de solicitudes/eventos/relaciones, ausencia previa y vínculo inequívoco al bloqueo; mecanismo físico de conservación/comparación pendientes. Primera clasificación sin estado previo y revision=1 ya acordadas conceptualmente. |
| Evidencia y protocolo | Parte A: actualidad/suficiencia de evidencia mientras S3 escribe, frontera técnica segura para validar esa evidencia. Contenido/revisión/replay ya resueltos conceptualmente; falta representación física, no una nueva elección de orden. A3.2 rechaza transacción exterior; no presuponer extracción anidada ni que COMPATIBLE autoriza clasificar. |
| Core/P5 | Conservación histórica, eliminación/anonimización, on_delete, identidad canónica del operador, tratamiento canónico de su participación en comparación y autorización confiable del proceso. No resueltos unilateralmente. |
| Henry/Duckies y consumidores | Transición de catálogo y referencias, causalidad de nuevas evoluciones y consumidores compatibles; no se cambia esquema Duckies. |
| Pruebas futuras | Validadores puros 01B según fila anterior. Concurrencia, rollback e idempotencia persistente del futuro servicio Django tras dependencias Core/P5; evidencia obsoleta/insuficiente, clasificación sin permiso XP, regresión S3 y aislamiento de perfiles/alias/autorizaciones siguen por verificar. Sin tests nuevos o ejecutados aquí. |
| Fases posteriores | Tras reglas puras y acuerdos Core/P5: modelos/migraciones sin backfill automático, servicios/tests, catálogo/causalidad/Duckies, migración autorizada/ensayos/activación global. No permiso por diagnóstico o clasificación. |

P1–P8, R1–R8 e I1–I9 conservan sus residuales; no se cierran por registrar A3.3.
Inventario integral, datos reales, conservación y activación siguen pendientes.
No se desbloquean Rewards F2-A, XP de dominio persistente, S13-A2 o economía.
Se mantiene ATR-OBJ-01: ATK, DEF, VEL, INT, LOG y CUACK, sin reinterpretar V1.

## 19. A3.4 · Puertas de persistencia y servicio

[Decisión interna](decisions.md#a34--dirección-de-persistencia-de-clasificación--20102026),
[contrato candidato](contracts/ecomotor-classification-persistence-v1.md) y
[consulta Core/P5 no ratificada](contracts/ecomotor-classification-core-boundary-v1.md).
Reglas puras #66 integradas; políticas/eventos persistentes y servicio no implementados.

**Dirección aprobada:** modelos candidatos E5/apps.ecomotor, política por perfil
con revisión positiva y evento inmutable reconstruible; identidad por operación,
transacción D-19 conjunta y lector interno específico para evidencia vigente.
No implica aprobación de modelos/migraciones, backfill o autorizaciones externas.

| Pendiente | Bloqueo y responsable |
| --- | --- |
| Esquema definitivo | Parte A con acuerdos Core/P5: tipos, longitudes, nulidad, colaciones, FKs/constraints SQL, representación exacta de request/before/after y ausencia previa. Analizar límites de claves/revisiones frente a API pura sin máximos especulativos. Bloquea modelos/migraciones finales. |
| Restricción de revisión | UNIQUE(profile, after_revision) propuesta, no definitiva: evaluar ventajas/limitaciones e historia. No reemplaza identidad aprobada (profile, operation_key), cadena válida o atomicidad. |
| CORE-A3.3-IDENTITY | Operador canónico y representación; participación en comparación original. Bloquea cierre de campos/relaciones/evidencia y atribución del servicio; no elegir FK o política por inferencia. |
| CORE-A3.3-LIFECYCLE/RETENTION/PRIVACY | Conservación, eliminación/anonimización y on_delete de User/perfil/política/eventos/claves/incidencias. Bloquean esquema/migraciones y operación con garantías históricas. CASCADE/PROTECT/identidad histórica separada son alternativas sin elección. |
| CORE-A3.3-AUTH | Permisos para inicial/transición/bloqueo/recuperación/replay y procesos internos: bloquean servicio. Si exigen datos nuevos, revisar también esquema; no son aprobación de acceso por conocer una clave. |
| Evidencia y cobertura por transición | Parte A/propietarios: concretar lector interno transaccional y verificaciones de V1_VERIFIED/TARGET_PREPARED/TARGET_CONFIRMED, incluidas dependencias fuera del auditor/extractor. Bloquea servicio; no basta fotografía previa ni COMPATIBLE. No anidar A3.2. |
| Henry/consumidores | Catálogo, causalidad, referencias e integración/ensayos siguen pendientes; dirección local no ratifica cambios Duckies. |
| Pruebas futuras | OneToOne, unicidades (revisión solo si aprobada), constraints/representabilidad, reconstrucción exacta, ausencia previa, replay sin mutación, conflicto/bloqueo/recuperación, concurrencia, rollback/timeout, evidencia, perfiles/aliases, autorización/retención/eliminación y regresión S3 sin backfill/XP objetivo. |

Secuencia orientativa: A3.4 documental → Core/P5 → evidencia/cobertura →
modelos/migraciones tras acuerdos sin backfill → servicio/tests → integración y
ensayos → migración/activación global autorizadas. No calendario ni permiso actual.
S3 V1 sigue como único escritor; no desbloquear Rewards F2-A, dominio persistente,
S13-A2, inventario o economía. P1–P8, R1–R8 e I1–I9 conservan sus residuales.

## 20. A3.6 · Cobertura y protocolo de evidencia pendientes

[Decisiones](decisions.md#a36--evidencia-vigente-y-condiciones-de-clasificación--20102026)
y [contrato canónico](contracts/ecomotor-classification-evidence-v1.md), aprobación
interna Equipo 5 sobre `bccc617`, sin servicio/modelos o permisos externos.

**Resuelto como dirección:** datos necesarios comprobados en la misma transacción
que confirma una operación nueva; lector interno específico, sin A3.2 anidado;
condiciones por operación y rechazo sin evidencia/autorización/condiciones externas
suficientes o coherencia. Bloqueo no exige avance; recuperación valida de nuevo.
Replay mantiene A3.3 sin repetir verificaciones de elegibilidad nueva.

| Pendiente | Responsable / alcance no cerrado |
| --- | --- |
| Cobertura verificable | Parte A y propietarios: detallar datos/fuentes/criterios para V1_VERIFIED, TARGET_PREPARED y TARGET_CONFIRMED, incluidas dependencias ajenas al alcance A3.1/A3.2. La tabla aprobada no es lista exhaustiva de consultas ni COMPATIBLE autoriza clasificar. |
| Lector y frontera | Parte A: API/consultas definitivas y comprobaciones dentro de transacción, actualidad más suficiencia, coordinación de condiciones externas sin I/O dentro. A3.2 conserva protección frente a transacción exterior. |
| A3.5 · Core/P5 | CORE-A3.3-IDENTITY/AUTH/LIFECYCLE/RETENTION/PRIVACY siguen abiertos, incluida participación del operador en comparación y on_delete. Las cinco preguntas no están respondidas/ratificadas; documento de consulta intacto. |
| Esquema e integración | Puertas A3.4, formatos físicos, relaciones, catálogo y consumidores/Henry siguen pendientes. A3.6 no aprueba modelos/migraciones ni cobertura global del historial. |
| Tests futuros del servicio | Evidencia obsoleta tras S3/actual en transacción/incompleta o incoherente; bloqueo sin avance; recuperación validada con historia íntegra; replay sin verificaciones nuevas; concurrencia/rollback/eventos parciales, aislamiento de perfiles/alias, regresión S3 sin migración automática o XP objetivo. No creados ni ejecutados aquí. |

P1–P8, R1–R8 e I1–I9 mantienen sus residuales. No se activa escritor objetivo,
ni se concede XP ni se crean clasificaciones/backfills por documentar A3.6. S3 V1
sigue activo y TARGET_CONFIRMED no lo sustituye automáticamente.
