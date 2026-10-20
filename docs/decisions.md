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
la referencia de etapa, no sus atributos históricos originales. No reconstruir
historia con catálogos nuevos, renombrar etapas o convertir puntos antiguos a cero.
Core/P5 conserva retención, anonimización/eliminación y on_delete pendientes.
[Dependencias A3](pending-decisions.md#14-a2--dependencias-para-xp-histórica-objetivo)
no bloquean diseñar/probar el planificador puro, pero sí la futura activación.
No se modifican contratos V1 ni se desbloquean dominio, S13-A2 o Rewards F2-A.
