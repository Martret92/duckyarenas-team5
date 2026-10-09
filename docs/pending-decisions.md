# Decisiones pendientes · Consolidación V2 y Rewards v0

## 1. Marco vigente

D-20/D-21 registran el reparto y apps objetivo acordados internamente el 08/10.
No queda abierta la pregunta antigua sobre Jaime/Félix/Henry: D-13 se conserva
como antecedente. D-14…D-16 siguen sin aprobación técnica conjunta automática.
D-17, D-18 y D-19 continúan vigentes; no se reabre la política SQLite.

[Arquitectura](architecture.md) concentra requisitos documentales y conclusiones
de las dailys del 06, 07, 08 y 09/10/2026, con su categoría y estado.
[Rewards v0](contracts/rewards-v0.md) es base técnica provisional, no contrato
global aprobado. El [ERD de Parte A](erd/ecomotor.md) conserva ocho entidades y
V2-A1…V2-A29 internas condicionadas; no hay aprobación global ni ORM definitivo.

## 2. Aclaraciones prioritarias con Óscar / Core

Óscar es también interlocutor de Core. Una respuesta parcial no cierra el diseño
físico ni autoriza el servicio afectado; los parámetros configurables no bloquean
por sí solos toda la revisión conceptual.

| ID | Evidencia / estado | Pregunta de cierre | Validadores e impacto |
| --- | --- | --- | --- |
| P1 · XP externa | Daily del 09/10/2026: rectificación funcional, en tensión con Ecomotor pp. 1–2 y 6 | ¿XP solo juegos afecta a histórica o también dominio? ¿Qué actividades externas conservan monedas, objetos o puntos? ¿Desde cuándo, qué ocurre con usuarios/recompensas existentes y cómo configurar nuevas actividades? Confirmación escrita sin borrados, recálculos ni conversión automática de todas las actividades externas a premios sin XP. | Óscar, Jaime/Core; bloquea elegibilidad definitiva y migración afectada, no el contrato conceptual. |
| P2 · Stats | Daily del 09/10/2026: se habló de stats por rol antes de Actual y distribución/edición de puntos en Actual; aclaración parcial | Iniciales, tabla/presupuesto, límites, redistribución y efectos al especializarse. No adoptar todos a 5, tabla de Clash o suma de 45 como defaults oficiales. | Óscar, Jaime, Henry y juegos; inicialización, límites y servicios de asignación. |
| P3 · Cursos | Daily del 09/10/2026: ejemplos de objetos y puntos; bonificación diaria de XP propuesta, no confirmada | ¿Qué premios, condiciones, efectos/consumos, cantidades y cobertura V1? ¿Cómo conceder puntos sin ascenso de nivel ni XP? | Óscar y A/B/C; reglas, puntos e integración externa. |
| P4 · User/auth | Sin respuesta nueva; conflicto PR07/D-09/D-10 bajo D-17 | User estándar/CustomUser, autenticación/JWT, origen autorizado, permisos e integración común. No crear auth paralela. | Óscar/Core y Equipo 5; exposición externa y migraciones. |
| P5 · Conservación | Pendiente; M-01 fail-closed interno preservado | Retención, anonimización/eliminación de User, perfiles, stats, Rewards y movimientos; referencias, borrado y tratamiento legacy. | Óscar/Core y A/B/C; FKs/on_delete y migraciones definitivas. |
| P6 · Vestimenta/Museo | Antecedente DAR3; mecanismo y cobertura pendientes | ¿Las seis piezas principales de cada época deben obtenerse exclusivamente mediante progreso y misiones, o pueden existir también variantes históricas comprables? ¿Cómo se diferencian de los complementos estéticos y qué ocurre al evolucionar? Aclarar conservación, compatibilidad e historiales/Museo sin imponer autoequipamiento o conservación de todos los conjuntos al saltar etapas. | Óscar, Henry y Fernando, con Jaime para evolución; ERD consolidado y vertical. |
| P7 · Especializaciones | Actual aclarado; selección/rangos parciales | Obligatoriedad, acceso, cambios/reinicio/nueva elección no aprobados, XP de dominio y rangos Junior/Middle/Senior/Maestro. Normalizar Sistemas/AdminSys, Data/Data & IA y códigos sin adoptar ejemplos. | Óscar, Jaime y juegos; catálogos y servicios. |
| P8 · Umbrales/configuración | Invariantes internas V2-A20/A21 documentadas; política restante abierta | Valores oficiales y cambios prospectivos/retroactivos sin rebajar progreso ni reconceder puntos silenciosamente. | Óscar/Jaime y Core si afecta a migración; administración y reconciliación. |

### Dependencia prioritaria: código y servicios comunes de Óscar

Dailys del 06, 07 y 09/10/2026: se habló de funciones existentes para recompensas,
puntos y monedas, de compartir código y de evitar duplicar funcionalidades.
Antes de crear servicios equivalentes, Jaime y Fernando deben revisar con
Óscar/Core, Henry y consumidores:

- Qué implementación reutilizar/adaptar y en qué repositorio y versión está.
- Qué parte corresponde implementar al Equipo 5.
- Qué componente será propietario canónico de la Wallet y del saldo.
- Qué servicio será el punto común de concesión de recompensas.
- Cómo encaja con la implementación candidata de Fernando y qué contratos
  validar con Óscar antes de implementar.

No se han recibido y verificado aquí firmas, modelos ni estructura de ese código.
La validación completa Rewards v0; no aprueba una segunda Wallet, otro saldo
canónico o un sistema duplicado de recompensas. Los límites de apps D-21 y
contratos requieren revisión de Óscar/Core y validación técnica A/B/C/juegos.

## 3. Validación conjunta de Rewards v0

Los principios están aceptados provisionalmente como propuesta, no como decisión
D nueva ni ORM. Las preguntas siguientes concretan el contrato; no reabren
por sí solas la autoridad funcional de Ecomotor, Bank o Duckies.

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

## 4. Juegos, compras y alcance V1

| ID | Evidencia / asunto pendiente | Validadores y siguiente paso |
| --- | --- | --- |
| I1 · Escape | Daily del 09/10/2026: XP válida de stages completados conservada y premio final independiente; PDF local contempla penalización provisional. Stage y habitación son distintos; sin moneda por stage no se eliminan automáticamente premios por habitación. Versión consolidada más reciente no identificada. | Óscar y Escape/Jaime: obtener versión, acordar cuándo consolidar parciales/finales, identidad y penalizaciones sin descontar XP histórica. |
| I2 · Training | PDF y reunión reiteran XP repetible y moneda diaria. Acceso gratuito/membresía sigue parcialmente ambiguo. | Training/Óscar: aclarar acceso separado del contrato de premios; no adoptar moneda única para toda la vida propuesta por participantes. |
| I3 · Clash/apuestas | Daily del 09/10/2026: reserva de ambas apuestas al aceptar. DAR3 p. 42 no exige apuestas en primera entrega. | Fernando, Clash y Óscar: confirmar V1 y reserva, liberación, liquidación, cancelación, timeout, claves y saldo disponible/reservado. |
| I4 · Compra | Ecomotor pp. 4–5 participa en comprobaciones; Shop proceso comercial, Bank fondos y Duckies entrega. | A/B/C: fijar coordinador, validaciones, claves y frontera transaccional/recuperación de compra, sin duplicar saldo ni aprobarlo por Rewards v0. |
| I5 · Objetos y equipo | Catálogo mínimo, efectos/consumos, precios, caducidad, roles y vestimenta sin cerrar; compra por rol es preferencia de Óscar. | Henry/Fernando con Jaime/juegos/Óscar: definir catálogo y compatibilidad. No confundir tipos de combate con productos Shop. |
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
- Consolidar ERD/diccionarios A/B/C con referencias y borrado acordados antes
  del ORM afectado. Mantener las ocho entidades provisionales de A y condiciones
  M-01, V2-A20/A21 y conservación.
- Implementar después servicios, ORM, migraciones y datos maestros del alcance
  acordado, sin parámetros oficiales ficticios.
- Verificar duplicados/conflictos, premios sin XP, límites diarios concurrentes,
  rollback, permisos y compatibilidad de contratos. D-19 exige TransactionTestCase
  y una ejecución SQLite file-backed; tests pendientes, no ejecutados en este PR.
- Completar Admin/interfaz/CRUD, historiales/Museo y evidencias PR07 según alcance.
  [Plan de trabajo](team5-work-plan.md) concentra hitos y responsables.

El cierre de una pregunta requiere evidencia y actualización del registro cuando
corresponda. Publicar una propuesta no equivale a validación conjunta.
