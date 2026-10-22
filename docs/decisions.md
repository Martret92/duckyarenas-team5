# Registro de decisiones

Este es el registro principal de acuerdos y decisiones técnicas. Las propuestas
pendientes se mantienen separadas de las decisiones confirmadas.

## Lectura del registro y baseline DOC-1 · 18/10/2026

Develop en `b42cb5f` incluye S1/S1.1, Día 4/5 y S2-A–S7-A (PR #22–#32).
El [estado vigente de arquitectura](architecture.md#21-estado-vigente-de-implementación--doc-1)
traza implementación, contratos y PR. Los apartados de bootstrap, V2 provisional,
Día 4/5 y decisiones S1–S7-A conservan su redacción de origen: «futuro», «para
revisión» o «pendiente» describen el incremento en que se registraron, no deshacen
su integración posterior. En particular, D-12 documenta perfiles mínimos históricos;
PR #24 los amplió y S7-A añadió StatAllocationEvent. La previsión D-19 de tests
file-backed ya tiene cobertura local S2-A/S3/S7-A, sin extenderla a Rewards global.
No se modifican decisiones confirmadas ni se atribuye aprobación externa.

## Requisitos de referencia: DAR3

DAR3, sección 9 (páginas 48-50), asigna al Equipo 5 Ecomotor y evolución, avatar e
inventario, Ecommerce y DuckyBank, y el servicio común de recompensas. No asigna
individualmente estas partes a los integrantes.

La sección 10 (páginas 50-53) requiere acordar el contrato de recompensas entre
el Equipo 5 y el Equipo 0; no implica que ese contrato esté ya decidido.
Fuente: `DAR3_ (1).pdf`, consultado y no copiado al repositorio. El alcance y los
requisitos se resumen en [architecture.md](architecture.md).

`DuckyEcomotor.pdf` y `DAR_formulas.pdf` son fuentes funcionales posteriores
facilitadas por Óscar: prevalecen donde actualizan explícitamente especificaciones
anteriores. Sus pasajes pertinentes se han consultado directamente, junto con
DAR3, PR07, DuckyClash, Training y Escape. La procedencia y las discrepancias se mantienen en
[architecture.md](architecture.md).
Estos requisitos trasladados se distinguen de propuestas internas y acuerdos
aprobados, según los criterios de fuentes de arquitectura (sección 1).

## Decisiones confirmadas

`Vigente` indica que la decisión sigue aplicándose. `Cumplida` identifica una
decisión limitada a una fase ya ejecutada. `Superada` se reserva para decisiones
reemplazadas claramente por otras; ninguna se clasifica así actualmente.

| ID | Decisión | Origen | Estado |
| --- | --- | --- | --- |
| D-01 | Trabajar inicialmente en repositorios independientes por equipo y posteriormente integrar en el repositorio común del Equipo 0. | Profesor / clase | Vigente |
| D-02 | `main` representa estados estables. | Equipo 5 | Vigente |
| D-03 | `develop` es la rama de integración del Equipo 5. | Equipo 5 | Vigente |
| D-04 | Usar ramas `feature/*`, `fix/*` y `docs/*` para el trabajo. | Equipo 5 | Vigente |
| D-05 | El Equipo 0 es responsable del User, la autenticación y la integración global; el Equipo 5 no creará un User propio. | Profesor / clase | Vigente |
| D-06 | Limitar el setup inicial a la configuración documental del repositorio, sin implementar Django ni añadir dependencias en aquella fase. | Equipo 5 | Cumplida |
| D-07 | No fijar como definitivos los modelos de dominio, contratos de recompensas, reglas de XP o arquitectura funcional que dependan de decisiones todavía pendientes del profesor o del equipo. | Equipo 5 | Vigente |
| D-08 | Crear el bootstrap Django en `config` y la app provisional `ecomotor`, con Django 5.2.17, sin lógica de dominio. | Equipo 5 | Cumplida |
| D-09 | Crear la app Django `users` y utilizar el User estándar de Django, sin crear un User personalizado ni heredar de `AbstractUser`. | Profesor / clase | Vigente |
| D-10 | El Equipo 5 no implementará login ni autenticación en su repositorio temporal; la integración global de usuarios y autenticación se realizará posteriormente en el proyecto común. | Profesor / clase | Vigente |
| D-11 | Centralizar en `users/models.py` los perfiles específicos del Equipo 5, inicialmente `UserProfileEcomotor` y `UserProfileBank`, relacionados uno a uno con el usuario. | Profesor / clase | Vigente |
| D-12 | En la implementación inicial, los perfiles contienen únicamente la relación con el usuario, además del identificador automático. Se utiliza `settings.AUTH_USER_MODEL` con `on_delete=models.CASCADE` y no se añaden todavía campos de negocio ni signals de creación automática. | Implementación del Equipo 5 | Vigente |

D-06 y D-08 corresponden al setup y al bootstrap ya ejecutados. D-07 permite
avanzar sin dar por definitivos los aspectos sujetos a decisiones pendientes.
D-09 a D-11 resuelven la estructura base de
usuarios y perfiles, sin decidir las reglas de negocio. Los detalles técnicos
de D-12 son elecciones de implementación del Equipo 5, no acuerdos atribuidos
al profesor. La integración global sigue a cargo del profesor y del Equipo 0.

## Condicionantes de referencia: PR07

Fuente directa: Documento PR07 · Ciclo de vida de una aplicación web, facilitado
por el profesor (17 páginas), no copiado al repositorio.
PR07 complementa DAR3 en estructura, proceso, entregables y evaluación. Los
siguientes puntos son requisitos o criterios de esa fuente, no decisiones
internas del Equipo 5:

- Apps bajo `apps/`; ERD y diccionario de datos antes del ORM, con cardinalidades
  y reglas `on_delete` documentadas (páginas 4-5).
- Modelos y migraciones, Admin, URLs, vistas, templates, listados, detalles,
  formularios y CRUD de al menos dos entidades principales (páginas 6-9).
- Permisos, seguridad, testing y evidencias de trabajo mediante Git y PR;
  contribuciones identificables de cada integrante (páginas 10-11 y 17).
- El plan detallado pide `AbstractUser`, `AUTH_USER_MODEL`, registro, login y
  logout (página 5), en conflicto con D-09 y D-10. Su aplicación requiere
  aclaración del profesor y validación del alcance del CRUD. Daily del 06/10/2026:
  se aclaró que el calendario de quince días es una guía de trabajo; se conservan
  sus entregables y criterios de evaluación.

## Decisión transversal provisional ante PR07

| ID | Decisión | Origen | Estado |
| --- | --- | --- | --- |
| D-17 | Mientras no se aclare con el profesor la contradicción de PR07 sobre usuarios y autenticación, mantener D-09 y D-10: User estándar, sin migrar a CustomUser ni implementar autenticación local; no cambiar `AUTH_USER_MODEL` ni migraciones por ese motivo. Cualquier cambio posterior deberá registrarse como nueva decisión. | Equipo 5 | Vigente |

D-17 es provisional hasta recibir esa aclaración. No declara resuelto el conflicto
ni sustituye los acuerdos de clase anteriores.

## Decisión técnica de estructura e identidad de las apps

| ID | Decisión | Origen | Estado |
| --- | --- | --- | --- |
| D-18 | Alojar físicamente las aplicaciones del Equipo 5 bajo `apps/`, con rutas Python canónicas `apps.ecomotor` y `apps.users`. Conservar expresamente los labels Django `ecomotor` y `users` para preservar la identidad de las aplicaciones y su historial de migraciones. Incorporar `apps/` al path según la adaptación de PR07. | Equipo 5 | Vigente |

`INSTALLED_APPS` utiliza `apps.ecomotor.apps.EcomotorConfig` y
`apps.users.apps.UsersConfig`; los `AppConfig` declaran los nombres canónicos y
los labels anteriores. `settings.py` conserva
`sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))`.
Para imports absolutos, las rutas canónicas son `apps.ecomotor` y `apps.users`.
No deben mezclarse imports absolutos `users...` con `apps.users...`, ni
`ecomotor...` con `apps.ecomotor...`. Así se evita cargar una misma app con dos
identidades Python. Los imports relativos internos de una app, por ejemplo
`from .models import ...`, siguen siendo válidos y no deben sustituirse
innecesariamente.
D-18 cambia únicamente la ubicación física de aquella app: el archivo
correspondiente a D-11 se encuentra ahora en `apps/users/models.py`, sin alterar
la decisión funcional registrada en D-11.
Esta decisión no cambia modelos, contenido de migraciones, User ni autenticación;
D-17 sigue vigente. La parte estructural y técnica aplicable del Día 1 está
validada. El [ERD y diccionario de Parte A](erd/ecomotor.md) ya documenta V2
provisional aceptada internamente y conserva V1 como antecedente. Queda pendiente
el ERD consolidado del Equipo 5 con los demás dominios, antes del ORM definitivo.

## D-19 · Política transversal de concurrencia SQLite para V1

| ID | Decisión | Origen | Estado |
| --- | --- | --- | --- |
| D-19 | Mientras la V1 use SQLite, adoptar globalmente `transaction_mode = "IMMEDIATE"` y un timeout explícito de 5 segundos. Las operaciones críticas de escritura deben abrir `transaction.atomic()` antes de leer el estado mutable que van a decidir o modificar. | Equipo 5 | Vigente |

`BEGIN IMMEDIATE` es la garantía efectiva utilizada en SQLite V1 para serializar
escritores. SQLite serializa escritores para toda la base de datos, no mediante
locks por fila. `select_for_update()` no proporciona row locking en este backend
y se considera un no-op; puede mantenerse en servicios para expresar intención
de bloqueo y facilitar una futura migración a un backend con row locking.

Las transacciones deben ser cortas y no contener HTTP, I/O externo, esperas ni
trabajo lento. No se adopta `ATOMIC_REQUESTS` como solución de concurrencia.
Si el lock no se obtiene dentro del timeout, la operación debe fallar y hacer
rollback. Un retry seguro debe comenzar una nueva transacción; cuando la operación
sea idempotente, debe reutilizar la misma `operation_key`.

Las constraints de base de datos y la idempotencia persistente siguen siendo
defensas obligatorias: `BEGIN IMMEDIATE` no las sustituye. Los tests críticos de
concurrencia deberán usar `TransactionTestCase` y contar con al menos una ejecución
específica contra SQLite respaldada por archivo (file-backed), sin depender
únicamente de una base SQLite de test en memoria. Estos tests siguen pendientes
de implementación.

D-19 no modifica D-17 ni D-18, no decide contratos A/B/C ni el contrato de Rewards.
Tampoco garantiza por sí sola atomicidad de una operación repartida entre varias
transacciones o servicios ni resuelve las fronteras transaccionales entre Rewards,
A, B y C, que siguen pendientes.

## Aceptación interna de Parte A

Parte A ha aceptado internamente su arquitectura V1, identificada como A-01…A-16.
Los antecedentes del ERD y diccionario V1 se conservan en [erd/ecomotor.md](erd/ecomotor.md), como
antecedente interno aceptado. A-01…A-16 se conservan como acuerdos históricos de
V1; su aceptación no se extiende automáticamente a los puntos incompatibles con
V2. El diseño V2 provisional de Parte A ya está documentado; queda pendiente
la integración del ERD consolidado con los demás dominios. Los modelos Django
y migraciones definitivos todavía no están aprobados globalmente. Los identificadores V2-A1…V2-A29 distinguen la
aceptación interna condicionada de Parte A de las decisiones D vigentes.
La aceptación interna no aprueba contratos compartidos con B/C o Rewards, que
siguen pendientes de validación conjunta. D-20 registra un reparto posterior a
D-13; no valida retrospectivamente D-14…D-16.

## Hito documental: arquitectura candidata V2

La arquitectura candidata V2 está elaborada y revisada internamente en
[architecture.md](architecture.md), incorporada mediante el commit local
`52c3865`. Este hito documental no constituye una nueva decisión arquitectónica
aprobada ni recibió un identificador D en aquel hito. La candidata no está
aprobada globalmente
por Óscar y los demás equipos; las decisiones compartidas requieren validación
conjunta. El diseño V2 provisional revisa expresamente el antecedente V1; sus condiciones
deben validarse antes del ORM afectado, sin cambiar decisiones D vigentes.

Como antecedente verificable, PR #15 integró la candidata mediante el squash
`256dd9e` (`Docs/team5 architecture candidate (#15)`). El commit `ca8d182`
actualizó previamente el registro de decisiones para la arquitectura V2.
Estos hitos documentales no equivalen a aprobación global.

## D-20 y D-21 · Acuerdos internos del 08/10/2026

Identificadores libres en el registro anterior. Fuente: acuerdos internos
comunicados expresamente por el Equipo 5 para esta consolidación; no se atribuyen
a una aprobación de Óscar. Jaime, Henry y Fernando aceptaron D-20 y D-21;
esta ratificación interna no aprueba otros contratos ni su integración física.

| ID | Acuerdo | Origen | Estado |
| --- | --- | --- | --- |
| D-20 | Reparto principal: Jaime, Parte A (Ecomotor, Rewards, XP, evolución y estadísticas); Henry, Parte B (Duckies, avatar, inventario y equipamiento); Fernando, Parte C (DukiBank y DukiShop). | Equipo 5, 08/10/2026 | Vigente como acuerdo interno |
| D-21 | Organización objetivo en cuatro apps de dominio: `apps.ecomotor`, `apps.duckies`, `apps.bank` y `apps.shop`, conservando `apps.users`. Rewards se coordina desde Ecomotor, sin app independiente obligatoria. | Equipo 5, 08/10/2026 | Vigente como acuerdo interno; implementación posterior |

D-20 reemplaza el reparto propuesto en D-13 para la planificación actual.
La redacción histórica de D-13 se conserva debajo: nunca fue una decisión
confirmada. D-21 amplía la organización objetivo, sin cambiar D-18, las rutas
y labels existentes, la ubicación de perfiles D-11 ni modelos o migraciones.
No afirma que las tres apps nuevas ya estén creadas ni valida el diseño de la
rama de Parte C. D-17 y D-19 continúan íntegramente vigentes.
En la mini daily del 06/10/2026 se propuso esta organización y quedó pendiente
su revisión. Daily del 08/10/2026: Óscar indicó una revisión por encima del documento,
con examen detallado pendiente. Los límites de apps y contratos requieren todavía
validación con Óscar/Core, Henry, Fernando y los equipos implicados.

## Propuestas y antecedente de reparto

| ID | Propuesta histórica | Origen | Estado en esta consolidación |
| --- | --- | --- | --- |
| D-13 | Establecer inicialmente a Jaime como responsable principal de Parte A (Ecomotor y evolución), Félix de Parte B (Avatar e inventario) y Henry de Parte C (Ecommerce y DuckyBank). | Propuesta interna anterior | Antecedente no confirmado; reparto posterior registrado en D-20 |
| D-14 | Mantener recompensas como responsabilidad compartida, con coordinación inicial desde A y operaciones de inventario y economía proporcionadas por B y C. | Propuesta interna | Validación técnica conjunta pendiente; la coordinación funcional se recoge en arquitectura |
| D-15 | Fronteras iniciales revisables: A propietaria de XP, épocas y evolución; B de catálogo, inventario y equipamiento; C de DuckyCoins, wallet, transacciones, tienda y compras; Rewards orquesta sin duplicar lógica. | Propuesta interna | Contratos y límites técnicos pendientes; D-20 no los aprueba automáticamente |
| D-16 | Datos ficticios/provisionales identificados y separados de la lógica, sin números mágicos ni presentación como oficiales; tests con datos propios. | Propuesta interna | Validación del Equipo 5 pendiente |

D-16 propone sustituir parámetros por datos oficiales sin cambiar la lógica.
Un cambio de regla funcional requiere revisar el diseño, no solo la configuración.

## Aclaraciones del 09/10 y propuesta Rewards v0

Las notas de la daily del 09/10/2026 se recogen en la matriz de
[arquitectura](architecture.md), distinguiendo aclaraciones del profesor,
respuestas parciales, propuestas de participantes y cuestiones pendientes.
No se registra aquí una aprobación global del ERD ni una respuesta que resuelva D-17.

La rectificación verbal sobre XP reservada a juegos y monedas externas queda
pendiente de alcance, vigencia y confirmación escrita; no autoriza eliminar o
recalcular progreso. Stats editables en Actual y posibles premios de cursos no
fijan presupuestos, límites ni parámetros oficiales.

[Rewards v0](contracts/rewards-v0.md) es una propuesta técnica aceptada
provisionalmente como base de trabajo, pendiente de validación conjunta A/B/C,
Core y juegos. Propone idempotencia de la recompensa completa y transacción
exterior compartida condicionada a la misma BD/conexión. No es una nueva decisión
D confirmada ni aprueba `RewardRule` como tabla, `RewardEvent` como ORM, nuevas
FKs o políticas `on_delete`. D-19 no resuelve por sí sola ese contrato.

## Aceptación interna provisional de Parte A V2

Se registran únicamente V2-A1…V2-A29 comunicadas y aceptadas internamente por
Parte A. No son decisiones D nuevas, aprobación de Óscar/Core/B/C ni validación
automática de D-14…D-16. El [ERD V2 provisional](erd/ecomotor.md) concreta ocho entidades
y conserva A-01…A-16 como antecedentes. La implementación actual D-12 permanece
intacta; el diseño de campos futuros no cambia retroactivamente su estado.

La revisión documental directa y las aclaraciones del 09/10 se recogen en
arquitectura; no cambian silenciosamente las condiciones físicas de V2-A1…V2-A29.
RewardEvent/RewardRule siguen conceptuales. El contrato Rewards v0 concentra
su semántica compartida para evitar duplicarla en el ERD.

| ID | Decisión aceptada internamente por Parte A | Condiciones y alcance |
| --- | --- | --- |
| V2-A1 | EvolutionStage y siete etapas | Catálogo interno; contenido y parámetros oficiales pendientes. |
| V2-A2 | Estadísticas RPG persistentes en CharacterStats | Valores iniciales, fórmulas y efectos pendientes. |
| V2-A3 | Simplificación inicial de especializaciones | Revisada parcialmente por V2-A25: se recupera progreso de dominio; sin rank en el mínimo. |
| V2-A4 | Idempotencia de la concesión completa de recompensa | Contrato global, coordinador y efectos multidominio pendientes; XPEvent solo cubre XP histórica. |
| V2-A5 | EvolutionEvent causado directamente por XPEvent | Una concesión puede causar varias evoluciones. |
| V2-A6 | Campos del perfil y estadísticas separadas | Diseño documental futuro; D-12 describe la implementación actual. |
| V2-A7 | current_level y LevelThreshold persistentes | Niveles independientes de etapas; sin valores oficiales inventados. |
| V2-A8 | Puntos por nivel configurables y asignación transaccional | Reglas de asignación y límites físicos pendientes de concreción. |
| V2-A9 | Catálogo EvolutionStage y condiciones de progresión | Evolución automática; no implica equipamiento automático. |
| V2-A10 | Definición e integridad de XPEvent | Cantidad positiva, snapshots, clave por perfil y fecha. |
| V2-A11 | Definición e integridad de EvolutionEvent | Perfil, etapa, evento XP causal y fecha; integridad entre tablas por servicio. |
| V2-A12 | Concesión transaccional de XP y evolución | Actualiza total, nivel, puntos, etapa y eventos; atomicidad local, no global. |
| V2-A13 | Inicialización explícita e idempotente | Transaccional, sin signals ni eventos ficticios. |
| V2-A14 | Constraints, validaciones de servicio y migraciones seguras | Las reglas entre tablas no se suponen CheckConstraint; M-01 fail-closed. |
| V2-A15 | RewardRule conceptual | Condicionada al diseño compartido de Rewards; sin campos físicos aprobados. |
| V2-A16 | RewardEvent conceptual | Condicionada a contratos compartidos; sin FKs definitivas. |
| V2-A17 | Estadísticas persistentes y efectivas separadas | Efectos de objetos y cálculo efectivo pendientes; no sobrescribir base por presentación. |
| V2-A18 | Límites de estadísticas por especialización | Representación física definitiva pendiente; no adoptar valores de ejemplo. |
| V2-A19 | Selección inicial de especialización en Actual | Obligatoriedad pendiente; cambio posterior fuera del mínimo. |
| V2-A20 | Reglas de LevelThreshold y cambios de configuración | Niveles positivos consecutivos; primer nivel configurado XP 0; stat_points_awarded >= 0. Política administrativa y tratamiento del progreso existente pendientes. |
| V2-A21 | Siete etapas, códigos estables y umbrales | Exactamente siete etapas, ordinales consecutivos 1–7; Prehistoria en XP 0; umbrales estrictamente crecientes y configurables. |
| V2-A22 | Integridad e inmutabilidad de XPEvent | UNIQUE(profile, operation_key), amount > 0 y xp_after = xp_before + amount. |
| V2-A23 | Integridad del historial EvolutionEvent | UNIQUE(profile, stage) y mismo perfil que el XPEvent causal. |
| V2-A24 | Catálogo estable Specialization | Identificador, código estable y nombre; códigos definitivos Sistemas/Data pendientes. |
| V2-A25 | UserSpecializationProgress mínimo | Revisa V2-A3: XP de dominio no negativa, única por perfil/especialización, sin rank. |
| V2-A26 | XP de dominio trazable e idempotente | Condicionada al contrato Rewards; no se aprueba otra entidad física de eventos. |
| V2-A27 | Desbloqueos históricos coordinados con Inventory | Condicionada a aclarar vestimenta; sin equipamiento ni adquisición individual impuestos. |
| V2-A28 | Conservación del progreso ante cambios administrativos | Parcialmente condicionada: política de ajustes/reconciliación pendiente, sin pérdida silenciosa. |
| V2-A29 | Core y migraciones legacy fail-closed | Parcialmente condicionada a conservación e integración con Core; no cambiar AUTH_USER_MODEL. |

## Daily del 13/10/2026 · evidencias verificadas y alcance

Procedencia: acta de la reunión del 13/10/2026
y aclaraciones verificadas comunicadas por Jaime. Se registran únicamente los
puntos contrastados de conformidad, controlador antiguo, autonomía, LMS/Bank y
recursos gráficos; las demás notas del acta no se adoptan aquí como acuerdos.
El contexto de LMS/Bank y los recursos gráficos se desarrollan en
[architecture.md](architecture.md).

Óscar manifestó haber leído el documento enviado por Jaime y expresó conformidad
funcional general. El contexto permite relacionarlo con el criterio funcional
enviado el 07/10, pero no identificó oralmente su título o versión exacta.
No es aprobación detallada del ERD V2, la estructura física de D-21, Rewards v0,
modelos, migraciones ni las ocho interfaces propuestas por Henry, todavía
pendientes de consenso A/B/C.

El controlador antiguo sencillo descrito para incrementar DuckyCoins no es de
reutilización obligatoria ni debe esperarse para avanzar con los servicios.
La aclaración se limita a ese controlador: no declara desaparecidos todos los
componentes anteriores de recompensas, puntos o economía. Consultarlos puede ser
útil, pero siguen pendientes con Core y Fernando Wallet/saldo canónicos, identidad,
autorización, movimientos, idempotencia, concurrencia y contratos Rewards/Bank;
no se autoriza duplicar saldos.

Óscar dejó margen de implementación y pidió trasladarle las dudas. El equipo
puede continuar desarrollando dentro de sus responsabilidades, manteniendo la
validación de contratos compartidos y la reconciliación de migraciones antes de
integrar. D-17/D-19/D-20/D-21, V2-A1…V2-A29, M-01 y el estado candidato de
Rewards v0 permanecen vigentes, sin nueva decisión D ni aprobación global.

## Integración estructural de catálogos · Día 4-A

Se prepara para revisión hacia develop únicamente LevelThreshold, EvolutionStage
y Specialization, sus validadores explícitos y 36 tests recuperados del Día 4
(`c78be74258dbe1eff3f552edeb5a0727cc316d41`). DAR3 define progreso/evolución y el
modelo inicial de especializaciones; DuckyEcomotor concreta siete etapas y
configuración de umbrales. V2-A7/A20/A21/A24 son decisiones internas sobre los
catálogos: nivel positivo, ordinales únicos 1–7, códigos únicos y campos no vacíos;
consecutividad, primer umbral 0 y crecimiento estricto por validación completa.
La carga gradual sigue permitida, sin validación global automática en save().

No se fijan umbrales, puntos ni códigos oficiales, ni se cargan datos maestros.
No se incorporan perfiles, estadísticas, historiales, progreso por usuario,
Admin o servicios; S1/S1.1 permanece independiente del ORM. La identidad antigua
ecomotor.0001_initial de Fernando tiene otro contenido y debe reconciliarse con
su responsable antes de combinar implementaciones A/C; este incremento no la
modifica ni resuelve esa colisión. La autorización interna para preparar este PR
no es aprobación global: contratos A/B/C/Core/Rewards y conservación siguen abiertos.

## Integración estructural de progreso · Día 4-B

Se prepara para revisión hacia develop el resto estructural de Parte A, recuperado
sin rediseño de Día 4 (`c78be74258dbe1eff3f552edeb5a0727cc316d41`): ampliación de
UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent y
UserSpecializationProgress. Se preservan los catálogos de PR #23, UserProfileBank,
settings.AUTH_USER_MODEL y S1/S1.1. DAR3/DuckyEcomotor son referencias funcionales;
campos, relaciones y restricciones concretan acuerdos internos V2, no una aprobación
global del diseño físico ni parámetros oficiales.

users.0002 aplica M-01 como primera operación: ante perfiles Ecomotor legacy aborta
sin alterar esquema ni datos; usuarios sin ese perfil y perfiles Bank permiten
continuar. Nivel y etapa siguen siendo obligatorios sin defaults ficticios.
ecomotor.0002 depende de users.0002; 0003 y 0004 preservan esa dependencia. Las cuatro
migraciones son atómicas y explícitamente irreversibles, también con tablas vacías.
La estrategia de conservación/migración legacy sigue pendiente de Core.

Se mantienen unicidad de estadísticas por perfil, de XPEvent por perfil/operation_key,
de evolución por perfil/etapa y de progreso por perfil/especialización; XP y puntos
disponibles no negativos, importe XP positivo, snapshots coherentes, nivel positivo
y etapa/clave no vacías. CASCADE al perfil y al XPEvent causal es provisional;
etapas y especializaciones referenciadas usan PROTECT. La coincidencia de perfiles
entre EvolutionEvent y su causa exige un futuro servicio transaccional. El historial
es conceptualmente inmutable, sin protección física completa de modificación/borrado.

V2-A22/A23 mantienen idempotencia local de XP histórica, distinta de Rewards v0;
V2-A25/A26 mantienen XP de dominio independiente, default 0 al crear explícitamente
el progreso y sin rank, trazabilidad ni concesión implementadas. No hay señales,
inicialización, servicios XP/evolución/Rewards, asignación de puntos ni Admin.
Conservación, contratos A/B/C/Core/Rewards y reconciliación de la migración antigua
de Fernando siguen pendientes. Se preservan las aclaraciones recientes de Óscar;
esta aceptación interna para preparar el PR no autoriza su merge.

## Integración de Django Admin · Día 5

Sobre develop con S1/S1.1 y Día 4-A/B integrados, se prepara para revisión el Admin
original de Parte A (`fa6858f3ebde9142778f09926ceb99b0859e69c0`) y sus 20 tests.
DAR3 aporta los requisitos funcionales de progresión; la siguiente política de
administración es un acuerdo interno, no un requisito atribuido al profesor.

Solo superusuarios activos pueden acceder a los ocho modelos de Parte A, aunque
otros usuarios staff tengan permisos ordinarios. LevelThreshold, EvolutionStage
y Specialization permiten carga gradual y modificación únicamente sin perfiles
Ecomotor; al existir cualquiera quedan de consulta. Se revalida al guardar dentro
de transaction.atomic(), bajo SQLite IMMEDIATE de D-19. Siempre se prohíben borrados
y acciones masivas. UserProfileEcomotor, CharacterStats, XPEvent, EvolutionEvent y
UserSpecializationProgress son exclusivamente de lectura, incluidos POST directos.
No se registra UserProfileBank ni se altera User o la autenticación/Admin de Core.

Se recuperan únicamente Admin y tests, sin modificar modelos ni migraciones.
Estas barreras pertenecen al Admin; no garantizan inmutabilidad universal del ORM
ni sustituyen la política de concurrencia de futuros servicios. Conservación,
tratamiento legacy, contratos Core/A/B/C/Rewards y servicios de inicialización,
XP, evolución y puntos siguen pendientes. No se concede XP ni se crean perfiles
desde el Admin. Se preservan los acuerdos provisionales y aclaraciones recientes;
no hay aprobación global ni autorización de merge. PR #21 se trata por separado.

## Contraste de acuerdos internos · 14–16/10/2026

Fuente: resumen verificado de la coordinación interna del Equipo 5 comunicado
el 16/10/2026. Se distingue la aceptación organizativa de la conformidad conceptual
y de los contratos físicos todavía pendientes; no se atribuye aprobación a Óscar/Core.
Por coordinación, esta PR documental no espera nuevas revisiones formales de Henry
y Fernando; esto no les atribuye una revisión personal de la PR en GitHub.

| Referencia | Grado de acuerdo | Pendiente |
| --- | --- | --- |
| D-20/D-21 | Ratificados por Jaime, Henry y Fernando: reparto y cuatro apps objetivo, con Rewards en Ecomotor. | Implementación física, interfaces e integración; no se reabre el reparto. |
| R-01 | Mixto: se debatió EvolutionItem–EvolutionStage y la adquisición. Jaime recordó entrega y equipamiento automáticos; no consta aceptación inequívoca de Henry del autoequipamiento. El 15–16/10 ambos acordaron proponer a Óscar apariencias completas seleccionables de cualquier época desbloqueada. | Resolver adquisición, entrega y equipamiento sin adoptar aún una alternativa; contrastar nueve épocas de DAR3 y siete etapas V2 provisionales. |
| R-05 | Henry expresó conformidad conceptual el 14/10 con la propuesta de Jaime de ItemGrant para entregas y deduplicación. | Fernando, contrato, esquema físico, ORM y migraciones sin ratificar. |
| R-08 | Henry expresó conformidad conceptual el 14/10 con la propuesta de Jaime de RewardEvent para trazabilidad e idempotencia de toda la recompensa. | Campos, reglas, migraciones y APIs de Core/juegos sin ratificar globalmente. |
| R-12 | Jaime y Henry acordaron el 13/10 avanzar con el inicializador local de Ecomotor sin esperar la integración global. | Core conserva alta global de User, orquestación final de Ducky/Wallet, legacy y autoridad externa. |
| Bank/Shop | Fernando aceptó revisar su reubicación respecto a Ecomotor; D-21 ya fija la organización objetivo. | Traslado físico y reconciliación de migraciones A/C; el conflicto no está resuelto. |
| ERD global y H01–H08 | Base documental interna aceptada para trabajar. | Sin aprobación expresa y completa de detalles físicos, APIs ni transacciones por los tres responsables. |

S2-A1/S2-A2 permanecen sin cambios: inicialización local atómica e idempotente
de perfil y stats, sin signals ni nuevo User; seis stats iniciales y puntos desde
configuración confiable, sin defaults inventados. Este contraste no incorpora
las decisiones o implementaciones de las features a develop ni modifica D-17,
D-19, V2-A1…V2-A29 o Rewards v0, que conserva su estado candidato.

## S1 · Cálculos puros de progresión — Aceptación interna provisional

Contrato recuperado de `feature/part-a-progression-s1:docs/decisions.md`
(`dc391bb`), contrastado con [progression.py](../apps/ecomotor/progression.py).
S1/S1.1 ya está integrado en develop mediante PR #22, con 28 tests. Mantiene
V2-A12/A20/A21 y su aceptación interna provisional, sin aprobación global de Core.

- `resolve_level(xp_total, levels)` devuelve el mayor nivel cuyo umbral se alcanza.
- `resolve_stage(xp_total, stages, *, ordered_stage_codes)` devuelve la etapa
  alcanzada según XP y una correspondencia explícita de siete códigos, en el orden
  funcional provisional Prehistoria, Griega, Romana, Renacentista, Contemporánea,
  Siglo XX y Actual; no incorpora códigos técnicos oficiales.
- `calculate_progression(xp_before, xp_after, levels, stages, *, ordered_stage_codes)`
  recibe totales históricos y devuelve estados inicial/final, todos los niveles y
  etapas nuevos cruzados en orden ascendente y la suma de puntos de esos niveles.
  No cuenta la etapa ya alcanzada ni concede puntos iniciales del nivel 1.

`LevelDefinition(level, minimum_xp, stat_points_awarded)`,
`StageDefinition(code, ordinal, minimum_xp)` y `ProgressionResult` son dataclasses
inmutables (`frozen=True`). El resultado contiene `xp_before`, `xp_after`,
`level_before`, `level_after`, `stage_before_code`, `stage_after_code`,
`crossed_levels`, `crossed_stages` y `total_stat_points_awarded`; las transiciones
son tuplas de definiciones. Las colecciones recibidas se copian y ordenan sin
mutarlas ni conservar referencias a listas mutables.

`InvalidXPError` e `InvalidCatalogError` derivan de ValueError. Se exige XP entera
no negativa, excluyendo booleanos y conversiones implícitas, y progresión no
decreciente. Igualar un umbral lo alcanza; con XP anterior y final iguales no hay
transiciones ni puntos. Los niveles son consecutivos desde 1, con primer umbral 0;
los puntos son enteros no negativos. Las etapas son exactamente siete, ordinales
únicos consecutivos 1–7, códigos únicos no vacíos de hasta 32 caracteres, coincidentes
con la correspondencia recibida, y primera etapa a 0 XP. Ambos catálogos exigen
umbrales enteros no negativos y estrictamente crecientes. La carga gradual del
Admin permanece separada de esta validación funcional completa.

S1 solo calcula, sin Django/ORM ni persistencia. No concede recompensas ni verifica
idempotencia, usuarios, permisos o contratos Rewards/Bank. S2 inicializará perfil y
stats con configuración confiable; S3 deberá cargar configuración coherente,
utilizar S1 y persistir la concesión transaccional y todas las transiciones.
S1 no limita los enteros por almacenamiento: su adaptación a campos persistentes
corresponde al futuro S3. La consistencia/concurrencia de S3 sigue pendiente de
diseño bajo D-19. No se fijan límites de juego, umbrales, puntos ni códigos oficiales,
ni se aprueban cambios administrativos de catálogos o contratos Core/A/B/C/Rewards.

## S2-A · Inicialización local — Decisión interna aprobada de Parte A

Jaime aprueba la inicialización local conforme a V2-A13, D-19 y R-12, sin nueva
decisión D ni aprobación global de Óscar/Core. El contrato
[ecomotor-initialization-v1](contracts/ecomotor-initialization-v1.md) fija
`ensure_ecomotor_initialized(user)`: User existente, creación atómica de perfil y
CharacterStats, XP 0, nivel 1 y Prehistoria desde catálogos completos validados,
sin especialización activa. Los puntos iniciales son stat_points_awarded del nivel 1.
Seis atributos y correspondencia funcional de códigos proceden de configuración
interna inmutable; permanece ausente hasta disponer de valores autorizados.

Un estado completo se devuelve sin reset ni validación de la configuración inicial
actual; un perfil parcial/estructuralmente inválido se rechaza sin reparación.
No se crean User, eventos, progresos de especialización ni efectos económicos.
SQLite IMMEDIATE serializa escritores antes de leer, con atomic(), constraints,
timeout 5 y rollback; errores de BD se comunican, no se disfrazan de éxito.
M-01, conservación legacy, alta global Core y contratos Rewards siguen pendientes.

## S3 V1 · Concesión de XP histórica — Decisión interna aprobada de Parte A

Jaime aprueba `grant_historical_xp(profile, amount, operation_key)` bajo
V2-A12/A22/A23, D-19 y el [contrato S2-A](contracts/ecomotor-initialization-v1.md).
El [contrato S3 V1](contracts/ecomotor-xp-v1.md) concreta cálculo exclusivo mediante
S1, validación de catálogos/correspondencia interna, snapshots XP, un XPEvent y
todas las evoluciones cruzadas, sumando solo puntos de nuevos niveles. Requiere
perfil con estadísticas; no inicializa ni repara. Comprueba coherencia actual y
límites técnicos antes de persistir dentro de atomic()/SQLite IMMEDIATE.

Un replay recupera snapshots y evoluciones persistidos sin catálogos actuales ni
nuevas escrituras. Niveles, códigos históricos de etapa y puntos no almacenados
se devuelven como None, sin inventar una reconstrucción. Los IDs de etapas y eventos
sí son recuperables; no se confunden con códigos históricos ni progreso actual.
Misma clave/cantidad diferente es conflicto explícito. Idempotencia local de XP,
no global de Rewards. Configuración autorizada, conservación, cambios históricos
de catálogo V2-A28 y contratos Core/A/B/C/Rewards permanecen pendientes.
Estas son decisiones internas aprobadas, no nuevos requisitos específicos de
DAR3 ni aprobación global de Óscar/Core; sin cambios de modelos ni migraciones.

## S4-A · Consultas locales V1 — Decisión interna aprobada de Parte A

Jaime aprueba [S4-A](contracts/ecomotor-progress-queries-v1.md):
get_progress_overview(profile) y list_progress_history(profile, *, limit=50,
before_id=None), exclusivamente internas y de lectura sobre estado persistido.
El overview básico no requiere configuración inicial; niveles y etapas proyectan
independientemente CALCULABLE, COMPLETED o UNAVAILABLE tras validar catálogos y
coherencia actual. Etapas necesitan solo la correspondencia interna confiable.

El historial pagina por PK descendente, máximo técnico 100, y agrupa evoluciones
por causa con PK ascendente. No reconstruye niveles/puntos ni códigos históricos
de etapas mediante catálogos actuales. Rechaza causalidad incompatible sin corregir.
Resultados frozen y errores diferenciados de perfil, estructura, parámetros y BD.
No hay atomic(), bloqueos ni escrituras; esta V1 no promete un snapshot único
entre lecturas concurrentes. No inicializa ni calcula premios y no sustituye las
vistas autenticadas/interfaz/CRUD pendientes de PR07. Convenciones técnicas internas,
no parámetros oficiales nuevos de DAR3 ni aprobación global de Óscar/Core/Rewards.

## S5-A · Vista web personal V1 — Decisión interna aprobada de Parte A

Jaime aprueba el [contrato local S5-A](contracts/ecomotor-progress-web-v1.md):
página GET/HEAD autenticada, identidad solo desde request.user y consultas S4-A
sin escrituras. Overview y diez concesiones recientes, objetivos independientes
CALCULABLE/COMPLETED/UNAVAILABLE e historial limitado a snapshots/IDs persistidos.
Ausencia de perfil produce 404; estado inconsistente 409 y fallo de BD 503,
siempre genéricos. Estas convenciones HTTP son internas, no requisitos DAR3.
Namespace ecomotor, sin montaje global ni nueva autenticación. No inicializa,
concede XP, reconstruye historia ni promete snapshot concurrente único.
Core, configuración oficial, contratos compartidos y CRUD PR07 siguen pendientes;
no constituye aprobación global de Óscar/Core.

## S6-A · Configuración y diagnóstico — Decisión interna aprobada de Parte A

Jaime aprueba [S6-A](contracts/ecomotor-configuration-v1.md): JSON interno local
de carga explícita, sin activación en imports, arranque, AppConfig.ready o comando.
INITIAL_CONFIGURATION sigue inicialmente None; el cargador devuelve un candidato
inmutable sin instalarlo. Rangos técnicos no equivalen a valores funcionales DAR3.
Diagnóstico de configuración/catálogos exclusivamente de lectura con cinco estados
y precedencia documentada; TECHNICALLY_READY no aprueba producción. El comando
distingue diagnóstico no preparado de fallo operativo. No altera S2-A/S3 ni S4-A/S5-A.
Instalación futura del servidor, parámetros oficiales, Core, conservación, Rewards
y cambios históricos V2-A28 siguen pendientes, sin aprobación global atribuida.

## S7-A · Asignación de puntos V1 — Decisión interna aprobada de Parte A

Jaime aprueba [S7-A](contracts/ecomotor-stat-allocation-v1.md): gasto 1:1 en un
atributo base, solo en Actual derivada por S1 y coherente con XP/etapa persistidas.
Catálogo/códigos confiables, sin validar niveles o stats iniciales. Nuevo historial
StatAllocationEvent con snapshots y clave única por perfil. Replay histórico validado
antes de exigir configuración/elegibilidad nueva, sin reinterpretación ni escritura.
D-19 serializa con S3; overflow/inconsistencia no reparan. 0005 aditiva protegida
y Admin solo lectura. CASCADE provisional y conservación Core/V2-A28 pendientes.
Decisión interna, no aprobación técnica de DAR3, profesor, Core ni Rewards.

## S8-A · Interfaz web de asignación — Aprobada y pausada

Jaime aprueba internamente la arquitectura web S8-A y pausa su implementación
por prioridad documental. **No está implementada ni integrada** en `b42cb5f`.
Alcance acordado: interfaz GET/POST para asignación de puntos, utilizando
exclusivamente [S7-A](contracts/ecomotor-stat-allocation-v1.md), autenticación
Django existente, protección CSRF, identidad del perfil desde `request.user`
e idempotencia. El adaptador no escribirá directamente stats o eventos ni
creará un User o autenticación paralela. Esta nota no añade endpoints, reglas,
valores ni un nuevo contrato global. No cambia decisiones S1–S7-A ni aprueba
integración con Core, Rewards, Henry o Fernando. DOC-1 no implementa S8-A;
DOC-2 y DOC-3 quedan fuera de este PR.

## DOC-2 · Contraste de fuentes funcionales y contratos · 18/10/2026

Base develop `33b4e87`, tras PR #33. La [matriz de acuerdos y conflictos](contracts/integracion-equipo5-v0.md#0-matriz-de-procedencia-y-acuerdos--doc-2)
consolida E5-01…E5-05, respuestas de coordinación 15–16/10, catálogo y propuestas
de balanceo/kit. Registra fuente, fecha, categoría y responsable sin copiar los
originales ni convertir sus rótulos de cierre en aprobación externa.

Las decisiones D-F/SHOP atribuidas al usuario en el catálogo son decisiones
funcionales internas con validación técnica pendiente; no son nuevos D del
repositorio ni acreditan aceptación de Henry/Fernando/juegos/Core. Bank como
saldo global es posición E5 pendiente de encaje Core. R-01, nueve épocas/seis
piezas frente a siete etapas/vestimentas completas y autoequipamiento siguen
abiertos. Escape mantiene penalizaciones y E5 propone solo DC por comprar:
conflicto sin resolver. Los baremos T-01/Q-01/E-01, 3/5/8 y 2/4/6 no se aprueban;
4/3/4 DC solo corresponde a demo interna, no a precios públicos.

D-17/D-19/D-20/D-21, V2-A1…V2-A29 y contratos locales S1–S7-A no cambian.
Rewards v0 permanece candidato; S8-A aprobado y pausado. La normalización de
nombres y el [índice ERD PR07](ERD.md) no autorizan modelos, migraciones o interfaces.

## DOC-3 · Arquitectura Rewards V1 — Acuerdos internos de Parte A · 18/10/2026

**Autoridad y procedencia:** aprobación interna de Jaime comunicada en el encargo
DOC-3 del 18/10/2026, sobre develop `9495bda` tras PR #34. Orienta Parte A;
**no es ratificación conjunta de Jaime, Henry y Fernando ni aceptación de Core o
los juegos**. DAR3 sigue como fuente funcional principal; DuckyEcomotor y
DAR_formulas conservan sus reglas y referencias para contraste. D-20/D-21 y D-19
permanecen vigentes. No se añaden identificadores D ni se implementa Rewards.

| ID | Decisión arquitectónica aprobada internamente por Jaime |
| --- | --- |
| R1 · Identidad | Identidad lógica (origen autorizado, identificador estable del hecho, usuario destinatario). Reintento conserva identidad; actividad válida distinta tiene otra. Emisor y resultado requieren validación del servidor. |
| R2 · Huella y conflictos | Persistir huella del contenido semántico validado. Misma identidad y contenido equivalente recuperan el resultado previo; contenido incompatible genera conflicto sin efectos nuevos. Algoritmo, formato y campos canónicos sin especificar. |
| R3 · RewardEvent | Aceptar el concepto de registro persistente global de evaluación: identidad, huella, regla/versionado, resultado, motivo y referencias a efectos. Estados finales de negocio APPLIED y NO_REWARD; errores técnicos nunca NO_REWARD. Sin representación ORM aprobada. |
| R4 · Atomicidad | Rewards coordina transacción exterior para evaluación, límites, efectos y registro final únicamente si los servicios comparten BD, conexión/alias y frontera transaccional. D-19 vigente; no afirmar atomicidad con Bank/Duckies remotos. Recuperación distribuida pendiente. |
| R5 · Efectos independientes | Admitir XP, DuckyCoins, objetos y puntos, también sin XP y sin XPEvent ficticios. Ecomotor controla XP/evolución, Bank monedas y Duckies inventario. Separar puntos de ascenso y concesión directa; su servicio sigue pendiente. |
| R6 · Límites temporales | Repetición y límites configurables por regla, usuario, actividad y periodo, independientes para XP y monedas. Distinguir reintentos de actividades nuevas y proteger límites frente a concurrencia. Europe/Madrid y una DC por primera finalización válida de juego/día son información local de Training, no contrato global de importes/hechos tardíos. |
| R7 · Errores y correcciones | Error técnico no es evaluación válida sin premio. Recuperar operaciones confirmadas con identidad original. Correcciones posteriores como operaciones nuevas trazables vinculadas al premio original, sin sobrescribir historia. Ajustes o retiradas de XP, monedas, niveles y objetos requieren política aprobada por su propietario. |
| R8 · REST y servicios Python | Núcleo de negocio Rewards en apps.ecomotor, con adaptadores cuando proceda. Conservar POST /api/v1/ecomotor/calculate-action/ y POST /api/v1/ecomotor/commit-rewards/ como referencias DAR_formulas. Calcular acción no concede premio definitivo; confirmar aplica R1–R7 y valida importes del juego. JWT, permisos, formatos, lotes, atomicidad entre destinatarios, WebSockets y publicación HTTP pendientes. |

Estos R1–R8 conservan los IDs del registro de Rewards; no son R-01…R-14 del ERD
global. [Pendientes §3](pending-decisions.md#3-validación-conjunta-de-rewards-v0)
separa para cada uno la aceptación interna y la validación residual. El
[contrato compartido Rewards v0](contracts/rewards-v0.md) sigue **candidato y sin
cambio de versión**: «V1» aquí identifica la dirección arquitectónica interna,
no un contrato definitivo, API publicada o implementación.

No se aprueban RewardRule como tabla, campos/índices/FKs de RewardEvent o ItemGrant,
conservación, importes T-01/Q-01/E-01, precios, penalizaciones Escape, transformación
de inventario ni vestimenta. S1–S7-A no cambian y S8-A continúa aprobado y pausado.

## DOC-4 · Diseño técnico Rewards V1 — T1–T8 · 18/10/2026

**Autoridad:** aprobación interna de Jaime, responsable de Parte A, comunicada
en el encargo DOC-4, sobre develop `be9e7aa` tras PR #35. Desarrolla R1–R8 de
DOC-3 sin cambiar su autoridad: no ratificación conjunta A/B/C ni aceptación de
Core/juegos. DAR3 es fuente funcional principal; los documentos del profesor no
se convierten en aprobación de estas elecciones técnicas. D-19/D-20/D-21 siguen
vigentes. Los identificadores T no son nuevas decisiones D ni tablas integradas.

| ID | Diseño aprobado internamente y alcance condicionado |
| --- | --- |
| T1 · Destinatario e identidad | RewardEvent refiere al User global de Core mediante settings.AUTH_USER_MODEL, sin exigir UserProfileEcomotor como destinatario. Unicidad lógica (origin_code, fact_id, recipient). on_delete, conservación y autorización pendientes con Core. |
| T2 · Identificadores y huella | origin_code estable; fact_id opaco, no vacío y hasta 255 caracteres; destinatario validado. SHA-256 sobre JSON semántico canónico versionado, claves ordenadas, UTF-8 y fechas UTC. Excluir IDs HTTP, instantes de reintento y configuración posterior. Campos semánticos por juego pendientes; igualdad de huella no demuestra autenticidad. |
| T3 · RewardEvent candidato | Modelo candidato en apps.ecomotor: destinatario/origen/hecho/tipo, fecha del hecho/registro, versión y valor de huella, versión de reglas, APPLIED/NO_REWARD y motivo, snapshot JSON histórico y relación opcional candidata con XPEvent. Proponer unicidad compuesta e integridad persistente, sin migración o políticas físicas definitivas. OneToOne opcional solo candidato para XP histórica V1; revisar batch/dominio/extensiones. Sin FKs Bank/Duckies sin contratos. |
| T4 · Integración S3 | Reutilizar grant_historical_xp(profile, amount, operation_key). Rewards valida identidad, huella, duplicados y elegibilidad; S3 controla XP/niveles/evoluciones/puntos de ascenso. Clave XP estable con prefijo reservado rewards:v1: y SHA-256 de la identidad Rewards. No S3 con XP cero ni inicialización automática. XP y RewardEvent en transacción exterior del mismo alias, con snapshots suficientes para replay y detección de incoherencia causal. No cambiar S3 sin necesidad posterior demostrada. |
| T5 · Evaluador | Separar evaluación/aplicación. RewardDecision conceptual: versión, cantidades, elegibilidad y motivos. APPLIED requiere al menos un efecto confirmado; NO_REWARD es evaluación válida sin premio. Configuración/autorización/infraestructura fallidas son errores. Configuración versionada sin tabla RewardRule; no activar baremos sin ratificar, reglas ficticias solo para tests futuros. |
| T6 · Límites concurrentes | RewardLimitUsage auxiliar candidato para cupos por usuario, regla, ámbito y periodo, identidad protegida por unicidad y comprobación/incremento en la misma transacción. XP y monedas separados; reintento no es actividad nueva. D-19/IMMEDIATE sin depender de select_for_update. No activar límites económicos sin contrato Bank; día efectivo, hechos tardíos y cambios de regla pendientes con Training/Core. |
| T7 · Contrato interno candidato | ValidatedRewardFact conceptual: origen, hecho, destinatario, tipo, instante, resultado validado y contexto, junto a contexto de autorización confiable. RewardResult conceptual: ID, estado, replayed, versión de reglas, premios, progresión, motivo y referencias propietarias. Operación candidata process_reward(validated_fact, authorized_context) -> RewardResult. Distinguir errores de entrada, autorización, conflicto, configuración, precondición, propietario y BD; sin firmas definitivas, payloads/códigos HTTP o batch aprobados. |
| T8 · Incrementos | Orden interno aprobado: núcleo puro; persistencia/XP local condicionada; límites; Bank/Duckies/juegos/REST con contratos y autenticación. Cada fase será pequeña, testeable y revisada mediante PR separado. DOC-4 solo documenta, no inicia ninguna fase. |

[Contrato v0, diseño técnico](contracts/rewards-v0.md#10-diseño-técnico-interno--doc-4)
concreta candidatos y límites; [pendientes §7](pending-decisions.md#7-validación-residual-del-diseño-técnico--doc-4)
identifica bloqueos; [plan por fases](team5-work-plan.md#31-fases-rewards--t8-aprobado-internamente-doc-4)
separa el trabajo posterior. La versión global sigue v0 candidata, sin rewards-v1.md.

No se aprueban conservación User/RewardEvent, contratos físicos Bank/Duckies,
importes T-01/Q-01/E-01 o precios, configuración oficial, autorización/JWT Core,
API/batch/WebSockets definitivos, recuperación distribuida ni políticas de hechos
tardíos/correcciones/retirada. S1–S7-A permanecen intactos y S8-A aprobado y pausado.

## DOC-5 · Criterio funcional propuesto de vestimentas históricas · 18/10/2026

**Procedencia:** encargo DOC-5 de Jaime y consulta de las actualizaciones E5 del
18/10 en CORE-07, E5-02 y B-06 del documento compartido «Coordinación entre equipos ·
Respuestas de integración». Se consultó DAR3, pp. 3 y 48: nueve épocas incluida
Era Espacial, apariencia y seis piezas principales, obtención por progreso/misiones,
conservación del progreso y conjuntos anteriores, y evolución automática por umbral.

**Estado:** criterio funcional interno **propuesto por E5**, no requisito confirmado
por Óscar, contrato técnico ratificado o implementación. La consulta sobre reutilizar
apariencias anteriores fue acordada por Jaime y Henry para trasladarla al profesor;
no acredita aceptación técnica inequívoca de Henry de todo el autoequipamiento.

E5 propone que cada época dispusiera de un conjunto completo. Al evolucionar,
el Ducky adquiriría y equiparía automáticamente el de la nueva época. Duckies
conservaría todos los conjuntos completos anteriores ya obtenidos, y el usuario
podría volver a equipar cualquiera de ellos **también durante épocas intermedias**.
Los conjuntos de épocas futuras todavía no alcanzadas no podrían equiparse.
Ecomotor seguiría siendo propietario de la evolución; Duckies, del inventario,
posesión, equipamiento y apariencias.

Esta formulación es posterior al R-01 mixto y a la respuesta E5 anterior que
limitaba la reutilización a fase final/especialización. Se conservan esos
antecedentes; no se convierten retrospectivamente en acuerdos técnicos cerrados.
Evolución, adquisición, posesión, equipamiento y elección de apariencia se distinguen.
**Conjunto completo no implica un único objeto físico del inventario.**

CORE-07, B-06, P6 y R-01 siguen abiertos: Óscar debe confirmar las seis piezas
como posibles objetos diferenciados, entrega automática frente a progreso/misiones,
adquisición/autoequipamiento y reutilización libre, y nueve épocas DAR3 frente a
siete etapas provisionales DuckyEcomotor. La propuesta no sustituye DAR3.
Antes de implementar, Jaime y Henry deberán acordar identidades, idempotencia,
adquisición, equipamiento y recuperación de errores, sin fijar aquí modelos,
transacciones o firmas definitivas. Véanse [arquitectura](architecture.md#31-vestimentas-históricas--propuesta-doc-5)
y [pendientes DOC-5](pending-decisions.md#8-vestimentas-históricas--propuesta-doc-5).
D-20/D-21, Rewards R1–R8/T1–T8, S1–S7-A y el estado pausado de S8-A no cambian.

## F1-A · Núcleo puro Rewards — Concreciones internas aprobadas por Jaime

El encargo de F1-A aprueba cinco detalles de T8/Fase 1 sobre T2/T5/T7 de DOC-4:
JSON semántico determinista versionado, datetimes conscientes normalizados UTC,
JSON exacto sin float/Decimal, RewardDecision inmutable sin efectos aplicados y
evaluación declarativa mínima sin cuotas/concesiones. El [contrato v0 §11](contracts/rewards-v0.md#11-f1-a--núcleo-puro--concreciones-técnicas-aprobadas-internamente)
fija tipos, errores, copia defensiva, formato UTC de seis microsegundos, SHA-256
y matching estricto/ambiguo. Identidad lógica no autoriza origen ni valida User.
Solo biblioteca estándar, reglas ficticias en tests, sin ORM ni servicios propietarios.
No atribuye aprobación a DAR3, Core, Henry, Fernando o juegos; v0 global candidato,
T-01/Q-01/E-01 y contratos compartidos abiertos. S1–S7-A intactos y S8-A pausado.

## DOC-6 · Arquitectura persistente Rewards F2-A · 18/10/2026

**Autoridad y base:** aprobación interna de Jaime/Parte A comunicada en el encargo
DOC-6, sobre develop `5a4e079` tras PR #38. Desarrolla R1–R8 (DOC-3, PR #35)
y T1–T8 (DOC-4, PR #36); no es ratificación de Core, Henry, Fernando ni juegos.
DAR3 conserva su autoridad funcional; las elecciones físicas siguientes son
candidatas, no requisitos atribuidos al profesor ni autorización de migraciones.

Fase 1 está integrada mediante [PR #38](https://github.com/Martret92/duckyarenas-team5/pull/38):
tipos, identidad/huella y evaluación pura. No incluye persistencia, concesiones
ni process_reward. Las menciones anteriores a Rewards sin implementar describen
sus respectivos cortes; el núcleo puro integrado no equivale al servicio global.

| Aspecto | Arquitectura F2-A aprobada internamente / condición |
| --- | --- |
| Alcance local | Persistir evaluaciones válidas y conceder exclusivamente XP histórica positiva mediante S3; evaluación válida sin efectos como NO_REWARD. Rechazar toda la operación si propone un efecto no soportado, sin descartarlo ni convertirlo en NO_REWARD. |
| Registro candidato | RewardEvent con destinatario User vía AUTH_USER_MODEL, identidad única origen/hecho/destinatario, huella y versiones, resultado histórico y OneToOne XPEvent opcional. APPLIED exige XP positiva y XPEvent solo en F2-A; NO_REWARD exige XP cero sin XPEvent. Constraints y modelo físico bloqueados hasta Core. |
| S3 sin cambios | Reutilizar grant_historical_xp con perfil persistido e inicializado para XP positiva. Clave rewards:v1: más SHA-256 de codificación versionada inequívoca de la identidad, nunca de semantic_fingerprint. Validar User, PK canónico y causalidad; no inicializar perfiles ni crear XPEvent con XP cero. |
| Historia y replay | Snapshot candidato reward-result-v1 conserva el resultado original, incluidas progresión y puntos de ascenso. Misma identidad/huella recupera historia sin reevaluar reglas/catálogos; huella incompatible es conflicto. Incoherencia u XPEvent Rewards huérfano es error, sin reconstrucción o reparación silenciosa. |
| Confirmación local | D-19: atomic, BEGIN IMMEDIATE, timeout 5 segundos, duplicados dentro de transacción y unicidad persistente. S3 y RewardEvent comparten alias y frontera; rollback completo y retry explícito en nueva transacción con identidad idéntica. Se recomienda que Rewards controle la confirmación exterior y rechace envolventes incompatibles; sin I/O externo o retry automático. |
| Contrato y autorización | Separar RewardDecision puro, aplicación transaccional, RewardResult confirmado y replay. process_reward sigue conceptual; origin_code y ValidatedRewardFact no autentican. Sin JWT paralelo, API definitiva ni concesiones desde entradas no autorizadas. |

El [detalle técnico F2-A](contracts/rewards-v0.md#12-f2-a--persistencia-y-xp-histórica-local--doc-6)
concentra campos, snapshot, errores y fronteras. El contrato global continúa **v0
candidato**; no se crean RewardEvent/RewardLimitUsage, migraciones ni servicios.
Core debe confirmar User/representación de identidad, conservación/anonimización/
eliminación, on_delete y relaciones con XPEvent/perfiles, y frontera de autorización
**antes de persistir físicamente**. Para premios reales se requieren además
configuración válida de evolución y reglas funcionales autorizadas.

Bank, Duckies y juegos no bloquean el diseño local F2-A; quedan fuera junto con
monedas, inventario/vestimenta, XP de dominio, puntos directos, cupos, RewardRule
como tabla, REST/WebSockets/batch y compensaciones distribuidas. Sus contratos
siguen pendientes para fases posteriores. No se promete atomicidad entre BD o
conexiones independientes. [Bloqueos DOC-6](pending-decisions.md#9-bloqueos-de-persistencia-rewards-f2-a--doc-6)
y [plan](team5-work-plan.md#31-fases-rewards--t8-aprobado-internamente-doc-4)
separan aprobación, implementación y activación. D-17/D-19/D-20/D-21, V2-A1…V2-A29,
S1–S7-A, Fase 1 y DOC-5 no cambian; S8-A permanece aprobado y pausado.

## S8-A · Reactivación e interfaz web local V1

Jaime reactiva S8-A tras coordinación de octubre y DOC-6. El [contrato web](contracts/ecomotor-stat-allocation-web-v1.md)
añade GET/POST autenticados, identidad exclusiva de request.user, forms.Form,
CSRF y clave impredecible conservada en POST/errores. S7-A es el único propietario
de elegibilidad/gasto/replay; no prevalidación web de saldo/Actual/configuración.
Nuevo/replay aplican PRG con mensajes distintos. HTTP 400/404/409/503 genéricos,
overflow 409, CSRF estándar 403. Ruta local sin montaje Core. Decisiones internas,
no atribuidas a DAR3/Core/Rewards. Los estados pausados anteriores son históricos;
F2-A continúa bloqueada para persistencia. S1–S7-A y DOC-6 intactos.

## S9-A · Historial web personal de asignaciones — aprobación interna

S8-A ya está integrada por PR #40 y UI-A por PR #41; las pausas documentadas
anteriormente describen sus cortes históricos. Jaime aprueba S9-A como incremento
local de Parte A, no como requisito literal nuevo de DAR3 ni aprobación de Core.

El [contrato S9-A](contracts/ecomotor-stat-allocation-history-web-v1.md) registra
list_stat_allocation_history y allocation_history_view: solo lectura, propiedad
exclusiva de request.user, snapshots persistidos de S7-A, resultados inmutables,
sin operation_key pública ni reconstrucción con catálogos actuales. Cursor por PK
descendente, límites técnicos 50/100 en servicio y diez en web; validación estricta
de cursores HTTP y errores 400/404/409/503 genéricos. UI-A conserva su identidad
visual y añade navegación accesible. No se modifican S1–S8-A ni el esquema.

Implementación y tests completados en feature para revisión; no se autoriza merge
automático. Sin snapshot transaccional conjunto entre consultas, reparación,
configuración oficial ni integración global de URLs. Conservación, User/auth y
contratos externos siguen pendientes. Rewards v0 continúa candidato global y
F2-A bloqueada para persistencia; S9-A no amplía esos acuerdos.

## S11-A · Selección inicial de especialización — aprobación interna 02B

Jaime/Parte A aprueba la arquitectura general y S11-A-01/S11-A-02 en «02B ·
Arquitectura y repositorio · Continuación». El [contrato S11-A](contracts/ecomotor-specialization-v1.md)
implementa una primera selección local con los modelos actuales, sin nuevas
entidades ni migraciones. V2-A19 contempla Actual; V2-A24 define el catálogo
estable y V2-A25 el progreso de dominio mínimo. Estas precisiones técnicas no
reescriben esos antecedentes ni se atribuyen a DAR3, Óscar/Core o Rewards.

> S11-A-01: En una primera elección, la elegibilidad depende de la configuración confiable de etapas, EvolutionStage y coherencia XP histórica–etapa, siguiendo S7-A. El nivel persistido se valida estructuralmente, pero no se exige LevelThreshold ni coherencia calculada XP–nivel. Esta elección es una decisión técnica local, no una regla atribuida a DAR3.

> S11-A-02: Una repetición del mismo código con perfil, CharacterStats, especialización y progreso persistidos coherentes devuelve la selección existente sin escrituras y sin reevaluar catálogos, configuración o elegibilidad actuales. Los estados inconsistentes se rechazan sin reparación. Es idempotencia basada en estado, no un historial de selección.

select_initial_specialization recarga perfil, CharacterStats y progreso dentro de
atomic usando el alias persistido, conforme a D-19/SQLite IMMEDIATE y timeout 5 s.
Primera elección: solo active_specialization_code y un progreso con domain_xp_total=0
cambian juntos. Repetición: mismos IDs y XP de dominio intacta; otra selección
coherente es conflicto. Estados parciales se rechazan antes de elegir/repetir,
sin reparación ni retries automáticos. Resultado frozen y errores diferenciados;
fallos de BD conservan causa y rollback. No presupone el tipo de PK de User.

Implementación en feature para revisión; S11-A no se considera terminado hasta
revisar y fusionar su PR. P7 permanece abierto para códigos canónicos, obligatoriedad,
condiciones adicionales de acceso, cambios/reinicios, XP de dominio positiva y sus
fuentes/idempotencia, rangos e integración con juegos/Rewards. Conservación y
autoridad Core siguen pendientes; Rewards v0 candidato y F2-A bloqueada sin cambios.

## S12-A · Arquitectura conceptual de XP de dominio — aprobación interna 02B

DOC-S12-A, sobre develop `84f809df43c7db9b438a6541a298214ce8d97b50`, registra
la alternativa C aprobada internamente por Jaime/Parte A en «02B · Arquitectura
y repositorio · Continuación»: servicio propietario local de concesión positiva
de XP de dominio, preparado para integración posterior mediante Rewards.
S11-A está integrado por PR #44. V2-A25/V2-A26 y DOC-6 conservan sus decisiones
históricas; no se atribuye aprobación externa ni se implementa este diseño.

| Decisión interna | Aprobación y límite |
| --- | --- |
| S12-A-01 · Propiedad y coordinación | Ecomotor es propietario del efecto de XP de dominio; Rewards coordina la recompensa global. El servicio local no sustituye esa responsabilidad ni legitima emisores. |
| S12-A-02 · Elegibilidad | Concesión nueva con perfil válido e inicializado, especialización activa coherente, progreso válido y elegibilidad coherente en Actual. Sin nuevos baremos ni condiciones de acceso no concretadas. |
| S12-A-03 · Trazabilidad conceptual | DomainXPEvent aceptado solo como modelo conceptual. No aprobación de ORM, campos/tipos, relaciones físicas, migración ni on_delete. Persistencia bloqueada hasta acuerdo de conservación/anonimización/eliminación con Core. |
| S12-A-04 · Identidad e idempotencia | Principio de identidad única origen–hecho–perfil, repetición histórica sin XP adicional y conflictos de identidad, importe o especialización rechazados. Identificadores, huellas, constraints y contratos de entrada definitivos por concretar; sin esquema físico aprobado. |
| S12-A-05 · Atomicidad | Evento y acumulado de dominio confirman o revierten juntos. D-19: transacciones, concurrencia segura, SQLite IMMEDIATE, duplicados/estados parciales rechazados, fallos operativos diferenciados y rollback. Sin atomicidad prometida entre BD/sistemas independientes. |
| S12-A-06 · Bloqueos | DomainXPEvent físico/migración sin autorizar hasta acuerdo Core de conservación, anonimización/eliminación y on_delete. Premios reales exigen origen autorizado, vínculo confiable hecho–destinatario y reglas validadas. ValidatedRewardFact por sí solo no autoriza. No desbloquea Rewards F2-A. |

El [contrato conceptual candidato](contracts/ecomotor-domain-xp-v1.md) conserva
`grant_domain_xp(profile, validated_fact, amount, authorized_context) -> DomainXPGrantResult`
como propuesta, no API disponible. Firma/tipos, authorized_context, autorización,
esquema físico, integración Rewards, fuentes/cantidades/límites y rangos no quedan
aprobados. Las alternativas A/B sí constan en la deliberación de 02B; no estaban
incorporadas a los documentos del repositorio ni al contexto documental recibido
por Codex. Se recupera esa trazabilidad sin alterar las seis decisiones anteriores:

- **A, estudiada:** servicio local de actualización de XP de dominio, con identidad
  e idempotencia suficientes y sin depender de F2-A.
- **B, estudiada:** concesión de XP de dominio exclusivamente coordinada por Rewards
  global, una vez aprobados sus contratos.
- **C, aprobada internamente:** separar el desarrollo en un núcleo local seguro y
  una integración posterior con Rewards, evitando mecanismos de concesión inseguros
  o incompatibles.

A/B no fueron decisiones aprobadas; no se atribuyen motivos adicionales de descarte.
No se crean código, tablas, migraciones ni tests. P5/P7 y DOC-6 siguen abiertos;
S13-A solo es prioridad funcional provisional futura, sin arquitectura de rangos.

## S13-A / DOC-S13-A1 · Rangos y evaluador puro — aprobación interna 02B

Sobre develop `5d36778449e7c796e2770ddfdb97f25e8f8b280f` (DOC-S12-A, PR #45),
Jaime/Parte A comunica la aprobación interna en «02B · Arquitectura y repositorio
· Continuación». Este corte supera la mención a S13-A sin diseño del antecedente
DOC-S12-A; no reescribe S12-A-01…06, V2-A25/A26 ni DOC-6. DAR3 mantiene su
autoridad funcional y no se atribuyen estas decisiones técnicas a Óscar/Core.

| ID | Decisión interna aprobada |
| --- | --- |
| S13-A-01 | Rangos independientes por especialización: sin rango → Junior → Middle → Senior → Maestro. |
| S13-A-02 | Ascensos secuenciales y requisitos configurables. |
| S13-A-03 | XP histórica y nivel general independientes de los rangos. |
| S13-A-04 | Evaluación pura separada de la confirmación persistente. |
| S13-A-05 | Requisitos de XP de dominio, cursos y retos mediante evidencias verificadas. |
| S13-A-06 | Ascensos confirmados trazables, idempotentes y conservados al cambiar de especialización. |
| S13-A-07 | Políticas versionadas, sin recalcular ni retirar silenciosamente rangos históricos. |

S13-A1 precisa XP mínima de dominio positiva para Junior, umbrales estrictamente
crecientes, AND de todos los requisitos configurados, cursos/retos opcionales si
la política no los exige y evidencia no disponible distinta de cumplimiento.
Se evalúa únicamente el siguiente rango y el resultado nunca confirma un ascenso.

Se registran también, como acuerdos internos, la conservación del progreso de
las cinco especializaciones al alternar y la **opción B de importes independientes
de XP general y XP de dominio**, sin conversión ni baremos oficiales. Esta opción
no es la alternativa B estudiada de S12-A. No implementa cambios/reinicios de rama.

El [contrato candidato del evaluador](contracts/ecomotor-ranks-evaluator-v1.md)
describe `evaluate_rank_eligibility(progress, evidence, policy) -> RankAssessment`,
estructuras, estados, validaciones y pruebas futuras; no es API disponible.
No se modifica ORM, ERD físico, migraciones, servicios ni configuración. Persistencia,
autorización de evidencias, valores oficiales, políticas de cambio y recompensas
tardías siguen pendientes. P5/P7 abiertos; DomainXPEvent solo conceptual;
Rewards v0 candidato y F2-A bloqueado, sin premios reales.

## S14-A · Arquitectura del cambio de especialización — aprobación interna 02B

DOC-S14-A parte de develop `e401c33045b4f1b4c8621c54c21757483769b56b`, con
S13-A1 puro integrado (#47). Jaime/Parte A aprueba internamente en 02B las reglas
siguientes; no se atribuyen literalmente a DAR3 ni a Óscar/Core.

| ID | Decisión interna aprobada |
| --- | --- |
| S14-A-01 | Una sola especialización activa por perfil; progreso independiente conservado en las cinco especializaciones. |
| S14-A-02 | Primera activación de una especialización nunca utilizada: domain_xp_total = 0 y estado funcional sin rango. |
| S14-A-03 | Volver a una anterior reutiliza su progreso sin reiniciar XP de dominio ni rangos confirmados. |
| S14-A-04 | Sin modificar XP histórica, nivel, etapa, estadísticas ni recompensas; sin transferencias de XP entre ramas. |
| S14-A-05 | Servicio local transaccional separado de primera selección, con estado activo esperado y concurrencia D-19. |
| S14-A-06 | V1 sin evento físico de cambio; idempotencia por estado, sin promesa de idempotencia histórica completa. |
| S14-A-07 | Recompensas tardías pendientes de revisión con S12-A, Rewards y Core. |

Cambio solo en Actual, sin retroceso ni consumo de XP histórica.
El [contrato candidato](contracts/ecomotor-specialization-switch-v1.md) describe
`switch_active_specialization(profile, target_code, expected_active_code) -> SpecializationSwitchResult`,
no API disponible. El esquema ya admite varios progresos por pareja única, pero
S11-A exige exactamente uno: adaptar su validación en el futuro requiere precisar
su comportamiento con varias filas coherentes. También queda por concretar la
precedencia entre repetición y estado esperado obsoleto, sin elegirla aquí.

S11-A/S12-A/S13-A conservan sus decisiones históricas. S13-A2 no está implementado;
sin rango es estado funcional, no campo físico. La propuesta preferida de atribuir
una recompensa tardía a la especialización de la actividad entra en conflicto con
S12-A-02 si ya no está activa: requiere revisión explícita y evidencias confiables,
no excepción operativa aprobada. P5/P7 abiertos; DomainXPEvent conceptual,
Rewards v0 candidato y F2-A bloqueado. Sin código, migraciones ni premios reales.

### S14-A-08/09 · Precisiones técnicas aprobadas internamente en 02B

Registro sobre develop `f4c9ce4167f37dcf302b3b3093333a688068e801` (PR #48).
Jaime/Parte A aprueba las siguientes precisiones; resuelven las dos cuestiones
del corte DOC-S14-A anterior, sin modificar retrospectivamente S14-A-01…07.

| ID | Decisión interna aprobada |
| --- | --- |
| S14-A-08 · Compatibilidad S11-A | Admitir varios progresos coherentes de especializaciones distintas, validando su integridad. Repetir el código activo recupera su progreso sin escrituras ni reevaluación de configuración de etapas, con validación estructural y sin reset de XP de dominio. S11-A conserva el conflicto ante otro código y su comportamiento de primera selección. |
| S14-A-09 · Precondición y repetición S14-A | Comprobar expected_active_code antes de tratar la solicitud como repetición. Una discrepancia con la activa persistida rechaza la solicitud aunque target_code ya sea la activa. Con esperado correcto y objetivo activo, devolver estado coherente sin escrituras ni reevaluación de configuración de etapas o elegibilidad; el cambio efectivo exige Actual y transacción D-19. |

El [contrato actualizado](contracts/ecomotor-specialization-switch-v1.md) distingue
estas reglas futuras del código S11-A todavía integrado, que exige un único
progreso. Su adaptación y el servicio de cambio no se implementan aquí.
Se mantiene la limitación A → B → A: comparar el código esperado no detecta toda
solicitud histórica. Sin evento físico, tokens persistentes ni garantía de replay
histórico completo. S12-A-02, P5/P7 y Rewards F2-A conservan sus límites/bloqueos;
recompensas tardías siguen pendientes. No aprobación externa ni premios reales.

## 02C · Arquitectura objetivo del Ecomotor · 20/10/2026

**Procedencia y autoridad:** aprobación interna del Equipo 5 comunicada por Jaime
en este encargo. Base develop `8401d462f70138f0b364a9e3869b1d798b6ae5df`, S14-A
integrado por PR #50 y S13-A1 por #47. La aclaración de Óscar del 19/10 comunicada
por Jaime confirma las siete épocas históricas; no le atribuye diseño técnico
ni las demás decisiones internas. DAR3 sigue principal, con nueve épocas como
antecedente. Se conserva trazabilidad existente, sin nueva consulta directa de PDFs.

**Arquitectura objetivo aprobada internamente, no implementada ni activada.**
V1 y sus contratos siguen describiendo el comportamiento integrado hasta transición
coordinada. Las decisiones anteriores conservan su significado histórico.

| ID / ámbito 02C | Decisión aprobada internamente y alcance |
| --- | --- |
| ARQ-PROG-01 | Prehistórico, Griego, Romano, Medieval, Renacentista, Revolución Industrial, Siglo XX en niveles 1–7, umbrales coincidentes. Nivel 8 abre elección, no octava época; niveles posteriores continúan. Puede aplazarse y seguir como Siglo XX. Sin puntos adicionales por nivel ni XP numérica oficial. |
| A1-CT-01 | Progresión y validación objetivo reconocen todas las épocas cruzadas, distinguen nivel, última época y desbloqueo de elección. |
| A2-CT-01 | Adaptación de XP histórica mantiene referencia S3, atomicidad/idempotencia y transiciones; elimina puntos nuevos por nivel y revisa campos heredados de resultados. Sin cambiar S3 ahora. |
| A3-CT-01 | Compatibilidad de catálogos V1 hasta activación, migración legacy y activación coordinada; correspondencia objetivo de umbrales niveles/épocas sin renombrar historia. |
| T-01 / T-02 / T-03; I-01 | Desde nivel 8, siete históricos jugables y cinco tecnológicos: Developer, Ciber, Sistemas, Data IA, Gamer; códigos pendientes. Una opción explícita activa; antes rige época alcanzada. Confirmar opción/configuración juntas, abandono sin parcial. Cambiar recupera stats y conserva XP/nivel/etapa y dominio/rangos tecnológicos independientes. |
| E-01 / E-02 | ATK Ataque, DEF Defensa, LOG Logística, SPE Especial / Especialización, VEL Velocidad, INT Inteligencia. SPE numérico, no identidad; Cuack pendiente. Snapshot de bases y reparto independientes, efectivas = bases + incrementos, puntos pendientes permitidos. Presupuesto inicial fijo utilizable en cada Ducky, no saldo global consumible. Sin puntos por nivel ni mejoras de seis atributos/puntos adicionales mediante Training en esta V1 objetivo. |
| OP-RED-01 | Redistribución gratuita, ilimitada, por Ducky, histórica, atómica, idempotente y concurrente; sin monedas/objetos ni cambios de bases/XP/nivel/dominio/rangos. No es R-01 histórico de equipamiento. |
| ARQ-OP-01 / ARQ-OP-02 / ARQ-OP-03; DOC-ERD-01 | Cuatro modelos conceptuales no implementados: PlayableOption, UserPlayableState, UserPlayableStats y PlayableStatsChangeEvent. Exclusión histórica/tecnológica, configuración única estado/opción, presupuesto/activa coherentes y eventos únicos estado/operation_key. ARQ-OP-02 aprueba diseño provisional de campos y restricciones de PlayableOption, UserPlayableState y UserPlayableStats; migraciones, relaciones físicas definitivas y on_delete no aprobados. |
| SVC-OP-01 | Configurar opción nunca usada: nivel 8 y elegibilidad, snapshot/reparto/selección/evento atómicos; estado solo en primera confirmación. Tecnología sin progreso crea dominio cero, nunca reset existente. |
| SVC-OP-02 | Activar configuración existente con revisión esperada: si coincide y destino ya activo, devolver estado existente sin escrituras; revisión obsoleta rechaza incluso destino activo. Sin modificar stats/progreso, configurar destinos automáticamente o generar redistribución. Sin replay histórico completo tras A → B → A; detalle técnico de implementación pendiente. |
| SVC-OP-03 | Consulta coherente de opción efectiva y seis atributos: época antes de elegir; activa/configuración conservada después. Sin escrituras. |
| SVC-OP-04 | Reparto completo de seis incrementos, propiedad/presupuesto/revisión y evento atómicos; no afecta a otros Duckies ni consume recursos. |
| DOC-CON-01 | Contrato objetivo nuevo separado de V1, entradas/resultados conceptuales, sin firmas/APIs implementadas. |
| COMP-01 / ORD-OP-01 / PLAN-OP-01 | Conservar nueve épocas DAR3, siete etapas V1 terminadas en Actual y siete épocas objetivo terminadas en Siglo XX. Inventariar/clasificar legacy y acordar migración/activación sin reasignar stats/historia o duplicar autoridades. Core/P5 conserva relaciones/retención/on_delete pendientes. Implementación posterior en 01B. |

Los IDs T/E/I anteriores se interpretan en **02C**, sin aprobar baremos homónimos
de juegos. El [contrato objetivo](contracts/ecomotor-playable-options-target-v1.md)
concentra alcance y pendientes; [ERD conceptual](erd/ecomotor.md#14-opciones-jugables--modelos-conceptuales-02c)
separa diseño de nueve entidades físicas. [Pendientes 02C](pending-decisions.md#13-pendientes-residuales-de-la-arquitectura-objetivo-02c)
no reabre lo aprobado ni cierra P1–P8 en bloque.

**Sustitución funcional futura, no retroactiva:** 02C sustituirá el objetivo anterior
de Actual, stats globales y puntos por nivel (V2-A8/A19/A20/A21 y servicios V1 en
lo incompatible) al activarse; conserva esos antecedentes. S1/S2-A/S3/S7-A/S11-A,
S13-A1 y S14-A siguen integrados; S3 todavía concede puntos por nivel. S13-A2 y
DomainXPEvent no son persistencia existente. Rewards F2-A mantiene sus bloqueos;
DOC-5 es vestimenta/inventario, no identidad jugable. No se autoriza migración,
borrado de eventos, recálculo legacy o cambio de código en esta tarea documental.

## A2 · Arquitectura de XP histórica objetivo · 20/10/2026

**Autoridad:** aprobación interna de 02C comunicada por Jaime en el encargo A2,
sobre develop `6a7d1d7c8cede455e1aa9ecd2de66382bea3aba7`. A1.1 (#52) y A1.2
(#53) ya están integrados como validación/cálculo puros, sin escritores objetivo.
DAR3 conserva su autoridad funcional; estas elecciones técnicas no son requisitos
literales del profesor ni ratificación de Core. Se usa la trazabilidad existente,
sin nueva consulta directa de PDFs. Los acuerdos 02C anteriores se conservan.

| ID | Decisión aprobada internamente / alcance |
| --- | --- |
| A2-ARQ-01 | Servicio objetivo separado. S3 V1 conserva interfaz, puntos y comportamiento hasta activación coordinada; no se modifica ahora. |
| A2-VER-01 | Versión de concesión decidida por servidor confiable. catalog_version textual o snapshot validado A1.1 no autorizan producción. Clasificación persistente de perfil, escritor único y activación dependen de A3; sin selección automática de versión. |
| A2-IDEM-01 | Mantener (profile, operation_key), sin añadir versión a identidad. Operaciones existentes recuperan datos históricos sin catálogos actuales; importe incompatible es conflicto. Conservar límites de snapshots XPEvent/EvolutionEvent, sin replay completo inventado. |
| A2-EVO-01 | A1.1/A1.2 calculan nivel/época y todos los cruces. Nueva concesión futura crea un XPEvent y exactamente las EvolutionEvent causales de épocas cruzadas, sin otra época en nivel 8 ni eventos iniciales ficticios. |
| A2-RES-01 | Nuevas concesiones objetivo sin puntos por nivel; si se conservan campos compatibles, stat_points_awarded=0 y available_points_after=None. No reinterpretar puntos/resultados históricos V1. |
| A2-VAL-01 | Validar perfil, XP, nivel, etapa, estadísticas según clasificación, catálogos y causalidad; rechazar incoherencias sin reparar legacy. No inferir clasificación por ausencia de estado. |
| A2-IMP-01 | Primer incremento implementable: planificador puro sobre A1.1/A1.2; sin escrituras/modelos/migraciones, cambios S3 o activación. No se crea en este PR. |

[Contrato A2 objetivo](contracts/ecomotor-target-xp-v1.md) detalla alternativas,
resultados, replay entre versiones y D-19. **A2-CT-01 sigue siendo adaptación de XP
sin puntos; A3-CT-01 sigue siendo compatibilidad de catálogos, migración legacy y
activación coordinada.** El servicio transaccional A2 no está implementado;
clasificación, migración y compatibilidad de resultados se resolverán en A3.

XPEvent no persiste versión, nivel o época como snapshots; EvolutionEvent conserva
la referencia de etapa, no sus atributos históricos originales. La mención original
a EvolutionEvent en A2-EVO-01 se conserva como antecedente; su materialización
objetivo queda precisada posteriormente por
[A3-CAT-EVENT-01](#a3-cat-event-01--separación-de-eventos-objetivo--21102026),
sin retirar causalidad, todos los cruces, replay, escritor único o atomicidad A2.
No reconstruir historia con catálogos nuevos, renombrar etapas o convertir puntos
antiguos a cero.
Core/P5 conserva retención, anonimización/eliminación y on_delete pendientes.
[Dependencias A3](pending-decisions.md#14-a2--dependencias-para-xp-histórica-objetivo)
no bloquean diseñar/probar el planificador puro, pero sí la futura activación.
No se modifican contratos V1 ni se desbloquean dominio, S13-A2 o Rewards F2-A.

## A3 · Compatibilidad histórica y activación coordinada · 20/10/2026

**A3-ARQ-01, aprobación interna y condicionada del Equipo 5**, comunicada en el
encargo A3. Base develop `7039ae64cd8975f14a93c4d4bbbc92893adc5ffd`; A2.1 puro
integrado por PR #56, sin escritor objetivo. DAR3 sigue como fuente funcional;
aclaraciones de Óscar sobre épocas no aprueban mecanismos Django, versión o
despliegue elegidos internamente. Se conserva trazabilidad existente, sin nueva
consulta directa de PDFs ni aprobación de contratos físicos externos.

| ID | Decisión interna aprobada / condición |
| --- | --- |
| A3-CLAS-01 | Proponer registro persistente de política unívoco por UserProfileEcomotor, separando procedencia y estado de transición. No inferirlo por nivel/época/stats/ausencia de UserPlayableState; existentes requieren auditoría. Clasificación no autoriza XP; campos/tipos/constraints pendientes. |
| A3-CAT-01 | Conservar EvolutionStage V1 y adoptar catálogo objetivo separado, versionado e inmutable tras uso. Nueve épocas DAR3, siete etapas V1/Actual y siete épocas objetivo/Siglo XX siguen distintas; nivel 8 no añade época. Identificación causal en EvolutionEvent y adaptación PlayableOption son bloqueos físicos, sin solución aprobada. |
| A3-MIG-01 | Inventario de perfiles/XP/niveles/épocas/eventos/stats/especializaciones y Duckies. Diagnósticos compatibles, requieren decisión o incoherentes no autorizan migración automática. Futura migración explícita/trazable/idempotente/concurrente; no reinterpretar eventos, reasignar stats ni recalcular XP/niveles por inferencia. |
| A3-WRITER-01 | S3 V1 vigente hasta activación; único punto interno futuro con versión confiable del servidor, nunca del cliente. Preferir primera activación mediante corte global coordinado frente a cohortes con escritores simultáneos. Preparación/suspensión/activación/detención son conceptos, no constantes o implementación. |
| A3-REPLAY-01 | UNIQUE(profile, operation_key) entre versiones; validación inicial y transacción antes de buscar operación. Existente valida importe/snapshots/causalidad y devuelve historia disponible sin catálogo/clasificación nueva. Ausente comprueba clasificación/escritor. Nuevas concesiones objetivo necesitan procedencia persistente inmutable, representación física pendiente. |
| A3-RES-01 | S3 conserva puntos mientras activo. Concesión objetivo nueva sin puntos: compatibilidad 0/None en stat_points_awarded/available_points_after; no reinterpretar V1, borrar saldo heredado o reconstruir snapshots ausentes. Interfaz final compartida pendiente. |
| A3-DEPLOY-01 | Inventario → esquema compatible aprobado → clasificación/auditoría → ensayo aislado → suspensión/drenaje → migración autorizada → activación objetivo → supervisión/detención segura. Requiere datos/catálogos/autorización, escritor único, consumidores, pruebas y acuerdos externos; sin reversión automática a S3 tras XP objetivo. |

La referencia original de A3-CAT-01 a identificación en EvolutionEvent es un
antecedente precisado por [A3-CAT-EVENT-01](#a3-cat-event-01--separación-de-eventos-objetivo--21102026):
eventos objetivo separados, sin diseño físico aprobado.

El [contrato A3](contracts/ecomotor-transition-target-v1.md) concentra diseño y
bloqueos. XPEvent V1 no guarda versión/nivel/época; EvolutionEvent no guarda
atributos históricos de etapa. Se conserva A2-IDEM-01 y su replay primero,
sin rutas alternativas no autorizadas ni reinterpretación de información ausente.

**A3.1 es propuesta futura:** auditoría pura por snapshots explícitos y diagnósticos
inmutables, sin ORM/escrituras/XP o permiso de migración; nombres/firmas candidatos
se concretarán en 01B. No se crea ningún archivo Python en esta tarea.
Dependencias actuales Duckies: EvolutionItem.stage, current_stage_code y consultas
de época/ordinales; referencias de catálogo deben coordinarse con Henry.
Clasificación, catálogo físico, nuevas relaciones causales/PlayableOption y
procedencia persistente siguen sin implementar; Core/P5, datos reales/contratos,
catálogos autorizados y pruebas mantienen sus bloqueos. No se desbloquean Rewards
F2-A, dominio persistente, S13-A2 ni economía/inventario. [Pendientes A3](pending-decisions.md#15-a3--condiciones-de-compatibilidad-y-activación).
A1-CT-01/A2-CT-01 conservan su significado; A3-CT-01 es compatibilidad/transición.

## A3.2 · Inventario legacy de solo lectura · 20/10/2026

**A3.2-ARQ-01, aprobación interna del Equipo 5**, comunicada en este encargo sobre
develop `8024fa7673e5587bcc49025a2fafe3eb215c1273`. A3 (#57) y A3.1 (#58) están
integrados; las menciones anteriores a A3.1 futuro son antecedentes fechados.
DAR3 conserva autoridad funcional; extractor/alias/transacciones son elecciones
técnicas internas, no especificación literal del profesor o permiso de Core.

| ID | Decisión interna / límite |
| --- | --- |
| A3.2-SCOPE-01 | Un perfil por operación: perfil, CharacterStats, XPEvent/EvolutionEvent propios, catálogo EvolutionStage V1 completo y causalidad mínima bidireccional. No inventario masivo ni auditoría integral de asignaciones, especializaciones, Duckies, umbrales/puntos históricos o migración. |
| A3.2-API-01 | extract_legacy_audit_snapshot(profile_id, *, using) -> LegacyAuditSnapshot conceptual; ID entero estricto persistido, alias de llamador interno confiable y autorizado. Solo clases tipadas A3.1, sin modelos/QuerySets, diagnósticos o permisos. Firma definitiva en 01B, sin auth propia. |
| A3.2-CONS-01 | Todas las lecturas y materialización en transacción corta del mismo alias. SQLite IMMEDIATE/timeout 5 puede bloquear escritores; sin row locking select_for_update, I/O externo, esperas o auditorías extensas. Proponer rechazo de transacción exterior activa. Fotografía posterior no es evidencia indefinidamente vigente ni permiso de migración. |
| A3.2-COV-01 | Sin snapshots parciales. xp_events_complete: todos propios; evolution_events_complete: todos propios y causalidad prevista completa; stages_complete: catálogo completo; character_stats_observed: consulta correcta incluso sin fila. Vacíos observados válidos y stats ausentes None; cobertura no significa coherencia. Fallos nunca se convierten en vacíos inventados. |
| A3.2-CAUS-01 | Detectar evolución propia con causa XP ajena y evolución ajena con XP propia, usando solo IDs/propietarios mínimos sin incorporar historiales ajenos. Causalidad cruzada confirmada falla; causa realmente ausente conserva referencia representable para XP_CAUSE_NOT_FOUND. Sin reparar, ampliar permisos o filtrar datos de terceros. |
| A3.2-PRIV-01 | Campos mínimos de snapshots, operation_key exacta sin normalizar/truncar/anonimizar; no logs/errores/trazas/exportaciones con su contenido. Sin datos personales Core, endpoint público, exportación masiva o almacenamiento adicional. |
| A3.2-SEP-01 | Extractor obtiene evidencia, A3.1 evalúa, futuros servicios clasifican/migran/conceden con permisos propios. Sin invocación automática de auditoría, clasificación o migración; fotografía/diagnóstico compatible no activa políticas. |

[Contrato A3.2](contracts/ecomotor-legacy-inventory-v1.md) concentra cobertura,
campos, errores conceptuales y pruebas previstas. A3.1 ya implementa snapshots y
audit_legacy_transition, no este extractor. Las ausencias observadas pueden ser
diagnósticos del auditor; causalidad extranjera confirmada es fallo del extractor.
A3.2 no está implementado y no devuelve resultados de auditoría.

Incremento futuro en 01B: legacy_inventory_reader.py y test_legacy_inventory_reader.py,
nombres/firmas por revisar; no se crean en esta PR. Sin cambios iniciales de A3.1,
S3, modelos Users/Ecomotor/Duckies, migraciones o configuración. Errores separados
de ID/alias/perfil/lectura/cobertura/representabilidad/causalidad, sin clases Python
ni códigos HTTP definitivos. Pruebas de concurrencia SQLite previstas con
TransactionTestCase y conexiones independientes, no ejecutadas aquí.
[Pendientes](pending-decisions.md#16-a32--alcance-y-validaciones-pendientes): auditoría
integral, Core/P5, consumidores, clasificación/catálogo físicos y migración/activación.
S3 V1 sigue activo; no se desbloquean dominio persistente, S13-A2, Rewards F2-A ni economía.

## Conciliación de aclaraciones de Óscar · 20/10/2026

**Procedencia:** consulta del documento compartido «DuckyArenas · Coordinación
entre equipos · Respuestas de integración» (CORE-03, CORE-07, PROF-04 y Training)
el 20/10/2026; confirmación directa de Jaime en 02C de lo indicado por Óscar.
Henry tomó notas y Óscar escribió los atributos en la pizarra, según esa confirmación;
no se afirma inspección independiente de la pizarra. La fecha es la de conciliación,
no una fecha de respuesta inferida: el documento aún conserva marcadores y etiquetas
antiguas de pendiente. No se modificó la fuente compartida ni se elevan sus demás
propuestas a acuerdos. DAR3 sigue principal; estas son aclaraciones funcionales
posteriores, distintas de decisiones internas E5 y contratos técnicos pendientes.

| Fuente / asunto | Aclaración confirmada y alcance residual |
| --- | --- |
| CORE-03 · membresías | User, Free, Plus y Pro. User es categoría funcional de acceso visual previo a entrar a la plataforma, no el modelo Django User. La XP de una misma actividad elegible debe ser igual entre membresías jugables. Se contempla DuckyCoins extra por pago, sin cantidades/fórmulas/baremos definitivos. Contratos de identidad, permisos y membresías siguen con Core. |
| Training · contraste | Respuesta local de 2 XP Free / 5 XP Plus-Pro contradice la igualdad XP confirmada por Óscar. Se conserva como antecedente y conflicto a conciliar con Training, sin escoger nueva cantidad ni activar reglas o modificar código externo. |
| CORE-07 · vestimenta | Una imagen de vestimenta completa por época, en lugar de seis piezas visuales separadas. Durante progresión histórica solo vestimenta de época vigente; tras elegir especialización pueden reutilizarse anteriores desbloqueadas. DOC-5 proponía reutilización también intermedia: antecedente más amplio, no comportamiento confirmado. Adquisición/autoequipamiento y representación física/contratos Duckies siguen pendientes. |
| CORE-07 · atributos/pizarra | Ataque, Defensa, Velocidad, Inteligencia, Lógica y Cuak. Atributos específicos por época y distribución de puntos al alcanzar especialización. El ejemplo 45 puntos no es presupuesto oficial. Definición técnica/papel de Cuak, códigos, bases y presupuesto siguen por concretar. |
| Contraste E-01/E-02 de 02C | ATK, DEF, LOG (Logística), SPE (Especial / Especialización), VEL e INT fueron aprobación interna. Lógica frente a Logística y Cuak frente al esquema interno exigen conciliación explícita; no mapear Cuak a SPE ni renombrar/reinterpretar códigos o datos. Composición/correspondencia técnica pendiente de adaptación; otras decisiones 02C no se reabren por inferencia. |
| PROF-04 / aclaración del 19/10 ya registrada | Se mantienen siete épocas históricas terminadas en Siglo XX y elección desde nivel 8. No se reabre la secuencia ni se alteran identidades V1; PROF-04 lista épocas/tecnologías, sin aprobar códigos o migración. |

DAR3/nueve épocas/seis piezas y DOC-5/02C se conservan como antecedentes, sin
presentar propuestas internas como confirmaciones de Óscar. Se precisan solo
los conflictos de vestimenta y atributos; no se decide un objeto único por imagen,
una FK o equipamiento automático. Identidad jugable histórica, época y apariencia
siguen distintas; cómo relacionar la elección jugable 02C con la condición visual
«tras elegir especialización» requiere coordinación, no equivalencia automática.
SPE sigue siendo atributo numérico del diseño interno, no identidad de rama;
no se atribuye a la pizarra ese código o significado. Cuak (Cuack en notas previas)
no se añade como séptimo atributo ni se implementa por esta conciliación.

[Matriz de procedencia](contracts/integracion-equipo5-v0.md#02-aclaraciones-confirmadas-de-óscar--conciliación-del-20102026),
[arquitectura](architecture.md#13-aclaraciones-funcionales-confirmadas-y-contraste-con-02c),
[contrato objetivo](contracts/ecomotor-playable-options-target-v1.md#8-conciliación-funcional-posterior-con-óscar)
y [pendientes residuales](pending-decisions.md#17-aclaraciones-confirmadas-de-óscar--pendientes-residuales).
Sin nuevas decisiones D, precios o cantidades oficiales, cambios S3/A3.1/A3.2,
activación A2 ni modificaciones de contratos Rewards/Bank/Duckies.

## ATR-OBJ-01 · Nomenclatura de atributos objetivo · 20/10/2026

**Autoridad y procedencia:** precisión funcional confirmada por Jaime tras las
aclaraciones de Óscar conciliadas en la PR #61. Aprobación interna del Equipo 5
para el diseño objetivo 02C; DAR3 sigue siendo la fuente funcional principal.
No se atribuye al profesor la aprobación de códigos o mecanismos Django.

Se realizan solo dos sustituciones: LOG pasa de Logística a **Lógica**; SPE se
denomina **CUACK**, manteniendo **Especial / Especialización**. Los seis atributos
objetivo vigentes son:

| Código | Significado |
| --- | --- |
| ATK | Ataque |
| DEF | Defensa |
| VEL | Velocidad |
| INT | Inteligencia |
| LOG | Lógica |
| CUACK | Especial / Especialización |

CUACK es un atributo numérico, no la identidad de una especialización tecnológica.
No se añade un atributo ni se inventan efectos especiales. Quedan resueltos estos
códigos y significados; siguen pendientes bases, presupuesto, fórmulas y migración
legacy. Los registros fechados E-01/E-02 de 02C y de conciliación de la PR #61
se conservan como antecedentes, sustituidos solo en esta nomenclatura objetivo.

**Compatibilidad:** S3 V1, CharacterStats, StatAllocationEvent, sus registros y
contratos conservan log_stat = Logística y spe = Especial / Especialización.
No convertir automáticamente valores históricos SPE a CUACK ni reinterpretar
log_stat como Lógica. No se cambian servicios, eventos, modelos o migraciones V1.
El diseño objetivo sigue sin implementar ni activar; no se activa A2 ni se reabren
épocas, nivel 8, opciones jugables, redistribución u otras decisiones no afectadas.

[Contrato objetivo](contracts/ecomotor-playable-options-target-v1.md#3-opciones-y-estadísticas),
[arquitectura](architecture.md#9-arquitectura-objetivo-02c--no-implementada),
[ERD conceptual](erd/ecomotor.md#14-opciones-jugables--modelos-conceptuales-02c) y
[pendientes](pending-decisions.md#13-pendientes-residuales-de-la-arquitectura-objetivo-02c).

## A3.3 · Clasificación persistente de perfiles · 20/10/2026

**A3.3-ARQ-01, aprobación interna del Equipo 5**, comunicada por Jaime en 02C,
sobre develop `75177a238fa74d6e1c719d8074d3e4741d607ee0`. Desarrolla A3-CLAS-01;
DAR3 sigue siendo la autoridad funcional principal. No es aprobación de Core/P5,
Henry ni del profesor de modelos Django, permisos o despliegue.

Estado vigente: A3.1 integrado por #58 y extractor A3.2 por #60; sus anotaciones
anteriores de implementación futura conservan su corte histórico. S3 V1 sigue
como único escritor de XP; A2.1 solo planifica. **A3.3 no está implementado**.

| Decisión | Acuerdo interno / condición |
| --- | --- |
| A3.3-PHYS-01 | ProfileProgressionPolicy candidato, OneToOne conceptual con UserProfileEcomotor; profile, origin, transition_state, revision, created_at, updated_at. Separar procedencia/transición; sin tabla, constraint físico, migración u on_delete aprobado. |
| A3.3-ORIGIN-01 | Procedencia explícita sin default clasificador e inmutable una vez confirmada. LEGACY_V1, NATIVE_V1 y NATIVE_TARGET son valores candidatos; nombres y matriz completa pendientes. |
| A3.3-STATE-01 | PENDING_REVIEW, V1_VERIFIED, TARGET_PREPARED, TARGET_CONFIRMED y BLOCKED candidatos. Sin registro significa no clasificado, no revisión. No inferir por fecha/nivel/XP/época/especialización/stats/estado jugable ausente. Revisión monotónica no negativa; transiciones/nombres/permisos por concretar y probar. |
| A3.3-EVENT-01 | ProfileProgressionPolicyEvent candidato e inmutable: perfil, operation_key, acción, estados/revisiones anteriores y posteriores, confirmación y operador autorizado pendiente de Core. UNIQUE(profile, operation_key) conceptual en clasificación; repetición compatible sin efectos y contenido incompatible en conflicto. No sustituye eventos XP/evolución/stats. |
| A3.3-AUTH-01 | Clasificación, activación global, emisor autorizado y precondiciones XP son garantías distintas. No hay interruptor XP por perfil. TARGET_CONFIRMED no activa objetivo; S3 V1 sigue bajo su contrato incluso sin clasificación hasta corte autorizado, sin escritores contradictorios. |
| A3.3-LEGACY-01 | A3.2 extrae fotografía y A3.1 evalúa alcance limitado. COMPATIBLE no clasifica/migra/repara ni autoriza XP. Evidencia puede quedar obsoleta por S3; futura clasificación requiere actualidad y frontera segura, sin backfill ni procedencia inventada. |
| A3.3-TX-01 | Política y evento confirman/revierten juntos: alias común, atomicidad D-19, idempotencia, revisión esperada y rechazo de cambios obsoletos, SQLite BEGIN IMMEDIATE/timeout 5 s. Sin I/O externo ni bloqueo de fila supuesto mediante select_for_update. Sin firmas definitivas. |
| A3.3-CORE-01 | Conservación, anonimización/eliminación, relaciones/on_delete, identidad del operador y autorización del proceso pendientes de Core/P5; consumidores y Duckies requieren coordinación con Henry. |
| A3.3-IMP-01 | Documentación → reglas puras/validadores 01B → contratos Core/P5 → modelos/migraciones sin backfill automático tras acuerdos → servicios/tests → catálogo/causalidad/Duckies → migración autorizada, ensayos y activación posterior. Aquí solo documentación. |

[Contrato A3.3](contracts/ecomotor-profile-classification-v1.md) concentra candidatos,
operación, errores, garantías y tests futuros; [arquitectura](architecture.md#14-a33--clasificación-persistente-de-perfiles),
[ERD](erd/ecomotor.md#16-a33--política-de-progresión-e-historial-conceptuales) y
[pendientes](pending-decisions.md#18-a33--pendientes-de-clasificación-persistente).
Sin reinterpretar eventos V1, crear modelos/backfill, clasificar perfiles o activar XP.
ATR-OBJ-01 y demás decisiones anteriores mantienen su alcance; no se desbloquean
Rewards F2-A, dominio persistente, S13-A2 o integración económica.

## A3.3 · Matriz, recuperación y revisiones · 20/10/2026

**Aprobación técnica interna del Equipo 5 en 02C**, posterior a la PR #63,
sobre develop `b913bf88ee205d87fb7a0a9e11573123028ebfd1`. Precisa A3.3-STATE-01
y A3.3-TX-01; no es nueva exigencia literal DAR3 ni aprobación de Core/P5.
La decisión A3.3 anterior conserva su significado histórico: entonces la matriz
estaba pendiente; ahora se documenta su resolución interna, sin implementación.

| Identificador | Acuerdo y alcance |
| --- | --- |
| A3.3-MATRIX-01 | Aprobar la matriz y primeras clasificaciones del contrato §3.1–§3.2: legacy sin registro → PENDING_REVIEW; PENDING_REVIEW → V1_VERIFIED → TARGET_PREPARED → TARGET_CONFIRMED con las condiciones autorizadas de cada paso. Alta NATIVE_V1 únicamente confiable/verificada en V1_VERIFIED; NATIVE_TARGET únicamente tras activación global y alta objetivo válida en TARGET_CONFIRMED. No inferir procedencia/estado ni cambiar procedencia confirmada. Todas las demás transiciones nuevas se rechazan, incluido retroceso TARGET_CONFIRMED → V1_VERIFIED. |
| A3.3-RECOVERY-01 | Cualquier estado registrado distinto de BLOCKED puede bloquearse por incidencia justificada y acción autorizada. Recuperación explícita solo al estado inmediatamente anterior al bloqueo, con nueva validación y evidencia inequívoca en el evento. No alterar/borrar el bloqueo. BLOCKED → BLOCKED prohibido como operación nueva; replay de bloqueo confirmado conserva idempotencia. |
| A3.3-REV-01 | Primera clasificación revision=1, ausencia de estado anterior sin inventar historia. Cada transición nueva confirmada suma 1 y registra evento propio. Replay compatible sin mutación/revisión/evento nuevo; identidad conceptual (profile, operation_key) de clasificación. Orden preciso de contenido/revisión/replay pendiente antes de servicios, con D-19 e idempotencia intactos. |

[Matriz y condiciones completas](contracts/ecomotor-profile-classification-v1.md#31-matriz-aprobada--a33-matrix-01)
centralizan el detalle, sin duplicar un contrato físico. TARGET_CONFIRMED no activa
XP; BLOCKED no sustituye controles globales de activación/suspensión. Evidencia
A3.2/COMPATIBLE A3.1 no autoriza clasificación/migración y su vigencia transaccional
sigue pendiente de protocolo. No backfill, reparación, migración o clasificación real.

Tests puros futuros 01B: matriz permitida/prohibida, altas por procedencia,
recuperación válida/inválida, procedencia inmutable, revisiones, replay y conflicto.
Concurrencia/rollback/idempotencia persistente se probarán en servicio Django futuro
tras dependencias Core/P5. Sin código/tests nuevos ni ejecución de tests Django.
[Pendientes](pending-decisions.md#18-a33--pendientes-de-clasificación-persistente).
ATR-OBJ-01, S3 V1 y los demás acuerdos no afectados permanecen intactos.

## A3.3 · Contenido, revisión y replay · 20/10/2026

**Aprobación técnica interna del Equipo 5 en 02C**, posterior a la integración de
PR #64, sobre develop `e362cbf5b15ac56bbc33eb6f4ec4d621d26b1f0c`. No son requisitos
literales nuevos de DAR3 ni aprobaciones de Core/P5. Se conservan los registros
fechados anteriores: su pendiente de orden conceptual se resuelve solo por esta
precisión, sin alterar matriz, altas o recuperación ya aprobadas.

| Identificador | Acuerdo interno y límites |
| --- | --- |
| A3.3-CONTENT-01 | Identidad (profile_id, operation_key), propia de clasificación. Comparar contenido original: perfil/clave exactos, acción, procedencia pertinente, destino, expected_revision original y motivo/referencia cuando corresponda; recuperación vinculada inequívocamente al bloqueo. Tipos distintos no equivalen ni None=0; sin normalización silenciosa. Contenido igual confirmado permite replay, diferente produce conflicto; evidencia insuficiente no acredita igualdad. Conservación/comparación física y participación canónica del operador siguen pendientes con Core/P5. |
| A3.3-REV-PROTOCOL-01 | Primera clasificación con expected_revision=None y ausencia real de política confirma revision=1, sin estado/revisión anterior fabricados. Transición nueva requiere revisión exacta actual y confirma +1/evento; obsoleta rechaza. Replay compatible no exige que revisión original coincida con la actual ni modifica estado, revisión o eventos. |
| A3.3-REPLAY-PROTOCOL-01 | Validación estructural/identidad/clave/autorización → transacción D-19 mismo alias → buscar evento primero. Existente: integridad/contenido original y resultado histórico sin efectos, o rechazo por diferencia/comparación injustificable. Solo sin evento: ausencia/revisión actual, procedencia, matriz, estado, autorizaciones y evidencia suficiente/vigente; confirmar política/evento juntos o rollback. No revalidar elegibilidad actual del evento histórico ni presentar replay como estado actual. |

[Contrato canónico y casos A–D](contracts/ecomotor-profile-classification-v1.md#41-contenido-original-comparable--a33-content-01)
y [orden conceptual](contracts/ecomotor-profile-classification-v1.md#72-orden-de-procesamiento--a33-replay-protocol-01).
Repetir bloqueo confirmado tras recuperar no vuelve a bloquear; la matriz y la
recuperación al estado anterior permanecen intactas. Replay conserva autorización
inicial y no permite consultar perfiles ajenos.

Siguen pendientes evidencia suficientemente actual mientras escribe S3 y frontera
segura sin anidar incorrectamente A3.2, representación persistente, identidad y
autorización del operador, conservación/eliminación/anonimización/on_delete Core/P5.
TARGET_CONFIRMED no activa XP; S3 V1 sigue como único escritor hasta corte global.
Sin código, modelos, migraciones, clasificación real, backfill, activación o tests
nuevos. Tests puros futuros 01B cubren contenido/tipos, None frente a 0, revisiones,
replay posterior, bloqueo recuperado e historia insuficiente/incoherente;
concurrencia/rollback/idempotencia persistente quedan para servicio Django futuro.
[Pendientes](pending-decisions.md#18-a33--pendientes-de-clasificación-persistente).

## A3.4 · Dirección de persistencia de clasificación · 20/10/2026

**A3.4-ARQ-01, aprobada internamente por el Equipo 5 en 02C**, sobre develop
`8b6b0f783b0042e66c53d9b46dfb930edae94f73`, tras integrar reglas puras A3.3
por PR #66. DAR3 conserva autoridad funcional; esta dirección técnica no se
atribuye al profesor, Core/P5 o Henry. No aprueba modelos Django definitivos,
migraciones, contratos externos o activación. Los registros anteriores conservan
su fecha/autoridad; sus previsiones de reglas futuras son antecedentes, no estado actual.

| Estado | Dirección o decisión pendiente |
| --- | --- |
| Arquitectura aprobada | Propiedad Equipo 5/apps.ecomotor, referencia conceptual a users.UserProfileEcomotor sin redefinir User. Política máxima una por perfil, procedencia explícita inmutable, transición separada y revisión positiva; ausencia no clasifica ni defaults automáticos. |
| Arquitectura aprobada | Evento inmutable separado, identidad UNIQUE(profile, operation_key) propia de clasificación, con evidencia suficiente para reconstruir ClassificationRequest, before=None o PolicySnapshot, after y ConfirmedClassificationEvent. Primera clasificación sin estado/revisión previa inventados. Bloqueo con estado anterior inequívoco; no elegir FK al bloqueo. |
| Arquitectura aprobada | Autorización previa, alias común, D-19/BEGIN IMMEDIATE/timeout 5 s, evento primero y validación por API pura; replay compatible sin mutación, conflicto/historia insuficiente rechazados. Nuevas operaciones requieren revisión/procedencia/matriz/evidencia; política/evento confirman juntos o rollback. Sin I/O externo, row locking supuesto o atomicidad entre conexiones. |
| Dirección de evidencia aprobada | Lector interno específico para comprobaciones dentro de la futura transacción; A3.2 queda intacto como inventario previo y no se invoca anidado. Cobertura suficiente y controles concretos de V1_VERIFIED/TARGET_PREPARED/TARGET_CONFIRMED siguen pendientes; COMPATIBLE A3.1 no certifica toda V1. |
| Recomendación provisional | Campos explícitos para request y snapshots, comparados con JSON, hash y reconstrucción solo por eventos. No tipos/longitudes/nulidad/colaciones/FKs/constraints SQL/on_delete definitivos; analizar representabilidad frente a API pura sin máximos especulativos. |
| Propuesta física no definitiva | Evaluar UNIQUE(profile, after_revision): evita revisiones duplicadas, pero no garantiza secuencia, causalidad o atomicidad. No sustituye reglas puras ni autoriza constraints/migración. |
| Dependencias externas | Core/P5: identidad/participación canónica del operador, autorización, ciclo de vida, retención, privacidad y on_delete. CASCADE, PROTECT e identidad histórica separada son alternativas para consulta, ninguna elegida. Henry/consumidores conservan dependencias. |

[Contrato de persistencia](contracts/ecomotor-classification-persistence-v1.md)
concentra campos candidatos, reconstrucción, alternativas, flujo, evidencia y tests.
[Propuesta Core/P5](contracts/ecomotor-classification-core-boundary-v1.md) identifica
CORE-A3.3-IDENTITY/AUTH/LIFECYCLE/RETENTION/PRIVACY y distingue puertas de esquema
y servicio. [Pendientes](pending-decisions.md#19-a34--puertas-de-persistencia-y-servicio).

Orden orientativo: documentación → acuerdos Core/P5 → evidencia/cobertura →
modelos/migraciones sin backfill tras acuerdos → servicio/tests → integración y
ensayos con Core/Henry/consumidores → migración/activación autorizadas. Sin código,
clasificación real o tests Django ejecutados aquí. S3 V1 sigue como único escritor;
no cambian A3.1/A3.2, reglas puras, ATR-OBJ-01, historiales o contratos V1.

## A3.6 · Evidencia vigente y condiciones de clasificación · 20/10/2026

**Aprobación técnica interna del Equipo 5 en 02C**, documentada sobre develop
`bccc6175ee1751073d8f610d28e99c97da1aad05`, tras arquitectura A3.4 (#67) y reglas
puras A3.3 (#66). DAR3 sigue principal; no se atribuyen estas decisiones técnicas
a DAR3, Óscar/Core o Henry. Se conserva la autoridad/fecha de los antecedentes.

| Identificador | Dirección aprobada y límite |
| --- | --- |
| A3.6-FRESH-01 | Operación nueva: comprobar datos necesarios dentro de la transacción que confirma política/evento, mismo alias confiable, D-19/BEGIN IMMEDIATE/timeout 5 s, rollback conjunto y sin I/O externo. Diagnóstico previo no garantiza vigencia ni lectura actual implica suficiencia. Lector interno específico como dirección, API/consultas aún pendientes; A3.2 intacto y no anidado. |
| A3.6-COVERAGE-01 | Aprobar condiciones por operación del contrato canónico: altas confiables por procedencia, verificación V1 suficiente, compatibilidad objetivo/consumidores y condiciones de migración/corte. Bloqueo por incidencia autorizada sin exigir avance; recuperación con bloqueo íntegro y validación nueva; replay con autorización/contenido/integridad propios. No es lista exhaustiva de consultas. Cobertura verificable de V1_VERIFIED/TARGET_PREPARED/TARGET_CONFIRMED pendiente con propietarios; COMPATIBLE no clasifica ni certifica integralmente puntos/niveles/especializaciones/rangos/Duckies. |
| A3.6-GATE-01 | No confirmar operación nueva sin evidencia requerida/suficiente/vigente, autorización, condiciones externas obligatorias o coherencia de política/historial/revisión. Replay conserva A3.3, evento primero y resultado histórico sin mutación ni nueva elegibilidad. TARGET_CONFIRMED no activa XP; S3 V1 sigue único escritor. Sin migración o clasificación automática. |

[Contrato de evidencia](contracts/ecomotor-classification-evidence-v1.md) concentra
las nueve filas de cobertura, límites, transacción, dependencias y pruebas futuras;
[pendientes](pending-decisions.md#20-a36--cobertura-y-protocolo-de-evidencia-pendientes).
A3.5 sigue abierto: [consulta Core/P5](contracts/ecomotor-classification-core-boundary-v1.md)
sin respuestas/ratificación de identidad, autorización, ciclo de vida, retención,
privacidad u on_delete. No se modifica ese documento ni se aprueban permisos.

Pruebas futuras: evidencia obsoleta/actual/incompleta, bloqueo sin avance,
recuperación validada, replay sin nueva elegibilidad, concurrencia/rollback/eventos
parciales, aislamiento y regresión S3 sin migración o XP objetivo. Sin código,
modelos, servicios o tests nuevos/ejecutados; no se activa el objetivo.

## A3.6.1 · Verificaciones locales V1 · 20/10/2026

**A3.6.1-V1-LOCAL-01**, aprobada internamente por Equipo 5 en 02C sobre develop
`959b102a608883373b7dd0f8e62a65dffe5c7df4`. Precisa parcialmente A3.6-COVERAGE-01;
DAR3 conserva autoridad funcional. No es aprobación del profesor/Core o Henry
ni certificación de cobertura suficiente para V1_VERIFIED.

Se revisaron modelos Users/Ecomotor, auditor A3.1, extractor A3.2 y servicios
S2-A/S3/S1/S7-A/S11-A. [Matriz canónica](contracts/ecomotor-classification-evidence-v1.md#71-matriz-de-evidencia-código-existente-y-límites)
separa para perfil, stats, XPEvent, EvolutionEvent, progresión, StatAllocationEvent
y especializaciones: verificaciones implementadas, verificaciones posibles con
filas actuales aún sin lector A3.6 y límites de información histórica persistida.
Los servicios existentes validan operaciones propias, no auditan integralmente
ni deben invocarse para escribir durante una supuesta comprobación de lectura.

Resultados conceptuales por comprobación: superada, evidencia insuficiente o
incoherencia detectada. No nuevos enums/TransitionState/LegacyAuditStatus ni
conversión COMPATIBLE → V1_VERIFIED. Datos incompletos no prueban igualdad,
completitud o incoherencia global; no fabricar eventos/snapshots/procedencias.

A3.6-FRESH-01/D-19 y replay A3.3 siguen intactos. Pendientes completitud XP,
origen/gasto de puntos, atributos históricos de etapas, historia de especialización/
dominio/rangos, Duckies/Henry, procedencia confiable y cobertura final V1_VERIFIED.
A3.5/Core conserva identidad, autorización, retención, privacidad y on_delete.
[Pendientes](pending-decisions.md#21-a361--límites-de-verificación-local-v1).
Sin lector, modelos, servicio, clasificación real, reparación/backfill o activación;
pruebas de casos locales y vigencia/replay documentadas como futuras, no ejecutadas.

## A3.6.2 · Contrato del lector transaccional V1 · 20/10/2026

**Aprobación técnica interna Equipo 5 en 02C**, sobre develop
`1c03e6493ae871e08243eccbcfe154b724a106a9`. Desarrolla A3.6/A3.6.1;
DAR3 conserva autoridad funcional y no se atribuye ratificación a Óscar/Core/Henry.

| Identificador | Acuerdo interno y límite |
| --- | --- |
| A3.6.2-READER-01 | Servicio controla transacción D-19 y lector trabaja dentro, sin transacción propia, escritura, otro alias, servicios escritores, A3.2 anidado o I/O externo. IMMEDIATE/timeout 5 s y rollback; in_atomic_block no acredita por sí solo contexto confiable. Mecanismo definitivo pendiente, sin row locking o atomicidad entre BD independientes supuestos. |
| A3.6.2-INPUT-01 | Perfil local, alias validado/autorizado, plan de comprobaciones confiable servidor y contexto transaccional: entradas conceptuales, no firma/clases definitivas. Cliente no omite verificaciones. Operador/permisos del servicio dependen de A3.5; lector no decide transiciones. |
| A3.6.2-RESULT-01 | Resultado inmutable propuesto con perfil/ámbito, solicitado/realizado, cobertura/limitaciones y diagnósticos de las tres categorías A3.6.1. Sin enums nuevos, verified=True global o V1_VERIFIED; fallos no son cobertura total. Datos sensibles/claves sin exposición indiscriminada. |
| A3.6.2-ERROR-01 | Diferenciar perfil inválido/inexistente, alias/contexto no confiable, BD/timeout, acceso indebido/referencias cruzadas, insuficiencia e incoherencia. Separar fallo que aborta lectura de diagnóstico representable de comprobación completa; no confundir ausencia con corrupción o fallo técnico con éxito. Excepciones definitivas pendientes. |

[Contrato central](contracts/ecomotor-classification-evidence-v1.md#8-a362--contrato-conceptual-del-lector-transaccional-v1)
concreta flujo, límites y pruebas futuras. A3.3 conserva evento primero y replay
sin nueva elegibilidad: lector solo verifica operaciones nuevas. Siete grupos
locales no son lista universal; suficiencia V1_VERIFIED y procedencia siguen abiertas.
A3.5/Core mantiene cinco preguntas sin responder y on_delete pendiente, documento
intacto; Henry conserva coordinación de referencias/consumidores.
Sin API Python definitiva, lector, modelos, servicios, tests nuevos o activación.
S3 V1 sigue único escritor. Pruebas documentadas como futuras, no ejecutadas.
[Pendientes](pending-decisions.md#22-a362--detalle-del-lector-y-dependencias).

## A3.6.3 · Criterios de suficiencia V1 · 20/10/2026

**Aprobación arquitectónica interna Equipo 5 en 02C**, sobre develop
`080849ee207c05f844d5ccfd1624ab270d1d5a3a`. DAR3 sigue principal; no son requisitos
literales nuevos ni acuerdos ratificados por Óscar/Core o Henry. Precisa condiciones
necesarias para estudiar PENDING_REVIEW → V1_VERIFIED, sin cerrar suficiencia final.

| Identificador | Acuerdo y límite |
| --- | --- |
| A3.6.3-MIN-01 | Controles locales necesarios según procedencia/aplicabilidad: perfil, stats, XP observable, causalidad de evoluciones, progreso frente a catálogo V1 validado/aplicable, gastos disponibles y selección/progresos. No son suficiencia automática ni exigen eventos o especialización cuando su ausencia sea legítima; no demostrar historia con catálogo actual sin aplicabilidad acreditada. |
| A3.6.3-GAPS-01 | Evidencia suficiente de condición examinada, insuficiencia de prueba obligatoria o incoherencia observable son situaciones distintas. Insuficiencia/incoherencia impiden avance nuevo sin mutar clasificación previa o crear evento de transición. No BLOCKED automático, historia ficticia o cronología PK. Política exacta de lagunas admisibles bajo garantías alternativas sigue pendiente, sin excepción general; COMPATIBLE no basta. |
| A3.6.3-NATIVE-01 | Legacy requiere procedencia acreditada e historia observable con lagunas explícitas; nativo V1 exige alta confiable/verificada, sin exigir historia antigua inexistente. No inferir origen por XP/fecha/nivel/historial vacío, reclasificar existentes o cambiar procedencia confirmada. S2-A no certifica retrospectivamente todos los perfiles; acreditación exacta del proceso creador pendiente. |
| A3.6.3-TIME-01 | Verificación confirmada acredita condiciones en su transacción. XP S3 posterior no revoca/actualiza clasificación, revisión o eventos automáticamente, sin prometer coherencia perpetua. Transiciones futuras requieren evidencia/permisos propios; diagnóstico no deduce BLOCKED. S3 V1 continúa único escritor. |

[Contrato canónico](contracts/ecomotor-classification-evidence-v1.md#9-a363--criterios-locales-necesarios-para-v1_verified)
centraliza matriz, lagunas, procedencia, temporalidad y pruebas futuras;
[pendientes](pending-decisions.md#23-a363--suficiencia-lagunas-y-procedencia-pendientes).
A3.3/A3.6.2, D-19, evento primero/replay y A3.2 separado permanecen intactos.
A3.5/Core/Henry y cobertura final siguen abiertos. Sin API definitiva, modelos,
lector, servicios, migraciones o tests nuevos/ejecutados. Antecedentes conservados.

## A3.6.4 · Lagunas históricas y garantías alternativas · 20/10/2026

**Aprobación arquitectónica interna Equipo 5 en 02C**, sobre develop
`8790ac7ddd9703d2d3686038e87f01d814358419`. Continúa A3.6.1–A3.6.3; DAR3 sigue
principal. No son requisitos literales nuevos ni acuerdos de Óscar/Core o Henry.

| Identificador | Acuerdo y límite |
| --- | --- |
| A3.6.4-GAP-01 | Evaluar cada laguna: condición, historia ausente, evidencia directa, fuentes alternativas existentes/candidatas e impacto. Separar ausencia legítima, historia incompleta, prueba obligatoria insuficiente y contradicción. Sin corrupción inferida, cronología PK o eventos inventados; COMPATIBLE no es V1_VERIFIED. |
| A3.6.4-ALT-01 | Alternativa solo podría acreditar la misma condición obligatoria con garantías suficientes: perfil inequívoco, procedencia, cobertura, tiempo, coherencia, independencia probatoria y validación/autorización propietaria. Ejemplos son hipótesis no constatadas ni admitidas; no equivalencia por parecido o estado actual circular. |
| A3.6.4-GATE-01 | Si condiciones obligatorias acreditadas y resto de requisitos cumplidos, evaluación puede continuar. Laguna no obligatoria solo bajo política aprobada puede no impedirla. Prueba obligatoria ausente sin alternativa admitida/suficiente, o incoherencia impeditiva: rechazo sin mutar estado/revisión/historial ni nuevo evento confirmado. No excepción genérica, BLOCKED automático, reparación o migración. Política concreta de admisibilidad pendiente. |
| A3.6.4-TRACE-01 | Justificar uso futuro mediante condición, laguna, fuente/procedencia, alcance, vigencia/aplicabilidad, resultado motivado y límites; distinguir examen de evidencia de autorización. No aprueba campos/modelos/tablas/firmas/formato/retención; privacidad, conservación e identidad del operador pendientes A3.5/Core. |

[Contrato canónico](contracts/ecomotor-classification-evidence-v1.md#10-a364--lagunas-históricas-y-garantías-alternativas)
centraliza ejemplos, criterios, puerta de avance y pruebas futuras;
[pendientes](pending-decisions.md#24-a364--admisibilidad-y-equivalencias-pendientes).
Lista de lagunas, fuentes disponibles/confiables, equivalencias específicas y
suficiencia final V1_VERIFIED siguen abiertas, al igual que procedencia, lector y
Core/Henry. PR #61 no resuelve esas dependencias técnicas; consulta Core intacta.
A3.3/replay y D-19 conservados, sin I/O externo transaccional o A3.2 anidado.
Sin código, modelos, servicios, clasificación real, migraciones o tests nuevos/
ejecutados. S3 V1 continúa único escritor; antecedentes conservados.

## A4.1 · Validación pura de estadísticas objetivo · 21/10/2026

**Aprobación interna Equipo 5 en 02C**, sobre develop
`0e960de432cc08d62933d8218586ae114dad9949`. DAR3 sigue principal; ATR-OBJ-01 es
decisión interna. No atribuir al profesor aprobación de tipos/esquemas Django,
configuración oficial o valores numéricos. Se conservan E-01/E-02 y OP-RED-01.

| Identificador | Acuerdo y límite |
| --- | --- |
| A4.1-ATTR-01 | Exactamente ATK Ataque, DEF Defensa, VEL Velocidad, INT Inteligencia, LOG Lógica y CUACK Especial / Especialización. Sin SPE adicional objetivo; V1 permanece intacto. |
| A4.1-BASE-01 | Bases explícitas autorizadas por opción y seis claves exactas, sin defaults. Tipos apropiados sin booleanos; valores oficiales, dominio base y límites/reglas adicionales pendientes. Comprobar estructura no acredita autorización funcional de una fuente. |
| A4.1-BUDGET-01 | Seis incrementos enteros no negativos y presupuesto entero no negativo, sin bool. Suma dentro del presupuesto, puntos sin gastar permitidos; efectivas=bases+incrementos, utilizados/restantes y entradas validadas sin mutación. Presupuesto independiente por configuración, no saldo consumido de otros Duckies. |
| A4.1-PURE-01 | Validación/cálculo puro determinista separado de BD, permisos y selección; sin perfiles/estados/eventos, transacciones o concesiones XP/puntos/monedas. Servicios persistentes futuros sujetos a 02C/Core. No reinterpreta V1 ni activa objetivo. |

[Contrato canónico](contracts/ecomotor-target-stats-validation-v1.md) centraliza
entradas/resultados, errores, límites y tests futuros; [pendientes](pending-decisions.md#25-a41--parámetros-y-dependencias-del-validador-objetivo).
No bases, presupuesto o límites oficiales inventados; ejemplo 45 no autorizado.
V1 conserva log_stat Logística y spe Especial / Especialización, servicios e historia.
Sin código, modelos, migraciones, servicios o tests nuevos/ejecutados; posterior
implementación pura en 01B. No se activa A2 ni se modifica S3 V1.

## A4.1-NUM-01 · Dominio numérico y concreción pura 01B · 21/10/2026

**Aprobación técnica interna del Equipo 5 en 02C**, comunicada por Jaime el
21/10/2026, posterior al contrato integrado mediante PR #73 sobre develop
`693f41d5ab012591b4b89d79239d000983072b6e`. DAR3 conserva autoridad funcional;
esta decisión no atribuye al profesor cifras oficiales, presupuesto, esquemas
o autorización de configuración. El registro A4.1 anterior se conserva como
antecedente: su incertidumbre sobre el dominio numérico básico queda resuelta.

**A4.1-NUM-01:** bases, incrementos y presupuesto son enteros Python exactos no
negativos (`type(value) is int`, valor >= 0). Rechazar bool, float, Decimal,
cadenas y tipos incompatibles sin convertir, redondear, truncar o completar.
Efectivas = bases + incrementos; utilizados = suma de incrementos; restantes =
presupuesto - utilizados, con suma <= presupuesto. Gasto completo, parcial o cero
permitido, por configuración independiente. Sin máximos funcionales inventados
ni límites técnicos de almacenamiento impuestos en esta capa pura.

**Concreción técnica de implementación en 01B, no nueva regla funcional:**
`validate_target_stats(bases, increments, *, budget) -> TargetStatsResult`;
listas/tuplas explícitas de pares permiten rechazar duplicados antes de colapsar
claves. Solo ATK, DEF, VEL, INT, LOG y CUACK, una vez cada una. Resultado frozen/slots
con tuplas canónicas y copias defensivas; construcción directa también valida
sus invariantes. Sin modelos, persistencia, cambios V1 o activación del objetivo.

[Contrato técnico](contracts/ecomotor-target-stats-validation-v1.md) y
[pendientes reales](pending-decisions.md#25-a41--parámetros-y-dependencias-del-validador-objetivo):
bases y presupuesto oficiales, posibles límites adicionales, fuente/versionado,
consumidores, integración y Core siguen abiertos. **45 no es presupuesto oficial.**

## A4.2 · Configuración autorizada de estadísticas objetivo · 21/10/2026

**Aprobación técnica interna Equipo 5 en 02C el 21/10/2026**, sobre develop
`13f0c5a2dff0c94b1e81939bfe50d0ed4b73a8e2`. DAR3 conserva autoridad funcional;
aclaraciones del profesor no aprueban automáticamente estos mecanismos, cifras
oficiales o esquemas Django. A4.1/NUM-01 integrada por #74, sin cambios de API.

| Identificador | Acuerdo y límite |
| --- | --- |
| A4.2-SPLIT-01 | Definición de seis bases por opción con referencia/versiones separada del presupuesto inicial fijo autorizado del jugador. Independiente por configuración, no saldo global agotable ni necesariamente campo de cada definición. Puntos pendientes permitidos; sin presupuestos por época/bonificaciones/puntos nuevos de nivel. |
| A4.2-ID-01 | Distinguir opción objetivo, catálogo objetivo, versión de catálogo y versión de definición, sin igualar ambas versiones. Códigos definitivos pendientes, nombres visibles no obligatorios. A3-CAT-01 preserva catálogo separado de EvolutionStage V1; no tablas/FKs/índices/SQL o migración implícita. |
| A4.2-TRUST-01 | Estructura válida no acredita autorización funcional. A4.1 y futuro A4.2.1 no certifican procedencia/publicación/vigencia. Frontera servidor posterior con catálogos/Core/E5, sin fuente autorizada implementada; texto/versión cliente o bool declarativo no bastan. |
| A4.2-SNAPSHOT-01 | Primera configuración futura conserva seis bases autorizadas, referencia/procedencia de definición, incrementos y presupuesto según 02C; no reinterpretar configuraciones al cambiar catálogo. Campos/formato/reglas de actualización/conservación/eliminación pendientes. Sin modelos/eventos nuevos; estado/stats jugables siguen futuros. |
| A4.2-CONSUME-01 | Consumidores obtienen estadísticas desde Ecomotor: opción efectiva, seis efectivas, configuración/versión y revisión/coherencia pertinentes. Consulta coherente de lectura, sin selección/puntos; permisos/contexto con Core. Sin endpoint/JSON/firma/token/UI definitivos ni autoridad arbitraria del juego. |

[Contrato central A4.2](contracts/ecomotor-target-stats-config-v1.md) concentra
responsabilidades, A4.1 integrada, A4.2.1 futura, límites y pruebas;
[pendientes](pending-decisions.md#26-a42--configuración-confianza-y-consumidores-pendientes).
Ducky físico actual es unívoco por User; opciones Ecomotor no crean múltiples
Duckies físicos. Henry conserva apariencia/inventario/equipamiento; Core, identidad,
políticas y contexto. Sin modificar sus documentos/esquemas o asumir sus contratos.
A4.2.1 queda para 01B sin BD/efectos, API concreta por definir. Sin código,
modelos/migraciones, servicios persistentes, tests nuevos/ejecutados o activación.
S3 V1 sigue único escritor XP; antecedentes conservados.

## A4.3 · Preparación pura de configuraciones objetivo · 21/10/2026

**Aprobación técnica interna Equipo 5 en 02C el 21/10/2026**, sobre develop
`e612ed5cba8dfcd1e661649ff9f8459b9f4fb7fa`. DAR3 sigue principal; no atribuir al
profesor aprobación de APIs, cifras, modelos Django o mecanismos de autorización.
A4.1 (#73/#74) y A4.2/A4.2.1 (#75/#76) integradas; sus previsiones de implementación
anteriores conservan su valor histórico. A4.3.1 no implementada.

| Identificador | Acuerdo y límite |
| --- | --- |
| A4.3-PREP-01 | Preparar con definición A4.2.1 válida/inmutable, seis incrementos y presupuesto explícito; reutilizar A4.1 sin duplicar reglas. Propuesta completa canónica/inmutable con opción/catálogo/versiones/bases/reparto/presupuesto/utilizados/restantes/efectivas. Presupuesto independiente y separado; propuesta válida no autoriza ni confirma. |
| A4.3-BOUNDARY-01 | Separar preparación pura, resolución autorizada por servidor y confirmación persistente propietaria. Versión/contexto cliente, definición válida, presupuesto navegador, bool o propuesta calculada no demuestran autorización. Sin certificados/tokens/contextos físicos o mecanismo definitivo de obtención. |
| A4.3-VERSION-01 | Preservar opción/catálogo, versiones distintas y seis bases; versiones no acreditan autenticidad. Confirmación futura conservará bases/procedencia según A4.2-SNAPSHOT-01 sin recálculo silencioso; catálogo objetivo separado A3-CAT-01. Sin campos/tablas/relaciones o políticas nuevas. |
| A4.3-FAIL-01 | Rechazar entradas incompletas/incompatibles/inconsistentes sin efectos, mutación o defaults. Confirmación futura valida vigencia/elegibilidad/referencias/estado en su frontera correspondiente; no se inventa concurrencia/replay/actualización para A4.3.1. |

[Contrato central](contracts/ecomotor-target-stats-preparation-v1.md) concentra
resultado, fronteras, responsabilidades y tests futuros; [pendientes](pending-decisions.md#27-a43--preparación-y-fronteras-pendientes).
Firma/errores/resultado concretos del preparador se revisarán en 01B. Óscar conserva
parámetros funcionales oficiales, Core contexto/políticas/A3.5, Henry apariencia/
inventario y otros equipos contratos consumidores; ninguno ratificado por inferencia.
Sin código, persistencia, endpoints o activación; APIs A4.1/A4.2.1 y V1 intactos.
No se ejecutan nuevos tests Django en esta PR documental. S3 V1 único escritor XP.

## DOC-Aclaraciones-20/10 · Presupuesto, vestimentas y membresías · 21/10/2026

Registro del 21/10/2026, sobre develop `780c967e8b8913e318775fa479636e19bf6dfeba`.
Procedencia: precisiones comunicadas por Jaime en 02C tras revisar las aclaraciones
funcionales de Óscar del 20/10. Se conserva la trazabilidad de la conciliación
anterior, sin afirmar nueva consulta directa al documento compartido o a DAR3.
DAR3 sigue como fuente funcional principal; se distinguen las siguientes autoridades.

**A4-PRESUPUESTO-PROV-01 · Decisión interna provisional del Equipo 5:** utilizar
**45 puntos de reparto inicial por opción jugable**, de forma independiente e
igual para cada opción, sin saldo global consumible. Reparto completo, parcial o
cero permitido conforme a A4.1. El valor permite avanzar y es revisable si se
confirma otro presupuesto o aparecen inconsistencias funcionales; no procede de
Óscar ni de DAR3. Las referencias anteriores a 45 como ejemplo se conservan como
antecedentes, precisados por esta adopción interna posterior, sin convertirlo en
valor oficial del profesor. Las seis bases y reglas adicionales siguen pendientes.

Sin defaults implícitos ni cambios de API/comportamiento en A4.1, A4.2.1 o A4.3.1;
utilizar 45 no autoriza por sí solo una configuración. Si en el futuro existen
configuraciones persistentes, cualquier cambio de presupuesto exigirá política
expresa de versionado y tratamiento de las confirmadas, sin recálculo silencioso.

**Aclaración funcional y recursos pendientes:** Óscar confirmó una imagen de
vestimenta completa por época. Según la información actual comunicada en 02C,
las imágenes definitivas aún no se han entregado al Equipo 5. Su recepción es
dependencia gráfica; no bloquea evolución/estadísticas puras ni acredita integración
visual completada. Henry conserva avatar y representación de apariencia. Se mantiene
uso de vestimenta vigente durante progresión histórica y reutilización de anteriores
desbloqueadas tras elegir especialización, sin ampliar adquisición/equipamiento.
Los recursos gráficos históricos de Classroom no prueban esta entrega definitiva.

**Membresías:** User funcional (acceso visual previo a entrar) es distinto del
modelo User estándar Django utilizado actualmente. Free, Plus y Pro están
confirmadas funcionalmente, pero no implementadas aquí como niveles de membresía;
el modelo Django no demuestra implementación de las cuatro categorías. Core debe
acordar representación, asignación, cambios, permisos y condiciones de acceso.
Beneficios adicionales de DuckyCoins siguen sin cifras/fórmulas aprobadas.
Permanece el conflicto Training 2 XP Free / 5 XP Plus-Pro frente a igualdad de XP
por la misma actividad elegible confirmada por Óscar; sin elegir nuevas cifras.

[Pendientes y propietarios](pending-decisions.md#28-precisiones-2010--presupuesto-recursos-y-membresías),
[coordinación candidata](contracts/integracion-equipo5-v0.md#03-precisiones-posteriores--presupuesto-recursos-y-membresías),
[bases/presupuesto](contracts/ecomotor-target-stats-config-v1.md#11-presupuesto-provisional--precisión-posterior)
y [opciones objetivo](contracts/ecomotor-playable-options-target-v1.md#10-precisiones-posteriores--presupuesto-y-recursos).
Sin implementación, cambios V1 o activación: S3 V1 sigue único escritor XP.
A4.4 queda fuera de este incremento y se documentará en otra PR.

## A4.4 · Resolución confiable de estadísticas objetivo · 21/10/2026

**Arquitectura interna aprobada por Equipo 5 en 02C el 21/10/2026**, comunicada
por Jaime, sobre develop `529e6a03a8c97d745ffbeadc9da3c67b83edafd3`. DAR3 conserva
autoridad funcional; no se atribuyen a Óscar decisiones técnicas, nuevas cifras,
APIs o modelos. Se usa trazabilidad existente, sin nueva consulta directa de fuentes.
A4.1 #74, A4.2.1 #76 y A4.3.1 #78 integradas; las previsiones anteriores conservan
su fecha y significado histórico. #79 integra el presupuesto provisional interno.

| Identificador | Acuerdo y límite |
| --- | --- |
| A4.4-SOURCE-01 | Separar resolución y fuentes: configuración versionada servidor, catálogo Django o servicio externo si se acuerda su necesidad son alternativas, sin elegir implementación física. Requiere autoridad de publicación acordada; almacenamiento servidor o fixtures sintéticos no acreditan aprobación oficial. |
| A4.4-INPUT-01 | Petición podrá incluir opción/seis incrementos. Servidor obtiene/verifica identidad, permisos, contexto, definición/bases/presupuesto/versiones; cliente no impone estos últimos ni pertenencia o autoridad por bool. Sin firmas/endpoints/auth definitivos. |
| A4.4-RESOLVE-01 | Verificar opción/pertenencia a catálogo autorizado, identidades/versiones, estado/aplicabilidad de definición, presupuesto y elegibilidad/contexto cuando correspondan; reutilizar A4.2.1/A4.3.1. Contexto estructural no certifica confianza; resolver no confirma persistencia. |
| A4.4-LIFECYCLE-01 | Primera configuración usa bases autorizadas aplicables; redistribución conserva bases confirmadas; cambio usa configuración propia confirmada; lectura coherente usa estado efectivo/configuración persistida. Sin vigencia uniforme impuesta; retiradas/sustituidas/antiguas pendientes. A4.2-SNAPSHOT-01/A3-CAT-01 conservados, sin esquema físico. |
| A4.4-FAIL-01 | Rechazo sin efectos si falta fuente autorizada/bases/presupuesto, incompatibilidad o elegibilidad no acreditada. Sin defaults, versiones alternativas silenciosas, flags cliente, confirmaciones parciales o reparación de historia. Frontera transaccional futura con servicios/A3/Core. |

[Contrato canónico](contracts/ecomotor-target-stats-resolution-v1.md) y
[pendientes](pending-decisions.md#29-a44--resolución-confiable-y-dependencias).
A4-PRESUPUESTO-PROV-01 se conserva: 45 por opción, independientes, gasto total/
parcial/cero, parámetro de desarrollo interno revisable; presupuesto definitivo
y autorización real separados. Sin budget implícito ni cambios de validadores.
A4.4.1 es candidato a frontera cerrada por defecto; revisar utilidad en 01B antes
de implementar, sin simular confianza con proveedores de prueba o certificados.
Fuentes reales, bases oficiales, ciclo de definiciones, Core/A3.5, Henry,
consumidores y persistencia siguen abiertos. Sin código, tests Django ejecutados,
modelos, migraciones o activación. S3 V1 sigue único escritor XP; no activar A2.

## A3.5 · Propuestas internas para Core · 21/10/2026

**Dirección arquitectónica aprobada internamente por Equipo 5 en 02C el 21/10/2026**,
comunicada por Jaime, sobre develop `3f140da0f53596fff429553641ac81b5f82ce6de`.
No son respuestas de Óscar/Core ni autorización de modelos/migraciones. DAR3
conserva autoridad funcional; estas propuestas técnicas no son requisitos literales
nuevos del profesor. Antecedentes A3.3/A3.4/A3.6 y preguntas originales preservados.

| Identificador | Dirección interna preferida, pendiente de compatibilidad/confirmación Core |
| --- | --- |
| CORE-A3.3-IDENTITY | Separar perfil/operador, contexto servidor confiable y atribución histórica original; representación, procesos y comparación canónica pendientes. |
| CORE-A3.3-AUTH | Administradores/procesos internos expresamente autorizados por operación, incluido replay; clave conocida no autoriza. Permisos e integración Core pendientes. |
| CORE-A3.3-LIFECYCLE | Evitar destrucción silenciosa de evidencia necesaria; conservación/anonimización/supresión acordadas con Core, sin elegir on_delete. |
| CORE-A3.3-RETENTION | Sin limpieza automática de eventos en primera versión; evidencia mientras sea legítimamente necesaria. Sin plazos ficticios/perpetuidad ni impedir eliminación Core; tratamiento definitivo pendiente. |
| CORE-A3.3-PRIVACY | Acceso mínimo, no exposición innecesaria, atribución protegida y límites explícitos de reconstrucción/replay tras supresión/anonimización; integración Core pendiente. |

[Respuesta canónica y residuales por pregunta](contracts/ecomotor-classification-core-boundary-v1.md#6-a35--respuestas-preferidas-del-equipo-5--21102026)
y [pendientes](pending-decisions.md#30-a35--preferencias-internas-y-acuerdos-externos-pendientes).
Las cinco preguntas siguen visibles e intactas; elegir una preferencia interna no
cierra operador, permisos, eliminación/conservación/privacidad, on_delete o esquema.
Sin nuevos campos/FKs, modelos, migraciones, backfill, cambios de idempotencia/
replay o activación. S3 V1 sigue único escritor XP; no modificaciones de otros equipos.

## A4-DEMO-01 · Demostración local de reparto · 21/10/2026

**Aprobada internamente por Equipo 5 en 02C**, comunicada por Jaime. Implementación
en PR para revisión, sobre develop 22e979e; no integrada hasta merge autorizado.
DAR3 conserva autoridad funcional; no implica aprobación de Óscar/Core/Henry.

Pantalla Django anónima y sin persistencia, habilitada exclusivamente por settings
y URLconf de demo en /demo/ecomotor/, con servidor ligado explícitamente a
127.0.0.1. Cinco etiquetas tecnológicas (Developer, Ciber, Sistemas, Data IA,
Gamer), seis incrementos ATK/DEF/VEL/INT/LOG/CUACK y botón Comprobar reparto.
Validación HTTP estricta, sin duplicados ni parámetros de autoridad, y CSRF real.

Reutiliza A4.1 con seis ceros sintéticos como bases técnicas y DEMO_BUDGET=45
en servidor; muestra solo opción y puntos gastados/restantes. No muestra bases
ni efectivas definitivas. A4-PRESUPUESTO-PROV-01 es una decisión separada:
presupuesto provisional interno, no oficial del profesor. No define catálogos,
selección real, autorización, sesión de jugador o activación del objetivo.

Sin cambios V1, Core, Duckies, modelos/migraciones, configuración global o
INITIAL_CONFIGURATION. Bases oficiales, resolución confiable y Core/A3.5 siguen
pendientes. [Contrato local](contracts/ecomotor-target-stats-demo-v1.md).

## A4.4.1 · Concreción interna de frontera cerrada · 21/10/2026

Traspaso aprobado internamente en 02C, comunicado por Jaime; concreta el mínimo
de A4.4, sin reabrir ni duplicar SOURCE/INPUT/RESOLVE/LIFECYCLE/FAIL-01. Implementación
en PR para revisión sobre 706181d; no integrada antes del merge autorizado.

resolve_target_stats_configuration(*, option_code, increments) siempre rechaza
con TargetStatsSourceUnavailableError mientras no exista fuente confiable integrada
y aprobada. Ningún proveedor inyectable, flag, presupuesto, bases o versión del
llamador suplanta esa autoridad. Sin I/O, BD o llamada al preparador en el rechazo.

Ensayo privado _prepare_untrusted_resolution_candidate, no conectado a la entrada
real: recibe definición/incrementos/presupuesto sintéticos explícitos, delega en
A4.3.1 y compara la opción exacta; devuelve solo propuesta pura sin autorización.
Sin proveedores ficticios de producción, nuevas dataclasses de confianza, fallback
a A4-DEMO-01, presupuesto 45 o bases cero. Errores originales preservados.

DAR3 mantiene autoridad funcional; no aprobación adicional de Óscar/Core/Henry.
Fuente real, publicación/vigencia/elegibilidad, parámetros oficiales, Core/A3.5,
Henry, consumidores y confirmación persistente siguen pendientes. APIs anteriores,
demo y S3 V1 intactos; sin migraciones, persistencia o activación.
[API, errores y límites](contracts/ecomotor-target-stats-resolution-v1.md#9-a441--frontera-mínima-y-ensayo-estructural).

## A3-CAT-EVENT-01 · Separación de eventos objetivo · 21/10/2026

**Aprobada internamente por Equipo 5 en 02C**, comunicada por Jaime; registro sobre
develop ca77b43cc9b1ddb2d44a3edf3cac5c22e3b3cba1. Decisión técnica local, no requisito
literal DAR3 ni aprobación externa de Óscar, Core o Henry.

Conservar EvolutionStage/EvolutionEvent V1, referencias y comportamiento. Catálogo
objetivo separado, versionado e inmutable una vez utilizado; eventos de evolución
objetivo separados de EvolutionEvent V1. Cada evolución conservará causa XP
verificable, perfil correspondiente e identidad histórica de época/versiones.
Cada época cruzada origina un evento, sin duplicados; replay no añade XP ni
evoluciones. Nivel 8 desbloquea elección, no octava época. Sin reinterpretación,
renombrado o migración silenciosa V1.

Precisa A2-EVO-01 sin reescribir su historia: la obligación de registrar todos los
cruces se cumple con eventos objetivo separados. Se mantiene (profile, operation_key),
XP acumulativa, un evento XP por concesión nueva, causalidad, escritor único,
atomicidad/concurrencia D-19, rechazo de incoherencias y ausencia de puntos por nivel.
No trasladar restricciones físicas V1 al objetivo por inferencia.

[Detalle conceptual A3-CAT](contracts/ecomotor-transition-target-v1.md#a3-cat-event-01--separación-de-eventos-objetivo)
y [conciliación A2](contracts/ecomotor-target-xp-v1.md#5-progresión-y-eventos-causales--a2-evo-01).
Pendientes: modelo del catálogo, nombres/campos/claves/restricciones y relaciones
de eventos con XPEvent/perfiles/épocas/versiones, consulta histórica conjunta,
conservación/supresión/on_delete Core/A3.5, EvolutionItem/vestimentas con Henry,
publicación y umbrales autorizados, migración y activación coordinada.
Sin código, modelos, esquemas físicos, migraciones ni servicio XP objetivo persistente.

## A3-CAT-PHYS-01 · Diseño mínimo del catálogo objetivo · 21/10/2026

**Aprobado internamente por Equipo 5 en 02C**, comunicado por Jaime, sobre develop
18b6bbd4174cc7325f4511906cb26827d2aafeff. Concreción documental, no modelos implementados
ni aprobación externa de Óscar/Core/Henry. DAR3 conserva autoridad funcional.

Tres modelos candidatos: TargetCatalogVersion (catalog_id/version, únicos juntos;
identidad lógica distinta de PK técnica), TargetLevelThreshold (catálogo, level
positivo, minimum_xp no negativa, únicos catálogo/nivel, sin stat_points_awarded)
y TargetEpoch (catálogo, code/name no vacíos, ordinal 1–7, minimum_xp no negativa;
unicidades catálogo/ordinal y catálogo/code).

Adaptación futura explícita a estructuras A1.1: stat_points_awarded=0 en cada
LevelDefinition, sin persistirlo. A1.1 valida las invariantes de catálogo completo,
no solo por fila ni publicación/autorización. Una versión completa usada no cambia;
crear otra para cambios. Garantía no implementada: concretar protección antes de
implementar físicamente, sin mecanismos o estados de publicación inventados.

[Detalle central, invariantes y límites](contracts/ecomotor-transition-target-v1.md#a3-cat-phys-01--catálogo-objetivo-mínimo-candidato).
Precisa los antecedentes donde el modelo del catálogo seguía pendiente; no altera
A3-CAT-EVENT-01 o A2-EVO-01. Eventos objetivo/relaciones/consulta conjunta, conservación/
supresión/on_delete Core/A3.5, Henry, códigos/umbrales oficiales, publicación, migración
y activación siguen abiertos. V1 intacto; S3 único escritor XP. Sin código ni migración.

## A3-CAT-IMMUT-01 · Protección progresiva del catálogo objetivo

**Aprobada internamente por Equipo 5 en 02C-2 el 21/10/2026**, comunicada por Jaime;
base develop 9b03d3bf485b6d2ca7940b822e6e6544005aca11. No requisito técnico literal
DAR3 ni ratificación externa. Sustituye solo la condición temporal del registro
[A3-CAT-PHYS-01](#a3-cat-phys-01--diseño-mínimo-del-catálogo-objetivo--21102026),
conservado como antecedente: ya no exige protección completa antes de crear la
persistencia preparatoria. Se mantiene preservar versiones históricas utilizadas.

- Fase 1: se permite implementar los tres modelos, restricciones locales de BD,
  validación completa A1.1, migración estructural vacía de datos y tests. Catálogos
  preparatorios sin uso real; no protección contra escrituras directas implementada
  ni versiones declaradas congeladas. Sin escritor XP objetivo, referencias reales
  de progresión, eventos objetivo basados en estas versiones, publicación o activación.
  No campos frozen, published o equivalentes; A1.1 no acredita aprobación de Óscar.
- Fase 2: antes del primer uso real aprobar e implementar congelación transaccional,
  protección física de versión/niveles/épocas ante modificaciones/eliminaciones,
  escrituras directas y concurrencia, y acreditación verificable de versión utilizada.
  Versión completa utilizada inmutable; cambios requieren nueva versión. Triggers
  SQLite concretos y su política no aprobados; garantía todavía no implementada.

[Detalle central y límites](contracts/ecomotor-transition-target-v1.md#a3-cat-immut-01--protección-progresiva-del-catálogo-objetivo).
Campos y unicidades PHYS-01, A3-CAT-EVENT-01, V1/S3 y pendientes Core/A3.5/Henry,
umbrales oficiales, publicación, eventos y activación intactos. Esta PR solo
documenta, sin modelos, migraciones, código o tests nuevos.


## A3-CAT-FREEZE-01 · Congelación del catálogo objetivo · 21/10/2026

**Aprobada internamente por Equipo 5 en 02C-2 el 21/10/2026**, sobre develop
`68f0c1ac415ad741b9ccae1beddadc292c80c2ca`, tras integrar #88. No es un requisito
técnico literal de DAR3 ni aprobación externa de Óscar, Core o Henry.
Desarrolla la fase 2 de [A3-CAT-IMMUT-01](#a3-cat-immut-01--protección-progresiva-del-catálogo-objetivo)
y conserva el antecedente [A3-CAT-PHYS-01](#a3-cat-phys-01--diseño-mínimo-del-catálogo-objetivo--21102026).
La fase 1 (tres modelos, 0006 y lector A1.1) está integrada; la congelación aquí
aprobada **todavía no está implementada**.

- Único campo conceptual nuevo: TargetCatalogVersion.frozen_at, fecha nullable
  generada por servidor. NULL indica versión preparatoria; fecha indica marcada
  como congelada. Sin descongelación; cambios requieren una versión nueva. Sin
  published, active, is_used u otros estados redundantes. La fecha no acredita
  publicación, autorización funcional ni ejecución de A1.1.
- Servicio interno candidato freeze_target_catalog_version(catalog_version_id,
  *, using): identidad técnica exacta y alias, transacción SQLite IMMEDIATE según
  D-19, lectura y validación completa mediante el lector existente/A1.1, y marca
  con hora del servidor. Si ya está congelada, revalidar y devolver el estado
  existente sin cambiar fecha. Error implica rollback, nunca confirmación parcial.
  Respetar la gestión transaccional Django, sin BEGIN manual dentro de una
  transacción activa sin diseñarlo. No publica, activa ni concede XP.
- Protección física aprobada mediante triggers SQLite con RAISE(ABORT): padre
  congelado no se modifica ni elimina; no inserción directa con fecha; NULL→fecha
  solo sin cambiar identidad simultáneamente. Hijos no admiten inserción,
  actualización, borrado o traslado que afecte a una versión congelada, comprobando
  OLD.catalog_id y NEW.catalog_id cuando corresponda. No se redacta SQL ni se
  fijan nombres/detalles de triggers. Protegen la marca, no certifican su origen
  en el servicio autorizado.
- Futura migración posterior a 0006: campo y protección física. Preferencia
  aprobada por instalación irreversible de triggers, para evitar retirar
  silenciosamente la defensa al revertir. Reconstrucciones futuras de tablas
  deberán preservar o reinstalar esas garantías.

[Contrato conceptual y condiciones de consumo](contracts/ecomotor-transition-target-v1.md#a3-cat-freeze-01--congelación-del-catálogo-objetivo).
Uso real bloqueado hasta identidad/fuente confiables, validación completa,
protección instalada y efectiva, configuración autorizada y referencia causal
verificable a la versión usada. frozen_at no basta. Sin tablas de uso ficticias,
eventos objetivo, publicación o activación; S3 V1 sigue único escritor XP activo.
Implementación, pruebas de concurrencia y acuerdos Core/A3.5/Henry/consumidores,
valores oficiales y permisos continúan pendientes. Este registro solo documenta.


## A3-XP-PREVIEW-01 · Simulación interna de XP objetivo · 21/10/2026

Aprobada **internamente por Equipo 5 en 02C-2 el 21/10/2026**, sobre develop
`68b85872f4f53dc575130622f507da5a55656048`, tras #90. No requisito técnico literal
DAR3 ni ratificación de Óscar/Core/Henry. Simular no concede XP ni activa el objetivo.

Se permite simular progresión sobre una versión persistida, preparatoria o
congelada, identificada por PK técnica y alias explícitos. Una lectura coherente
bajo SQLite/D-19 obtiene un catálogo completo validado por A1.1; el cálculo se
delega al planificador puro A2.1. El resultado inmutable conserva PK y plan,
exclusivamente informativos: sin perfiles, eventos, elecciones o efectos de negocio.
No congela, publica, autoriza ni genera trazabilidad persistente de uso real.
S3 V1 permanece único escritor XP activo.

En el corte documental de PR #91, el traspaso mencionaba A3-CAT-USE-01A y
A3-CAT-TRACE-01A sin aportar su articulado en los documentos revisados. Se
registraron correctamente solo los límites suministrados: la simulación no acredita
autorización de uso ni genera trazabilidad persistente real. La conciliación
posterior completa ese articulado aprobado internamente en 02C-2 mediante
[USE-01A](#a3-cat-use-01a--condiciones-de-uso-autorizado-del-catálogo-objetivo--21102026)
y [TRACE-01A](#a3-cat-trace-01a--procedencia-y-trazabilidad-causal-del-catálogo-objetivo--21102026),
sin cambiar el alcance ni las garantías de PREVIEW-01.

Concreción técnica menor del simulador: preview_target_xp(catalog_version_id, *,
using, xp_before, amount), resultado compuesto por PK y TargetXPPlan; frontera
exterior atomic IMMEDIATE y rechazo explícito de transacciones ya activas. El
comando preview_target_xp solicita cuatro argumentos obligatorios, calcula sin
salida de consola dentro del bloqueo y muestra un aviso inequívoco de simulación.
No son contratos definitivos de autorización o consumidores externos.

[Contrato, API y límites](contracts/ecomotor-transition-target-v1.md#a3-xp-preview-01--simulación-interna-de-xp-objetivo).
En el corte de #91 se entregó implementación para revisión; después quedó
integrada mediante #91 en b60b59b. Su merge no autoriza activación ni uso real.


## A3-CAT-USE-01A · Condiciones de uso autorizado del catálogo objetivo · 21/10/2026

**Aprobada internamente por Equipo 5 en 02C-2 el 21/10/2026**. Conciliación
sobre develop `b60b59b72cae54ddda748bc2a79728eadcffc52e`, tras #91. No requisito
técnico literal DAR3 ni ratificación externa de Óscar, Core/Equipo 0 o Henry.

Toda nueva concesión XP objetivo exige catálogo completo/coherente A1.1 y versión
congelada con protección física FREEZE-01 efectiva. Identidad confiable: alias de
BD, PK técnica exacta y comprobación de catalog_id/version. Ni fecha, PK o versión
textual acreditan aprobación funcional. Una fuente confiable del servidor deberá
acreditar contenido y aplicabilidad de la configuración autorizada; el servidor
resuelve la versión, no el cliente como autoridad. Si falta alguna garantía,
rechazar sin efectos; autorización efectiva coherente con la escritura D-19.
Antes de habilitar consumidores reales se verifica protección instalada/efectiva
en la BD utilizada, sin exigir inspeccionar los nueve triggers en cada concesión.

Replay autorizado conserva la operación original sin exigir que su catálogo siga
autorizado para nuevas concesiones; no recalcula con el catálogo actual. Mantiene
validación inicial de identidad, acceso e integridad histórica: no elimina controles
de seguridad ni permite recuperar operaciones ajenas. Importe incompatible sigue
siendo conflicto. Identidad idempotente **(profile, operation_key)** sin catálogo
ni versión, conforme a A2-IDEM-01; A2-EVO-01 y EVENT/PHYS/FREEZE/PREVIEW se conservan.

[Invariantes completas y fronteras](contracts/ecomotor-transition-target-v1.md#a3-cat-use-01a--condiciones-de-uso-autorizado-del-catálogo-objetivo).
**USE-01B pendiente:** fuente física de aprobación funcional, publicación/selección,
configuración autorizada y vínculo con valores de Óscar, permisos/Core/consumidores,
servicios y diseño físico de autorización. Sin approved/published/active, tablas o
endpoints nuevos. Decisión conceptual documentada, sin implementación ni activación.

## A3-CAT-TRACE-01A · Procedencia y trazabilidad causal del catálogo objetivo · 21/10/2026

**Aprobada internamente por Equipo 5 en 02C-2 el 21/10/2026**. Conciliación
sobre develop `b60b59b72cae54ddda748bc2a79728eadcffc52e`; no requisito técnico
literal DAR3 ni ratificación externa de Óscar, Core/Equipo 0 o Henry.

Cada nueva concesión XP objetivo conserva procedencia persistente, inequívoca e
inmutable de la versión exacta utilizada, incluso sin cambio de época; un nombre
textual no basta. Cada evolución objetivo mantiene causa XP verificable, perfil y
correspondencia histórica de época/catálogo. Todos los cruces se registran sin
omisiones ni duplicados; nivel 8 no añade octava época ni evolución ficticia.
XP, procedencia, progreso y eventos causales objetivo se confirman o revierten
juntos bajo D-19. Replay conserva operación/procedencia originales, sin XP o
evoluciones adicionales ni sustitución de catálogo histórico por uno actual.

Ausencia de procedencia objetivo no demuestra pertenencia V1 ni permite reconstruir
datos inexistentes. XPEvent/EvolutionEvent V1 conservan modelos, registros y
semántica histórica. A3-CAT-EVENT-01 mantiene evoluciones objetivo separadas de
EvolutionEvent V1. **Preferencia conceptual aprobada:** registro de procedencia
separado para concesiones objetivo; no aprueba tabla, modelo o relación concreta.

[Garantías y diseño pendiente](contracts/ecomotor-transition-target-v1.md#a3-cat-trace-01a--procedencia-y-trazabilidad-causal-del-catálogo-objetivo).
**TRACE-01B pendiente:** modelo/tabla, campos/tipos, referencias/FKs a catálogo,
perfil y causa XP, constraints/unicidades/índices, on_delete, privacidad,
conservación/ciclo de vida, eventos físicos objetivo, consulta conjunta V1/objetivo
e integración transaccional y tests de idempotencia/concurrencia. Sin diseño físico
inferido. El simulador no crea concesiones ni procedencia. S3 V1 sigue único
escritor XP activo; activación pendiente de fuentes oficiales, Core/A3.5, Henry
y los demás contratos necesarios.


## A3-CAT-AUDIT-01 · Auditoría técnica del catálogo objetivo · 21/10/2026

**Aprobada internamente por Equipo 5 en 02C-2 el 21/10/2026**, sobre develop
`aabf646f53c77312426454fdf89c8591dfd71727`, tras #92. No requisito técnico literal
DAR3 ni ratificación externa de Óscar/Core/Henry. No requiere nuevas respuestas
externas para este diagnóstico; las dependencias de uso real permanecen abiertas.

Diagnóstico interno de solo lectura por alias SQLite explícito y PK exacta:
observa registro 0007, estructura necesaria, SQL de los nueve triggers de FREEZE-01,
identidad/marca del catálogo y validez completa mediante el lector A1.1. Referencia
SQL importada de TRIGGERS en 0007; comparación conservadora, no solo por nombre ni
normalización que oculte cambios semánticos. Sin DML de prueba, reparación o DDL.
Toda observación ocurre bajo una transacción exterior IMMEDIATE/timeout=5 según
D-19; transacciones exteriores activas rechazadas. No conclusiones favorables
sobre lecturas contradictorias; los fallos operativos no son conformidad.

Resultado inmutable con identidad solicitada/observada, estado preparatorio o
congelado, comprobaciones e incumplimientos identificables. Solo se denomina
**conformidad técnica observada**, no autorización para conceder XP ni credencial
duradera. Un preparatorio válido se identifica como no congelado; un congelado
inválido no obtiene conformidad global. frozen_at no certifica aprobación funcional.
Comando interno audit_target_catalog: éxito 0, incumplimiento 2 y fallo operativo 3;
salida después de cerrar la transacción, sin instalar ni generar datos.

[Contrato, API, alcance y límites](contracts/ecomotor-transition-target-v1.md#a3-cat-audit-01--auditoría-técnica-del-catálogo-objetivo).
Implementación para revisión en PR; no modelos/migraciones, cambios FREEZE/PREVIEW,
publicación, procedencia persistente o escritor objetivo. USE-01B, TRACE-01B,
Core/A3.5, Henry y valores funcionales oficiales siguen pendientes. S3 V1 conserva
su condición de único escritor XP activo.

## A3-TARGET-DEMO-01 · Demo navegable del Ecomotor objetivo · 22/10/2026

**Aprobada internamente por Equipo 5 en 02C-2.** No es una aprobación externa
de valores por Óscar ni un contrato de integración Core/Henry. DAR3 conserva
su autoridad funcional. Implementación en PR para revisión técnica en 01B.

Demo Django independiente de A4-DEMO-01, con settings/URLconf propios y SQLite
exclusiva en `instance/target_demo.sqlite3`. Instalación explícita de un catálogo
sintético preparatorio, reproducible y validado A1.1; no se instala durante HTTP.
PREVIEW-01/A2.1/A1.2 calculan incrementos y todos los cruces de siete épocas;
nivel 8 desbloquea doce opciones visuales (siete históricas y cinco tecnológicas),
sin octava época. Estado efímero firmado, sin sesiones o escrituras de jugador.

Reparto mediante A4.1 con seis bases cero sintéticas y presupuesto interno
provisional de 45, separado de cualquier fuente autorizada de estadísticas.
Placeholders locales de vestimenta, sin equipamiento ni diseños finales Duckies.
HTTP estricto y CSRF, sin escritor XP, elección definitiva o persistencia de puntos.
No altera APIs existentes, rutas Core, modelos, migraciones o V1/S3.

[Contrato y ejecución reproducible](contracts/ecomotor-target-demo-v1.md).
Siguen pendientes valores oficiales, Core/A3.5, Henry, USE-01B/TRACE-01B y
activación coordinada. La demo no acredita publicación, autorización ni integración global.

## A3-TARGET-PERSIST-DEMO-01 · XP y evoluciones ficticias guardadas · 22/10/2026

**Aprobación interna Equipo 5 / 02C-2**, implementada para revisión en PR. App y
SQLite exclusivas de demo, sin alterar A3-TARGET-DEMO-01, V1/S3 o usuarios reales.
Catálogo sintético distinto, validación A1.1 y congelación FREEZE-01; preparación
y congelación tienen transacciones exteriores separadas. Si falla la segunda,
seed puede reintentarse y el estado preparatorio bloquea concesiones.

Tres tablas locales (partida, concesión XP y evolución causal), FKs PROTECT como
concreción exclusiva de demo, snapshots históricos y unicidad por partida/operación.
Concesión sintética atómica IMMEDIATE mediante A2.1/A1.2; replay sin nuevos efectos,
seis cruces para 0→700 y ninguna octava época. Sesión local y operación firmada
por servidor, sin IDs del navegador como autorización. Backend y migrate locales
protegen separación física y apertura no creadora de las operaciones normales.

[Diseño, ejecución y límites](contracts/ecomotor-target-persistent-demo-v1.md).
No aprobación de valores por Óscar, autorización Core, escritor productivo o
implementación USE-01B/TRACE-01B. DAR3 conserva autoridad funcional. La demo guarda
datos ficticios reales; no se presenta como una simulación sin persistencia.

## A4-TARGET-PERSIST-DEMO-01 · Opciones y atributos persistentes de demo · 22/10/2026

**Aprobada internamente por Equipo 5 / 02C-2**, implementada para revisión en 01B.
Extiende únicamente la app/SQLite aisladas del Paso 2 con configuración por opción,
estado activo e historial de selección/redistribución. Doce códigos sintéticos,
seis bases cero y presupuesto provisional independiente de 45, sin aprobación
funcional de esos valores por Óscar. Composición A4.2.1/A4.3.1/A4.1, transacciones
IMMEDIATE, sesión y claves firmadas con propósito propio, revisiones explícitas,
replay histórico y rollback íntegro. Redistribución gratuita para la demo; no-op
sin eventos. No relaciones Duckies/User ni modificaciones XP/evoluciones/V1.

[Contrato y concreciones técnicas locales](contracts/ecomotor-target-playable-persistent-demo-v1.md).
No cierra USE-01B, TRACE-01B ni acuerdos externos; no Rewards ni activación.
DAR3 conserva autoridad funcional. La demo #94 permanece intacta.

## DEMO-REWARDS-XP-01 · Rewards XP sintético persistente · 22/10/2026

**Aprobado internamente por Equipo 5 / 02C-2**, implementado para revisión 01B.
Paso 4 sobre app/SQLite/ruta del laboratorio persistente: desafío ficticio propone
700 XP mediante F1-A y visita válida produce NO_REWARD. Nuevos hechos firmados,
instante original estable, huella F1-A, identidad terna y clave causal XP derivada
de identidad con namespace propio. Un único DemoTargetRewardEvent local conserva
propuesta/snapshots/versiones y causas; no es RewardEvent productivo.

Extracción mínima del núcleo XP privado sin abrir transacciones; propietario
interno comprueba el contexto exterior IMMEDIATE. Entrada pública XP del Paso 2
conserva su contrato; Rewards confirma XP/evoluciones/registro juntos o revierte
todo. Replay no reevalúa reglas ni concede otra vez. No monedas, objetos o efectos
no soportados. Sin cambios a F1-A, contrato global Rewards v0, V1 u otros equipos.

[Contrato, esquema, seguridad y reproducción](contracts/ecomotor-target-demo-rewards-xp-v1.md).
Los datos son sintéticos, no aprobación de Óscar/Core; DAR3 conserva autoridad.
No F2-A productivo, USE-01B, TRACE-01B ni activación.

## CONSOLIDACIÓN-A-01 · Reorganización física del laboratorio

Aprobada internamente por Equipo 5 en 02C-2 el **22/10/2026**, conforme a D-18 y
D-21. El laboratorio de los Pasos 2–4 se mueve de `apps/ecomotor_target_demo/`
a `apps/ecomotor/ecomotor_target_demo/`. La ruta anterior se conserva en los
antecedentes como ubicación histórica; no se mantiene un paquete de compatibilidad.

`AppConfig.name` pasa a `apps.ecomotor.ecomotor_target_demo` y su label explícito
sigue siendo `ecomotor_target_demo`. Sigue siendo una app auxiliar independiente,
instalada exclusivamente en los settings de demo. No se fusiona con Ecomotor.
Las migraciones 0001, 0002 y 0003 conservan contenido, dependencias, identidades y
tablas. No hay nueva migración ni transformación de datos o ContentTypes.

Se actualizan rutas Python y descubrimiento, manteniendo el runner de dos fases.
Settings, SQLite, URL, cookies, tokens, reglas, transacciones y aislamiento no cambian.
Una copia desechable creada antes del movimiento permite comprobar migraciones ya
aplicadas, datos completos y replay histórico con sesiones y tokens anteriores;
una SQLite nueva comprueba instalación y flujo completo desde la nueva ubicación.
Los resultados de las suites se comunican en la PR, sin sustituirlos por recuentos históricos.

Es una reorganización estructural, no una aprobación externa de DAR3, Óscar o Core.
No cierra USE-01B, TRACE-01B ni contratos productivos. No altera V1/S3, Duckies,
Bank, Shop, Rewards F1-A ni la demo #94.
