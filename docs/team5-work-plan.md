# Plan de trabajo · Estado hasta S7-A y pendientes del Equipo 5

## 1. Estado y referencias

El reparto y apps objetivo del 08/10 son acuerdos internos D-20/D-21.
Corte DOC-1 del 18/10/2026: develop en `b42cb5f` (PR #32), conservado como antecedente.
Actualización DOC-6: develop `5a4e079` incorpora Fase 1 por PR #38; §3.1 distingue
ese núcleo integrado de F2-A aprobado internamente y bloqueado hasta Core. Los estados siguientes
distinguen implementación local, aprobación interna pausada, decisiones pendientes
y dependencias externas; no aprueban contratos compartidos ni alcance final V1.

[Arquitectura](architecture.md) concentra fuentes funcionales y notas de las dailys;
[decisiones](decisions.md), acuerdos; [pendientes](pending-decisions.md), preguntas;
[Rewards v0](contracts/rewards-v0.md), contrato candidato;
[ERD Parte A](erd/ecomotor.md), ocho entidades históricas V2 más StatAllocationEvent integrado en S7-A.
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
| Jaime | A · `apps.ecomotor`: Ecomotor, Rewards, XP, evolución, especializaciones y stats | S1–S7-A integrados; S8-A aprobado y pausado. Continuar con configuración autorizada, especializaciones/XP de dominio y Rewards según decisiones y contratos pendientes. |
| Henry | B · `apps.duckies`: Duckies, avatar, objetos, inventario y equipamiento | Revisar catálogo/posesión, concesiones/consumos, compatibilidad y contrato de objetos con Rewards/Shop. |
| Fernando | C · `apps.bank` y `apps.shop`: wallet, movimientos, catálogo comercial y compras | Revisar diseño B/C, créditos/débitos idempotentes, coordinación de compra y reservas solo si se incluyen apuestas. |
| Equipo 5 con Óscar/Core | `apps.users` conservada; integración de identidad/JWT | Resolver autenticación, permisos, conservación y legacy antes de la parte afectada. |

D-20 sustituye para la planificación el antiguo reparto propuesto D-13,
conservado como antecedente. D-21 no crea apps en este PR ni mueve perfiles.
D-18 mantiene rutas/labels actuales; D-17/D-19 no cambian.
La rama de Fernando requiere revisión antes de integrar y no se modifica aquí.

## 3. Orden de trabajo y condiciones

**Dependencia de integración:** acordar con Óscar/Core y Fernando la fuente
canónica de Wallet/saldo, identidad/autorización, movimientos, idempotencia,
concurrencia y contratos Rewards/Bank/Shop. Daily del 13/10/2026: no es obligatorio
esperar ni reutilizar el controlador antiguo sencillo de DuckyCoins para continuar
nuestro desarrollo. La aclaración se limita a ese componente; no declara
desaparecidos todos los servicios anteriores de recompensas, puntos o economía.
Consultar código previo es opcional si resulta útil; no se conocen aquí sus firmas,
modelos o estructura verificados. La integración requiere coordinación con Henry,
Fernando, Core y consumidores, sin duplicar Wallet, saldo canónico o recompensas;
Rewards v0 conserva su estado candidato.

1. **Reglas que cambian comportamiento:** confirmar alcance/vigencia de XP externa,
   stats editables en Actual, iniciales/límites y posibles puntos/objetos de cursos;
   preservar progreso existente. Consultar Escape consolidado.
2. **Contrato compartido:** revisar Rewards v0 con Henry/Fernando, Óscar/Core y
   juegos: identidad, huella, reglas/resultados, claves locales y transacción
   compartida con misma BD/conexión.
3. **Diseño físico compartido:** revisar conservación/FKs/on_delete y consolidar
   A/B/C antes del ORM afectado. El esquema local A ya está integrado;
   RewardRule/RewardEvent no son tablas aprobadas.
4. **Servicios y vertical:** S1–S7-A locales están implementados. La vertical
   multidominio requiere diseño y alcance revisados: actividad validada → premio → progreso/monedas/objetos
   → compra → equipamiento → historial conforme a DAR3.
5. **Evaluación/integración:** Admin, CRUD evaluable, permisos, tests y evidencias
   PR07; validar REST, realtime y RPG con Óscar/Core/juegos sin aplazarlos
   globalmente por propuestas de participantes.

Los parámetros configurables no bloquean todo el diseño conceptual.
Cambios de reglas, como elegibilidad de XP o condiciones de stats, sí requieren
acuerdo antes del servicio afectado. D-16 sigue pendiente; datos de prueba
identificados no son valores oficiales ni prueban la adopción de una regla.

### 3.1. Fases Rewards · T8 aprobado internamente (DOC-4)

Orden aprobado por Jaime el 18/10/2026, después de R1–R8 integradas por PR #35.
[T1–T8](decisions.md#doc-4--diseño-técnico-rewards-v1--t1t8--18102026) son diseño
interno, no contrato global ni implementación. Cada fase exige un incremento
pequeño, testeable y revisado mediante PR separado; DOC-4 no inicia ninguna.

| Orden | Incremento posterior | Condición y límite |
| --- | --- | --- |
| 1 | **Integrada: F1-A, PR #38.** Tipos, validaciones, canonicalización, huella y evaluador puro con reglas ficticias de tests. | Sin ORM, efectos reales ni migraciones; no activa baremos ni el servicio transaccional. |
| 2 | **F2-A: arquitectura aprobada internamente por Jaime (DOC-6); sin implementar.** RewardEvent candidato, XP histórica positiva mediante S3, NO_REWARD, snapshot histórico y replay. | Tabla/migración bloqueadas hasta Core: User/PK, conservación/anonimización/eliminación, on_delete/relaciones y autorización. Misma BD/conexión/alias, D-19 y causalidad; sin inicialización automática ni cambios S3/Fase 1. |
| 3 | Cupos: RewardLimitUsage y pruebas concurrentes. | Modelo aún candidato, D-19; día efectivo/hechos tardíos/reglas por acordar. No activar economía sin contrato Bank. |
| 4 | Bank, Duckies, juegos y REST. | Solo con contratos propietarios y autenticación acordados; sin atomicidad remota supuesta ni API/batch/WebSockets definitivos. |

[Detalle F2-A](contracts/rewards-v0.md#12-f2-a--persistencia-y-xp-histórica-local--doc-6)
y [bloqueos DOC-6](pending-decisions.md#9-bloqueos-de-persistencia-rewards-f2-a--doc-6)
precisan la fase 2; [pendientes DOC-4](pending-decisions.md#7-validación-residual-del-diseño-técnico--doc-4)
conserva las validaciones posteriores. No se completa Fase 2 por aprobar el diseño.
Premios reales exigen configuración de evolución válida y reglas autorizadas.
Bank/Duckies/juegos no bloquean el diseño local F2-A, pero siguen fuera junto con
monedas, dominio, puntos directos, cupos, REST/WebSockets/batch y compensaciones.
Un efecto no soportado rechaza toda la operación, sin descartarlo ni convertirlo
en NO_REWARD.
Los servicios locales S1–S7-A siguen integrados; S8-A permanece aprobado y pausado.
La regresión histórica comunicada en DOC-1/DOC-4 es de 407 tests correctos.
La última regresión comunicada tras Fase 1 es de 463 tests correctos, según el
informe de Codex. En DOC-6 no se han ejecutado tests Django: la PR es
exclusivamente documental, sin cambios de modelos, servicios, migraciones ni tests.

## 4. Hitos y estado vigente

H0–H6 no equivalen a días literales de PR07 ni comprometen fechas nuevas.

| Hito | Estado y condición de avance |
| --- | --- |
| H0 · Base | Bootstrap, apps actuales bajo apps/ y perfiles iniciales documentados. Día 1: check y cuatro tests correctos, sin nuevas migraciones y servidor con HTTP 200; evidencia histórica, no ejecución nueva ni validación del dominio V2. |
| H1 · Diseño/documentación | Candidata V2 y ERD interno existentes; acuerdos 08/10 y notas de la daily 09/10 consolidados para revisión. Rewards v0 candidato. Pendientes condiciones funcionales/Core, B/C y contratos antes de ORM afectado; no completado globalmente. |
| H2 · ORM y servicios | Implementado localmente en A: Día 4 (PR #23/#24), S1/S1.1 (#22), S2-A (#27), S3 (#28), S4-A (#29), S6-A (#31) y S7-A (#32). F1-A integrada por PR #38 (núcleo puro); pendientes especializaciones, XP de dominio y persistencia/coordinación Rewards F2-A; B/C e integración global dependen de sus contratos y migraciones. |
| H3 · Vertical mínima | Futuro: actividad, recompensa, compra y equipamiento con interfaz/permiso. Training distingue XP repetible/límite monetario; Escape distingue parcial/final. No imponer autoequipamiento. |
| H4 · CRUD/historiales/Museo | Implementados Admin seguro (#25 y evento S7-A), consultas/historial XP S4-A y página personal GET/HEAD S5-A (#30). S8-A aprobado por Jaime, pausado sin implementación. CRUD evaluable PR07, historial web de asignaciones y Museo compartido siguen pendientes de alcance. |
| H5 · Robustez | Tests locales implementados: integridad/migraciones, Admin, servicios, consultas, HTTP, replay/conflictos, rollback y concurrencia SQLite file-backed. Regresión histórica DOC-1/DOC-4: 407 tests correctos. Última regresión comunicada tras Fase 1: 463 tests correctos, según el informe de Codex. En DOC-6 no se han ejecutado tests Django por ser una PR exclusivamente documental. Robustez multidominio y autorización global siguen pendientes. |
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
- S7-A ya gasta puntos disponibles con coste 1:1 en Actual e historial idempotente.
  Sigue pendiente conceder puntos directos como premio sin XP; no es la asignación
  de S7-A. XP histórica y de dominio siguen separadas, sin eventos ficticios; M-01 vigente.
- S4-A/S5-A ya consultan progreso e historial; acordar integración con
  calculate-action/commit-rewards, Escape actualizado y Training con sus emisores.
- S1–S7-A están integrados y no esperan la integración global para su diseño local.
  S8-A, interfaz GET/POST basada exclusivamente en S7-A, está aprobado y pausado por
  prioridad documental; reanudar solo conforme a ese alcance, sin incluirlo en DOC-1.
- Pendientes: configuración funcional e instalación real (S6-A no la activa),
  especializaciones/XP de dominio, persistencia/coordinación Rewards F2-A y contratos Core/A/B/C/juegos. Fase 1 ya está integrada, sin efectos reales.

### Henry · Parte B

- Diseñar/revisar Duckies, objetos, posesión, cantidades, consumos, compatibilidad
  y equipamiento; aclarar vestimenta con Óscar, incluida su conservación.
- Acordar efectos idempotentes y referencias con Rewards, entrega Shop y
  composición de historiales/Museo con A, sin escritura directa entre dominios.
- Revisar diccionario antes del ORM; después servicios, interfaz y pruebas
  de posesión, cantidades, consumos, reintentos y equipamiento.

### Fernando · Parte C

- Acordar con Core el encaje económico de la candidata y la fuente canónica del
  saldo. Consultar código anterior de Óscar es opcional: la daily del 13/10/2026
  aclaró que no es necesario esperar ni reutilizar el controlador antiguo sencillo
  de DuckyCoins para continuar; identidad/autorización, movimientos, idempotencia,
  concurrencia y contratos Rewards/Bank/Shop siguen pendientes.
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

## 6. Pruebas existentes, pendientes y criterio de cierre

No se añaden ni ejecutan tests Django en este PR documental.

| Área | Comprobaciones existentes / pendientes |
| --- | --- |
| A | Implementados tests de S1–S7-A, Admin, modelos y migraciones: progresión, inicialización, XP, consultas, HTTP y asignación idempotente. Legacy fail-closed local no cierra conservación global ni configuración autorizada. Especializaciones/XP de dominio y persistencia/coordinación Rewards pendientes; núcleo puro F1-A integrado por PR #38. |
| B | Posesión/cantidades, concesiones/consumos idempotentes, compatibilidad y equipamiento; historiales y objetos por condiciones acordadas. |
| C | `saldo >= 0` y fondos suficientes antes de débito; créditos/débitos sin duplicados, concurrencia, movimientos con origen/motivo y consistencia cargo-entrega; reserva de ambas apuestas al aceptar solo bajo alcance confirmado. |
| Rewards | APPLIED/NO_REWARD repetidos, conflicto, premios sin XP, referencias a efectos, versiones, rollback de cada propietario y autorización. |
| Training/Escape | Hechos distintos compitiendo por límite monetario diario; parcial/final sin doble premio; penalización provisional sin pérdida de XP consolidada. |
| D-19 | Existen TransactionTestCase file-backed para S2-A/S3/S7-A: escritores, locks/timeout, replay/conflictos, rollback y retry. Se mantiene la exigencia para futuros servicios; no garantiza atomicidad multidominio. No reejecutados en DOC-1. |
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

DOC-1 sincroniza exclusivamente documentación; DOC-2/DOC-3 y S8-A quedan fuera.
Actualizar plan/pendientes cuando llegue una respuesta y registrar acuerdos
formales cuando corresponda. No inventar respuestas del profesor ni presentar
esta propuesta como aprobación global del ERD V2.
