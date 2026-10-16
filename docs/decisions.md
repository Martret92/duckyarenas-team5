# Registro de decisiones

Este es el registro principal de acuerdos y decisiones técnicas. Las propuestas
pendientes se mantienen separadas de las decisiones confirmadas.

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
