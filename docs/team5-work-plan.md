# Plan de trabajo · Consolidación V2 y Rewards v0

## 1. Estado y referencias

El reparto y apps objetivo del 08/10 son acuerdos internos D-20/D-21.
Hitos, prioridad y autonomía de este plan son propuestas operativas;
no aprueban ORM, contratos compartidos ni el alcance final V1.

[Arquitectura](architecture.md) concentra fuentes funcionales y notas de las dailys;
[decisiones](decisions.md), acuerdos; [pendientes](pending-decisions.md), preguntas;
[Rewards v0](contracts/rewards-v0.md), contrato candidato;
[ERD Parte A](erd/ecomotor.md), ocho entidades físicas provisionales.
A-01…A-16 son antecedentes; V2-A1…V2-A29 siguen internas y condicionadas.

DAR3 §§9–10 requiere una vertical integrada, recompensa única, compra consistente
e historiales, coordinada con Core y juegos. PR07 aporta ERD/diccionario antes del
ORM, cardinalidades/on_delete, modelos/migraciones, Admin, vistas/templates,
formularios/CRUD, permisos/tests y evidencias Git individuales.
D-17 mantiene el conflicto User/auth pendiente. Daily del 06/10/2026: se aclaró
que el calendario de quince días de PR07 es una guía de trabajo; sus entregables
se conservan. Daily del 09/10/2026: el 19/10 se comentó en relación con exámenes
y evaluación, sin fijarlo como entrega completa de DuckyArenas. Los hitos
formativos se distinguen del calendario de entrega del producto.

## 2. Reparto acordado y apps objetivo

| Responsable | Parte y apps | Trabajo inmediato propuesto |
| --- | --- | --- |
| Jaime | A · `apps.ecomotor`: Ecomotor, Rewards, XP, evolución, especializaciones y stats | Consolidar contrato candidato, reglas pendientes y consultas; revisar condiciones del ERD sin alterar las ocho entidades en este PR. |
| Henry | B · `apps.duckies`: Duckies, avatar, objetos, inventario y equipamiento | Revisar catálogo/posesión, concesiones/consumos, compatibilidad y contrato de objetos con Rewards/Shop. |
| Fernando | C · `apps.bank` y `apps.shop`: wallet, movimientos, catálogo comercial y compras | Revisar diseño B/C, créditos/débitos idempotentes, coordinación de compra y reservas solo si se incluyen apuestas. |
| Equipo 5 con Óscar/Core | `apps.users` conservada; integración de identidad/JWT | Resolver autenticación, permisos, conservación y legacy antes de la parte afectada. |

D-20 sustituye para la planificación el antiguo reparto propuesto D-13,
conservado como antecedente. D-21 no crea apps en este PR ni mueve perfiles.
D-18 mantiene rutas/labels actuales; D-17/D-19 no cambian.
La rama de Fernando requiere revisión antes de integrar y no se modifica aquí.

## 3. Orden de trabajo y condiciones

**Dependencia prioritaria:** revisar con Óscar el código existente de recompensas,
puntos y monedas comentado en las dailys del 06, 07 y 09/10/2026 antes de crear
servicios equivalentes. Identificar repositorio/versión, reutilización o adaptación,
alcance propio del Equipo 5, propietario canónico de Wallet y punto común de
concesión; coordinarlo con la candidata de Fernando y acordar contratos.
No se conocen todavía sus firmas, modelos ni estructura verificados. Esta revisión
completa la validación de Rewards v0, sin duplicar wallet, saldo o recompensas.

1. **Reglas que cambian comportamiento:** confirmar alcance/vigencia de XP externa,
   stats editables en Actual, iniciales/límites y posibles puntos/objetos de cursos;
   preservar progreso existente. Consultar Escape consolidado.
2. **Contrato compartido:** revisar Rewards v0 con Henry/Fernando, Óscar/Core y
   juegos: identidad, huella, reglas/resultados, claves locales y transacción
   compartida con misma BD/conexión.
3. **Diseño físico afectado:** revisar conservación/FKs/on_delete y consolidar
   A/B/C antes de ORM. RewardRule/RewardEvent no son tablas aprobadas.
4. **Servicios y vertical:** implementar solo después del diseño y alcance
   revisados. Priorizar actividad validada → premio → progreso/monedas/objetos
   → compra → equipamiento → historial conforme a DAR3.
5. **Evaluación/integración:** Admin, CRUD evaluable, permisos, tests y evidencias
   PR07; validar REST, realtime y RPG con Óscar/Core/juegos sin aplazarlos
   globalmente por propuestas de participantes.

Los parámetros configurables no bloquean todo el diseño conceptual.
Cambios de reglas, como elegibilidad de XP o condiciones de stats, sí requieren
acuerdo antes del servicio afectado. D-16 sigue pendiente; datos de prueba
identificados no son valores oficiales ni prueban la adopción de una regla.

## 4. Hitos propuestos

H0–H6 no equivalen a días literales de PR07 ni comprometen fechas nuevas.

| Hito | Estado y condición de avance |
| --- | --- |
| H0 · Base | Bootstrap, apps actuales bajo apps/ y perfiles iniciales documentados. Día 1: check y cuatro tests correctos, sin nuevas migraciones y servidor con HTTP 200; evidencia histórica, no ejecución nueva ni validación del dominio V2. |
| H1 · Diseño/documentación | Candidata V2 y ERD interno existentes; acuerdos 08/10 y notas de la daily 09/10 consolidados para revisión. Rewards v0 candidato. Pendientes condiciones funcionales/Core, B/C y contratos antes de ORM afectado; no completado globalmente. |
| H2 · ORM y servicios | Futuro: modelos/migraciones y servicios tras H1 revisado, con propiedad por dominio y D-19. No crear apps ni servicios por esta consolidación. |
| H3 · Vertical mínima | Futuro: actividad, recompensa, compra y equipamiento con interfaz/permiso. Training distingue XP repetible/límite monetario; Escape distingue parcial/final. No imponer autoequipamiento. |
| H4 · CRUD/historiales/Museo | Futuro: alcance evaluable acordado, historiales de A/B/Bank y composición Museo sin editar arbitrariamente estados derivados. |
| H5 · Robustez | Futuro: integridad, duplicados, conflictos, límites, fallos, autorización y concurrencia. Las pruebas empiezan en H2. |
| H6 · Integración/demo/evidencias | Futuro: Core y juegos, REST y cobertura realtime acordada, demo y aportaciones individuales. RPG completo, apuestas, externo y pedidos físicos según alcance confirmado. |

Se conserva DAR3: demo inicial con Prehistoria, Grecia y Roma; no equivale al
catálogo completo de siete etapas. Historiales y Museo requieren priorización,
no eliminación. Techies/cotización variable fuera de primera entrega.
El antecedente de DAR3 sobre seis piezas principales por época no implica crear
seis campos por etapa ni equiparlas automáticamente. Rangos/especializaciones, catálogo y efectos avanzados quedan sujetos
a condiciones del ERD y pendientes, no se descartan por una propuesta de MVP.

## 5. Backlog por responsable

### Jaime · Parte A

- Obtener aclaraciones P1/P2/P3/P7/P8 y coordinar R1–R8 de pendientes.
- Revisar servicio independiente de puntos y premios sin XP; XP histórica y de
  dominio distintas, sin XPEvent ficticios. Mantener las condiciones físicas
  provisionales de Parte A y M-01.
- Acordar consultas de progreso/stats y encaje calculate-action/commit-rewards;
  coordinar Escape actualizado y Training con sus emisores.
- Después de H1, implementar y probar progreso, inicialización, transiciones,
  puntos, Rewards y lecturas de historial/Admin del alcance validado.

### Henry · Parte B

- Diseñar/revisar Duckies, objetos, posesión, cantidades, consumos, compatibilidad
  y equipamiento; aclarar vestimenta con Óscar, incluida su conservación.
- Acordar efectos idempotentes y referencias con Rewards, entrega Shop y
  composición de historiales/Museo con A, sin escritura directa entre dominios.
- Revisar diccionario antes del ORM; después servicios, interfaz y pruebas
  de posesión, cantidades, consumos, reintentos y equipamiento.

### Fernando · Parte C

- Revisar primero la implementación existente de Óscar y su encaje con la candidata,
  antes de crear servicios equivalentes de Bank o recompensas.
- Revisar Bank/Shop, fuentes de verdad, movimientos y distinción del catálogo
  comercial frente a identidad de objetos de Duckies.
- Acordar créditos Rewards y compra/cargo/entrega: coordinador, claves,
  validaciones y rollback/recuperación. Rewards v0 no aprueba el contrato de compra.
- Si apuestas entran en V1, revisar con Clash reserva de ambos al aceptar,
  liberación/liquidación/cancelación/timeout; no deducir inclusión obligatoria.
- Tras revisión, implementar créditos/débitos/compras y pruebas; preparar
  historial, Admin/CRUD e integración sin modificaciones a su rama desde esta tarea.

Bank asume la responsabilidad contable; Ecomotor coordina funcionalmente Rewards.
Garantías a implementar y comprobar: `saldo >= 0`, fondos suficientes antes de
cada débito, créditos y débitos sin repetición por reintentos, comportamiento
correcto ante concurrencia y movimientos trazables con origen y motivo.
Las compras coordinan saldo e inventario. Si se implementan apuestas de Clash,
se reservan ambas apuestas al aceptar el duelo; DAR3 permite una primera entrega
sin apuestas. D-19 es una decisión técnica del Equipo 5, no una configuración de DAR3.

## 6. Pruebas futuras y criterio de cierre

No se añaden ni ejecutan tests Django en este PR documental.

| Área | Comprobaciones tras validar diseño |
| --- | --- |
| A | XP histórica no decreciente; niveles/etapas independientes y transiciones múltiples; stats/puntos, inicialización idempotente sin eventos ficticios; legacy fail-closed. |
| B | Posesión/cantidades, concesiones/consumos idempotentes, compatibilidad y equipamiento; historiales y objetos por condiciones acordadas. |
| C | `saldo >= 0` y fondos suficientes antes de débito; créditos/débitos sin duplicados, concurrencia, movimientos con origen/motivo y consistencia cargo-entrega; reserva de ambas apuestas al aceptar solo bajo alcance confirmado. |
| Rewards | APPLIED/NO_REWARD repetidos, conflicto, premios sin XP, referencias a efectos, versiones, rollback de cada propietario y autorización. |
| Training/Escape | Hechos distintos compitiendo por límite monetario diario; parcial/final sin doble premio; penalización provisional sin pérdida de XP consolidada. |
| D-19 | TransactionTestCase y al menos una ejecución SQLite file-backed: escritores concurrentes, locks/timeout, misma clave, rollback y retry en nueva transacción. |
| PR07/integración | CRUD evaluable de al menos dos entidades apropiadas; validación de formularios, permisos/aislamiento entre usuarios y pruebas HTTP de respuestas/redirecciones 200/302/403/404 donde corresponda; contratos REST/realtime validados. |

D-19 permanece íntegra; la transacción exterior compartida es propuesta
condicionada a misma BD/conexión, no garantía entre servicios independientes.
No introducir I/O externo en transacciones.

Como criterio operativo propuesto, cerrar una funcionalidad exige comportamiento
integrado, reglas servidor, pruebas críticas, revisión comprensible por otro
integrante, diseño revisado y aportación trazable. La autonomía técnica interna
reversible no autoriza cerrar unilateralmente reglas o contratos compartidos.

## 7. Git y siguientes entregables

Se mantienen main estable, develop integración y ramas feature/*, fix/* y docs/*.
Aportaciones individuales mediante commits/PR y trazabilidad incluso con squash.
Entregables previstos de PR07: ERD con cardinalidades, relaciones y reglas
`on_delete`, diccionario de datos, ORM y migraciones tras las decisiones necesarias,
CRUD evaluable de al menos dos entidades, permisos, formularios y pruebas HTTP.
Conservar pruebas de integridad, recompensas e importes junto con las evidencias Git.
`docs/postmortem-bugs.md` recogerá los tres bugs más complejos encontrados y su
resolución; no se inventan bugs ni se crea ese documento en esta consolidación.
El tag Git `v1.0.0` es un hito previsto de release, junto con PR de release,
instrucciones de despliegue local y presentación/demo, no una tarea inmediata.

Este único cambio documental queda para revisión antes de commit/push/PR.
Actualizar plan/pendientes cuando llegue una respuesta y registrar acuerdos
formales cuando corresponda. No inventar respuestas del profesor ni presentar
esta propuesta como aprobación global del ERD V2.
