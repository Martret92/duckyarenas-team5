# Plan de trabajo V2 · Equipo 5

Estado: propuesta operativa para revisión por los tres integrantes del Equipo 5.

[architecture.md](architecture.md) describe arquitectura y límites;
[decisions.md](decisions.md) registra decisiones confirmadas y separa propuestas;
[pending-decisions.md](pending-decisions.md) recoge asuntos abiertos.
Este plan sirve como guía práctica de trabajo, no como aprobación de modelos o contratos.

## 1. Alcance y procedencia

DAR3 sigue siendo la fuente general principal. Según los requisitos recogidos
en la documentación del repositorio, atribuye al Equipo 5:

- Parte A: Ecomotor y evolución.
- Parte B: Avatar e inventario.
- Parte C: Ecommerce y DuckyBank.
- Servicio común de recompensas.

DAR3 exige progreso, inventario, economía y recompensas validados por el servidor,
prevención de duplicados y consistencia de las compras. El servidor es la fuente
de verdad para XP, evolución, inventario, DuckyCoins, compras y recompensas.
La sección 10 requiere coordinación de recompensas con el Equipo 0 y los juegos.
DAR3 no asigna individualmente A/B/C a Jaime, Félix y Henry.

Las especificaciones posteriores `DuckyEcomotor.pdf` y `DAR_formulas.pdf`,
facilitadas por Óscar, actualizan explícitamente determinados aspectos de DAR3.
Esta revisión utiliza la información contrastada externamente y trasladada a
[architecture.md](architecture.md); no afirma lectura directa de los PDF.
Se distinguen requisitos documentales, decisiones vigentes, propuestas internas,
trabajo completado y trabajo pendiente.

La candidata V2 y la actualización de decisiones/pendientes se integraron en
`develop` mediante PR #15, squash `256dd9e`. Esto es un hito documental, no una
aprobación global de Óscar, Core o todos los integrantes. El reparto, las fronteras,
la autonomía, los hitos y el backlog continúan siendo propuestas.
El [ERD y diccionario V1 de Parte A](erd/ecomotor.md) ya existe como antecedente
interno A-01…A-16. Su adaptación a V2 y los contratos A/B/C siguen pendientes;
no se implementará ORM definitivo desde reglas V1 incompatibles ni se darán
D-13…D-16 por validadas.

### PR07 como marco transversal complementario

PR07 · Ciclo de vida de una aplicación web es la referencia de proceso y
evaluación recogida en el repositorio; no se consulta directamente en esta revisión.
DAR3 sigue siendo la fuente funcional principal. PR07 aporta estructura, proceso, entregables y
evaluación: apps bajo `apps/`; diseño conceptual con ERD y diccionario antes
del ORM; cardinalidades y reglas `on_delete`; modelos y migraciones; Admin;
URLs, vistas, templates, navegación, listados, detalles, formularios y CRUD;
permisos, seguridad y tests; evidencias Git y PR (páginas 4-11 y 17).

La adaptación física a `apps/` ya está completada y validada (D-18). Las rutas
Python canónicas son `apps.ecomotor` y `apps.users`; los labels Django siguen
siendo `ecomotor` y `users`. Se preservaron los modelos y migraciones existentes.
La parte estructural y técnica aplicable del Día 1 queda completada: `config/`,
`apps/`, `requirements.txt`, `.gitignore`, `check` correcto, cuatro tests correctos,
sin nuevas migraciones y servidor con HTTP 200. CustomUser/auth sigue pendiente
bajo D-17. El siguiente paso es diseño conceptual, ERD y diccionario revisados
antes del ORM de dominio; el Día 2 no está completado.
El CRUD de al menos dos entidades principales exigido por PR07 debe concretarse
con el profesor. No implica permitir modificaciones arbitrarias de XP,
evolución o registros financieros al margen de sus operaciones de dominio.

PR07 pide en su plan detallado CustomUser con `AbstractUser` y autenticación
local. Hasta aclarar el conflicto se mantienen D-09 y D-10 según D-17: User
estándar, sin cambiar `AUTH_USER_MODEL` ni migraciones por ese motivo y sin
implementar registro/login/logout local. Los permisos deberán encajar con la
solución aclarada. También está pendiente si el calendario de 15 días y sus
entregables Git son literales o una guía/rúbrica; H1–H6 no equivalen a sus días.

## 2. Modelo funcional y cuestiones de adaptación

### Progreso histórico y evolución

| Orden de etapa (no nivel) | Etapa |
| --- | --- |
| 1 | Prehistoria |
| 2 | Griega |
| 3 | Romana |
| 4 | Renacentista |
| 5 | Contemporánea |
| 6 | Siglo XX |
| 7 | Actual |

La XP histórica es acumulativa y no decreciente: no se gasta en compras ni se
reduce por consumo o penalizaciones económicas. Nivel, etapa y progreso son
conceptos distintos; la barra visual representa el estado canónico. La evolución
es automática cuando se cumplen los requisitos definidos. No se inventan umbrales,
fórmulas ni condiciones; su representación y las transiciones múltiples deben
revisarse en el ERD V2 conservando trazabilidad.

### Equipamiento y objetos

DAR3 conserva seis piezas principales por época, diferenciadas de complementos
estéticos. Su adaptación a siete etapas y cobertura V1 están pendientes. El ERD
V1 concedía conjuntos completos y equipaba automáticamente al inicializar y
evolucionar: es un antecedente que requiere revisión formal, no una instrucción
V2 aprobada. Apariencia y equipamiento no sustituyen el progreso canónico.

Inventory define identidad de objetos, posesión, cantidades, concesiones y
consumos; Avatar/Equipment valida compatibilidad y posesión. Shop mantiene ofertas,
precios y disponibilidad comercial. Deben aclararse conservación y reequipamiento
de conjuntos, efectos de consumibles y encaje de tienda estética/combate, incluida
la regla anterior de conjuntos históricos no comprables, sin resolverla unilateralmente.

### Especializaciones

Developer, Ciberseguridad, Sistemas, Data y Gamer aparecen dentro de Actual.
Quedan pendientes normalización Data / Data & IA y nombres anteriores, acceso,
cambios, conservación de progreso, XP y rangos. Era Digital y los rangos fijos
antiguos pertenecen al antecedente V1; no se adoptan automáticamente para V2.

### Stats y recompensas

Las estadísticas canónicas son `ATK`, `DEF`, `LOG`, `SPE`, `VEL`, `INT`.
Cálculo o persistencia, fórmulas, efectos de objetos y parámetros deben concretarse
para el alcance acordado. Ecomotor es la autoridad candidata sobre stats y progreso.
Rewards se plantea como capacidad coordinada por Ecomotor que evalúa reglas y
solicita monedas a Bank y objetos a Inventory. Puntuación provisional de partida,
resultado validado, recompensa y XP histórica consolidada son estados distintos.
No se aprueban aquí modelos, apps, endpoints ni contratos nuevos.

El detalle funcional está en arquitectura §§3–8; las preguntas operativas,
responsables e impactos están en [pending-decisions.md](pending-decisions.md).

## 3. Reparto y fronteras propuestos

Pendiente de revisión por los tres integrantes del Equipo 5, incluida la
confirmación con Félix y Henry (D-13 a D-15). No es una asignación individual de DAR3.

### Jaime · Parte A

Responsabilidad propuesta: XP, progreso, evolución, especializaciones, stats,
historiales y coordinación de Rewards. Prioridad inmediata: revisar decisiones
estructurales y adaptar el ERD/diccionario V1 a V2. A decide progreso y solicita
operaciones a los propietarios B/C; no escribe inventario ni saldo directamente.

### Félix · Parte B

Responsabilidad propuesta: identidad/definición de objetos, Inventory, posesión,
cantidades, Avatar/Equipment e historial de equipamiento. Coordina conjuntos,
compatibilidad y lecturas para Museo con A. Equipamiento automático sigue pendiente.

### Henry · Parte C

Responsabilidad propuesta: Bank (wallet, saldo y movimientos), catálogo comercial,
Shop y compras. Bank es el único propietario del saldo; Shop no posee inventario.

### Fronteras y dependencias candidatas

| Área | Autoridad candidata y coordinación |
| --- | --- |
| A / Ecomotor | XP, evolución, especializaciones y stats; evalúa Rewards y participa documentalmente en comprobaciones de compra |
| B / Inventory | Identidad/definición de objetos y posesión; concede, consume y valida cantidades |
| B / Avatar-Equipment | Apariencia, compatibilidad y estado de equipamiento; consulta posesión a Inventory |
| C / Bank | Saldo y movimientos; valida y ejecuta créditos/débitos idempotentes |
| C / Shop | Ofertas, precios, disponibilidad comercial y compra; coordina pago y entrega |

El catálogo de objetos de B se distingue del catálogo comercial de C; esta
interpretación y su relación con D-15 requieren validación conjunta, sin modificar
la propuesta registrada. También debe acordarse cómo Ecomotor comprueba condiciones
y consulta saldo con Shop/Bank/Inventory, y quién coordina la compra completa.

## 4. Rewards, contratos y dependencias

D-14 mantiene Rewards como propuesta compartida, coordinada inicialmente desde A.
El flujo conceptual es actividad validada → evaluación de regla e idempotencia →
operaciones propietarias de XP/monedas/objetos → trazabilidad y resumen.
No fija orden de escrituras ni garantiza atomicidad global.

El mínimo funcional DAR3 ya está recogido en arquitectura §8. H1 debe acordar
contratos internos mínimos, identidad, claves, errores/reintentos y fronteras
transaccionales; los contratos externos se validan con Core y juegos antes de
integrar. Reglas configurables, vigencia, límites, compatibilidad y repetibilidad
se concretarán para V1 sin aprobar `RewardRule`/`RewardEvent` como ORM.

- A/B: concesiones, equipamiento y efectos de objetos; conservar trazabilidad.
- A/C: monedas de Rewards y participación de Ecomotor en comprobaciones de compra.
- B/C: Shop referencia objetos de Inventory y solicita entrega tras compra válida.
- A/B/C: coordinador, claves idempotentes y rollback o recuperación de fallos parciales.
- Core: User, JWT, autorización e integración global; sin autenticación paralela.
- Juegos: resultados validados y consultas canónicas de progreso/stats; no imponen
  XP/monedas ni escriben estado del Equipo 5.

REST y WebSockets son arquitectura objetivo documental. Formatos, eventos,
productores/consumidores, infraestructura y cobertura V1 siguen pendientes;
servicios Python internos no requieren HTTP obligatorio.

## 5. Autonomía propuesta y revisión conjunta

Se propone que cada responsable pueda decidir detalles técnicos internos sin
esperar aprobación previa cuando sean compatibles con DAR3, respeten las
decisiones registradas y no cambien contratos compartidos ni responsabilidades
de otra parte. Además, deben ser razonablemente reversibles, estar cubiertos por
tests y revisarse mediante Pull Request.

Requieren revisión conjunta las fronteras A/B/C, el contrato Rewards, las reglas
funcionales, los cambios que afecten varios dominios y las interfaces con otros
equipos. Esta regla operativa también está pendiente de validación conjunta;
no autoriza a dar por definitivos asuntos abiertos en D-07.

## 6. Plan por hitos

H0–H6 son una propuesta operativa sin fechas, no una equivalencia con los días
PR07. Los responsables pueden avanzar conceptualmente en paralelo; cerrar ORM
requiere diseño revisado del dominio y acuerdos compartidos necesarios.

| Hito | Estado, entregable y dependencias |
| --- | --- |
| H0 · Base | Completados bootstrap, estructura bajo `apps/`, perfiles iniciales y comprobaciones documentadas del Día 1 (check, cuatro tests, migraciones y HTTP 200). Core/PR07 y D-17 continúan pendientes; no está completada toda PR07. |
| H1 · Diseño conceptual y documentación | Parcial: candidata V2, registro y lista operativa integrados en PR #15; ERD/diccionario V1 de A existente. Pendientes decisiones estructurales, adaptación de A a V2, diseños y consolidación A/B/C, y fronteras/contratos mínimos de Rewards y compras antes del ORM afectado. No completado globalmente. |
| H2 · Modelos y servicios de dominio | Pendiente tras revisar ERD/diccionario y contratos necesarios. Implementar servicios reutilizables y modelos/migraciones del alcance acordado; no usar automáticamente reglas V1 incompatibles ni cambiar User/auth. Tests críticos con cada operación. |
| H3 · Admin, interfaz y vertical mínima | Pendiente tras H2: Admin, URLs, vistas, templates, formularios y permisos. Demo de actividad validada → recompensa → progreso/monedas/objetos → compra e inventario/equipamiento según acuerdos. DAR3 contempla Prehistoria, Grecia y Roma para demo, distintas del catálogo de siete etapas. El equipamiento automático continúa pendiente de confirmación. |
| H4 · CRUD, historiales y Museo | Pendiente tras diseño e interfaz: CRUD evaluable aclarado con Óscar, historiales de XP/evolución/equipamiento y Bank, y Museo según cobertura acordada. Lecturas y permisos respetan operaciones de dominio. |
| H5 · Seguridad, testing y robustez | Pendiente: completar revisión transversal de permisos, integridad, idempotencia, fallos parciales y concurrencia D-19. Los tests empiezan en H2; al menos una ejecución crítica SQLite file-backed con TransactionTestCase. |
| H6 · Integración, evidencias y demo | Pendiente: Core y equipos 1–4, contratos acordados, tests integrados, datos demo, documentación y contribuciones identificables mediante Git/PR. Alcance final y calendario sujetos a aclaración; sin comprometer RPG completo, WebSockets o integraciones externas por defecto. |

D-19 fija la política transversal SQLite V1: `IMMEDIATE`, timeout de 5 segundos
y `transaction.atomic()` antes de leer estado mutable en escrituras críticas.
Los servicios deberán mantener transacciones cortas, constraints e idempotencia
persistente; la configuración no sustituye los contratos ni decide las fronteras
transaccionales de Rewards/A/B/C. Su implementación y tests siguen pendientes.

## 7. Backlog inicial por integrante

Reparto individual propuesto bajo D-13, pendiente de aceptación conjunta. El
backlog no convierte A-01…A-16 en instrucciones V2 para puntos incompatibles.

### Jaime · A (propuesto)

1. Revisar decisiones estructurales de progresión, especializaciones, stats,
   Rewards e historiales, con la lista de pendientes y alcance V1.
2. Adaptar ERD V2 y diccionario desde el antecedente existente, documentando
   cardinalidades, restricciones y `on_delete`, sin nuevos campos ORM aquí.
3. Validar dependencias y contratos mínimos con B/C y Core, incluidos claves y
   coordinador; elevar a Óscar solo ambigüedades funcionales.
4. Tras revisión H1, implementar servicios y modelos/migraciones H2 del alcance
   acordado, sin asumir equipamiento automático ni rangos antiguos.
5. Probar progreso, XP no decreciente, evolución múltiple, Rewards, idempotencia
   y concurrencia; después lecturas, Admin, historial/CRUD y demo H3–H6.

### Félix · B (propuesto)

1. Diseñar identidad/definición de objetos, posesión, cantidades, equipamiento e
   historiales; adaptar conjuntos de seis piezas a etapas sin inventar contenido.
2. Acordar con A inicialización, concesión y comportamiento de equipamiento;
   con C referencias comerciales y entrega, distinguiendo ambos catálogos.
3. Revisar ERD/diccionario antes de ORM y servicios H2; no aprobar equipamiento
   automático por conservarlo en el antecedente V1.
4. Preparar interfaz, apariencia y Museo/CRUD según alcance H3–H4.
5. Probar posesión, cantidades, consumos, compatibilidad, aislamiento, idempotencia
   y concurrencia; integrar concesiones Rewards y entregas Shop H5–H6.

### Henry · C (propuesto)

1. Diseñar Bank, movimientos, catálogo comercial, Shop y compras; revisar
   ERD/diccionario y separar ofertas comerciales de identidad de objetos.
2. Acordar con A/B participación de Ecomotor, cargo, entrega, claves y coordinador
   de compras/recompensas; no prometer atomicidad entre servicios independientes.
3. Tras H1, implementar créditos, débitos y compra en servidor bajo D-19.
4. Preparar Admin, interfaz, historial Bank y CRUD acordado H3–H4.
5. Probar fondos insuficientes, saldo no negativo, cargos/entregas sin duplicados,
   fallos parciales y concurrencia; integrar demo y datos comerciales H5–H6.

## 8. Datos provisionales y pendientes

La propuesta operativa amplía el uso previsto en D-16 a umbrales, XP, DuckyCoins,
precios, nombres/contenido de objetos, efectos y datos demo. Esta política sigue
pendiente de validación; los efectos ficticios no determinan reglas oficiales de juego.
Los valores deben marcarse como provisionales, separarse de la lógica, evitar
números mágicos y poder sustituirse. Los tests pueden usar datos propios para
verificar comportamiento, sin presentarlos como requisitos reales.

Una cuestión puramente paramétrica no debe bloquear el desarrollo: se propone
usar datos de prueba explícitos mientras se espera el valor oficial. La arquitectura
se diseñará para sustituir parámetros sin cambiar la lógica; si el profesor cambia
también reglas funcionales, se revisará la arquitectura correspondiente.

La lista operativa de [pending-decisions.md](pending-decisions.md) es la fuente
para responsables, impacto y condiciones de cierre; este plan no la duplica.

El siguiente paso es iniciar la adaptación conceptual del ERD V2 de A: no hace
falta esperar todos los parámetros oficiales ni diseños definitivos de otros
equipos. Para cerrarlo deben concretarse representación de progreso y evolución,
especializaciones y stats incluidos, persistencia de historiales y relaciones
compartidas. Las claves, fronteras transaccionales y contratos necesarios deben
cerrarse antes del ORM/servicio afectado, sin bloquear todo el diseño conceptual.

### Alcance aplazable por acuerdo

Contenido de etapas fuera de la demo, especializaciones completas, efectos
avanzados, interfaz avanzada del Museo, RPG completo, WebSockets, integraciones
externas y pedidos físicos no se comprometen para V1 sin confirmar cobertura.
Techies y cotización variable se mantienen fuera de prioridad según antecedentes
DAR3. Aplazar cobertura no elimina requisitos ni sustituye la confirmación del
alcance evaluable con Óscar.

## 9. Tests mínimos por área

Los cuatro tests correctos del bootstrap son evidencia histórica del setup, no
validación del dominio V2 ni una nueva ejecución en esta tarea. Los siguientes
tests corresponden a requisitos y reglas finalmente acordadas;
no existen todavía como tests implementados de dominio.

| Área | Comprobaciones mínimas |
| --- | --- |
| A | XP no decreciente; nivel/etapa/progreso separados; evolución automática según condiciones acordadas y transiciones múltiples; stats y efectos confirmados; historial; idempotencia de XP/evolución. |
| B | Posesión y cantidades; concesiones/consumos idempotentes; compatibilidad; conjuntos de seis piezas según adaptación revisada; equipamiento e historial conforme a reglas acordadas, sin imponer automatismo; aislamiento entre usuarios. |
| C | Ingresos, fondos suficientes y saldo no negativo; compra/cargo/entrega sin duplicados; rollback o recuperación conforme a coordinación acordada, sin presuponer atomicidad global. |
| Rewards | Condiciones, vigencia, límites, emisor, compatibilidad y repetibilidad configurados; actividad no recompensada dos veces; dominios propietarios y resumen coherente; separación de puntuación provisional y XP consolidada. |
| Concurrencia SQLite (D-19) | `TransactionTestCase`; escrituras concurrentes; mismo `operation_key`; rollback/timeout; al menos una ejecución específica SQLite file-backed. Pendiente de implementación. |
| Transversal PR07 | Tests de modelos, vistas y permisos: accesos autorizados, redirección o denegación según corresponda (200/302/403), detalle inexistente controlado (404), formularios válidos e inválidos y protección del CRUD por propietario. La autenticación concreta sigue pendiente de aclaración. |

## 10. Definition of Done

Como criterio operativo propuesto, una funcionalidad se considera terminada cuando:

- Cumple el requisito y las reglas críticas se validan en servidor.
- Tiene tests y respeta las fronteras de dominio.
- Está integrada y otro integrante puede comprenderla.
- Está documentada si introduce decisiones importantes.
- El PR tiene una responsabilidad clara.
- Los nuevos modelos parten de ERD V2 y diccionario revisados del dominio, con
  incompatibilidades V1 resueltas formalmente y contratos mínimos acordados, con
  cardinalidades y reglas `on_delete`; Admin, interfaz y permisos se verifican cuando correspondan.
- La aportación y su validación son identificables mediante commits y PR.

Estos criterios recogen la orientación de entrega integrada de DAR3 y añaden la
organización interna propuesta y los criterios complementarios de PR07; no
constituyen una cita textual de DAR3.

## 11. Git y mantenimiento del plan

Se mantienen las convenciones registradas: `main` estable, `develop` para
integración y ramas `feature/*`, `fix/*` y `docs/*`. Para integrar se requiere PR,
como práctica de revisión prevista en DAR3 y en esta guía operativa.

PR07 exige el uso de Git y aportaciones identificables mediante commits de cada
integrante (páginas 4-11 y 17). El Equipo 5 mantiene además su estrategia de
integración mediante Pull Requests. Las contribuciones individuales deberán
quedar trazables mediante commits y, cuando corresponda, mediante los PR
asociados. Se conservará la trazabilidad de
los PR originales cuando la integración use squash; este plan no cambia el
método de integración registrado. Los entregables diarios quedan sujetos a la
aclaración del calendario, sin eliminar la obligación de evidenciar el trabajo.

Según el antecedente PR07 documentado, la entrega contempla pruebas, análisis
de tres bugs complejos, PR de release, etiqueta `v1.0.0`, instrucciones de
despliegue local y presentación. Se prepararán en la fase de entrega
que corresponda; este PR no crea esos archivos ni realiza una release.

El plan debe actualizarse cuando se valide el reparto, cambie un hito, llegue
información del profesor, se acuerden contratos, cambien fronteras o se resuelvan
dependencias. Las decisiones definitivas importantes deberán registrarse también
en [decisions.md](decisions.md) cuando se aprueben; este plan no las confirma.
