# Decisiones pendientes · Arquitectura candidata V2

## 1. Marco vigente y antecedentes

Esta lista operativa distingue requisitos documentales trasladados, decisiones
vigentes y propuestas candidatas. Se basa en los documentos del repositorio y en
la revisión externa incorporada a [architecture.md](architecture.md), sin afirmar
consulta directa de los PDF del Project. No aprueba acuerdos nuevos ni cambia
los estados del [registro de decisiones](decisions.md).

La arquitectura candidata V2 está documentada en `52c3865` y el registro actualizado
en `ca8d182`. El [ERD y diccionario V1 de Parte A](erd/ecomotor.md) ya existe como
antecedente interno aceptado A-01…A-16. Su adaptación a V2, el ERD consolidado con
los demás dominios y el ORM/migraciones definitivos siguen pendientes. Nueve épocas,
rangos antiguos y equipamiento automático no se trasladan como reglas V2 aprobadas;
los puntos afectados requieren revisión formal, sin revocar acuerdos mediante
una nota editorial.

Son requisitos documentales trasladados que no se reabren aquí: siete etapas,
evolución automática al cumplir condiciones, especializaciones dentro de Actual,
XP histórica acumulativa y no decreciente, los seis stats `ATK`, `DEF`, `LOG`, `SPE`,
`VEL`, `INT`, seis piezas principales por época diferenciadas de complementos,
historiales y Museo Ducky, y el mínimo funcional de recompensas de DAR3. Sus detalles
pendientes se remiten a arquitectura, secciones 3, 7 y 8. La puntuación provisional
de una partida y sus penalizaciones no descuentan XP histórica ya consolidada.

Core conserva User, autenticación y JWT. D-09…D-12, D-17 y D-18 mantienen la base
provisional de usuarios/perfiles y las rutas/labels Django. **D-19 está vigente**:
`IMMEDIATE`, timeout de 5 segundos, transacciones antes de leer estado mutable,
restricciones e idempotencia. No es una decisión abierta; tampoco resuelve la
coordinación entre dominios.

En las tablas, **pendiente** identifica un acuerdo por tomar y **pendiente de
confirmación** una aclaración o validación aún no recibida. El impacto y la
prioridad son recomendaciones de planificación para el ámbito indicado: una
cuestión puede impedir cerrar su ORM sin impedir diseñar conceptualmente el ERD.
Las referencias por sección remiten a [architecture.md](architecture.md), salvo
cuando se indica una decisión o un apartado del ERD V1.

## 2. Validaciones pendientes del Equipo 5

| Pregunta concreta | Estado | Responsable de validación | Impacto | Prioridad y condición | Referencia |
| --- | --- | --- | --- | --- | --- |
| ¿Se confirma el reparto principal Jaime/A, Félix/B y Henry/C y cómo se delimitan las responsabilidades definitivas? | Pendiente | Tres integrantes del Equipo 5, incluidos Félix y Henry | Planificación V1 e integración | Resolver para asignar trabajo y revisión; no impide diseñar propuestas | D-13; arquitectura §4 |
| ¿Se acepta Rewards como capacidad coordinada por Ecomotor, con responsabilidad compartida y servicios de B/C propietarios de sus efectos? | Pendiente | Equipo 5, Partes A/B/C | ERD V2, ORM e integración | Acordar antes de cerrar el diseño compartido de Rewards; no exige app nueva | D-14/D-15; §§4–5 |
| ¿Se valida la distinción entre catálogo comercial de Shop (ofertas, precios y disponibilidad) e identidad/definición de objetos y posesión de Inventory? ¿Cómo se interpreta el catálogo de B en D-15? | Pendiente | Equipo 5, especialmente B/C, con A como consumidor | ERD V2, ORM e integración | Resolver antes de cerrar las entidades y referencias B/C; D-15 sigue siendo propuesta, no se corrige su estado por interpretación | D-15; §4 |
| ¿Se acepta usar datos provisionales separados de la lógica, identificados como demo/prueba, sin números mágicos ni valores presentados como oficiales? | Pendiente | Tres integrantes del Equipo 5 | Planificación V1 y ORM | Confirmar antes de adoptar esa política; valores aislados no impiden el diseño conceptual | D-16; §5 |
| ¿Quién coordina cada compra y recompensa completa y delimita la transacción exterior o la recuperación? | Pendiente | Equipo 5, Partes A/B/C | ORM e integración | Resolver antes de implementar operaciones multidominio; detalles y claves en §4 de este documento | D-14/D-15/D-19; §§8–9 |

## 3. Adaptación funcional y ERD V2

| Pregunta concreta | Estado | Responsable de validación | Impacto | Prioridad y condición | Referencia |
| --- | --- | --- | --- | --- | --- |
| ¿Cómo se adapta el catálogo y estado de progresión del ERD V1 de nueve épocas a las siete etapas, distinguiendo nivel de etapa? | Pendiente | Parte A y Equipo 5 | ERD V2 y ORM | Necesario para cerrar el ERD V2 de progresión; las siete etapas no están en duda | §7; A-03/A-04/A-15 |
| ¿Qué condiciones de evolución deben representarse y cómo se procesan transiciones múltiples conservando trazabilidad? | Pendiente de confirmación | Parte A; Óscar para reglas ambiguas | ERD V2, ORM e integración | Cerrar representación y reglas antes del ORM/servicio afectado; valores de umbrales pueden parametrizarse | §7; A-05/A-06/A-07 |
| ¿Se equipa automáticamente al evolucionar o inicializar y cómo se coordina esa operación con posesión y compatibilidad? | Pendiente de confirmación | Partes A/B; Óscar para dudas funcionales | ERD V2 e integración | Revisar formalmente el comportamiento V1 antes del flujo definitivo; no cuestiona la evolución automática | §§7–8; A-08/A-12; ERD §§9–10 y 16 |
| ¿Cómo se adaptan los conjuntos de seis piezas a siete etapas y qué concesiones, conservación y reequipamiento se cubren en V1? | Pendiente de confirmación | Partes A/B y Equipo 5; Óscar para contenido oficial | ERD V2, ORM y planificación V1 | Definir relaciones para cerrar el ERD; el contenido de etapas fuera de la demo puede aplazarse si se acuerda | §§3, 7 y 11; A-08 |
| ¿Qué nombres y códigos se normalizan entre Sistemas/AdminSys y Data/Data & IA/Data & AI? ¿Se aceptan identificadores estables y etiquetas configurables? | Pendiente de confirmación | Parte A y Equipo 5; Óscar ante equivalencias ambiguas | ERD V2 e integración | Acordar identidades antes de cerrar catálogos/contratos; etiquetas pueden ajustarse después. No se aprueba `data_ia` como código definitivo | §7; A-09/A-14 |
| ¿Qué acceso, cambio, conservación de progreso, XP y rangos tendrán las especializaciones? | Pendiente de confirmación | Parte A; Óscar para reglas funcionales | ERD V2 y ORM | Bloquea el ORM definitivo de ese dominio si entra en V1; puede aplazarse su implementación con alcance acordado | §7; A-09; ERD §14 |
| ¿Cómo se representan y configuran condiciones, vigencia, límites temporales, emisor, compatibilidad y repetibilidad de recompensas cuando proceda? | Pendiente | Equipo 5, especialmente A; juegos y Óscar según la regla | ERD V2 y ORM | Definir capacidades usadas en V1 antes del ORM de Rewards; `RewardRule`/`RewardEvent` no son modelos aprobados | §§4–5 y 8 |
| ¿Los seis stats canónicos se calculan o persisten y cómo influyen piezas, complementos y consumibles en ellos y en cada juego? | Pendiente de confirmación | Parte A, B y equipos de juegos; Óscar para fórmulas ambiguas | ERD V2, ORM e integración | Cerrar representación si entra en el ERD V2; acordar efectos antes de servicios RPG. No inventar fórmulas | §§5 y 7 |
| ¿Qué datos de historial de épocas, XP y equipamiento deben persistir y qué lecturas componen el Museo? | Pendiente | Partes A/B y Equipo 5 | ERD V2, ORM y planificación V1 | Definir persistencia del alcance incluido antes del ORM; interfaz avanzada puede aplazarse | §§5 y 11; A-02/A-05/A-16 |
| ¿Qué entidades, cardinalidades, restricciones y referencias al usuario necesita el diseño consolidado A/B/C, conservando D-11/D-12 hasta revisión autorizada? | Pendiente | Partes A/B/C y Equipo 5 | ERD V2 y ORM | Cerrar el diseño revisado del dominio antes de su ORM; no toda Parte A vuelve a estar sin diseñar | D-07/D-11/D-12/D-18; ERD V1 |

## 4. Contratos e integración entre módulos

| Pregunta concreta | Estado | Responsable de validación | Impacto | Prioridad y condición | Referencia |
| --- | --- | --- | --- | --- | --- |
| ¿Qué formato técnico y respuesta concretan el mínimo funcional de recompensas entre juegos, Ecomotor y Core? | Pendiente | Equipo 5, Core y equipos de juegos | Integración y ORM de trazabilidad | Acordar antes de integrar; el mínimo DAR3 ya está especificado y no se reabre | §8; D-05/D-14 |
| ¿Cómo se verifican identidad, origen autorizado y permisos, y cómo se incorpora el repositorio al proyecto común y su entorno? | Pendiente | Core y Equipo 5; juegos para emisión de hechos | Integración | Necesario antes de exponer operaciones externas; diseño local compatible puede continuar. User/JWT/auth pertenecen a Core | §§3 y 10; D-01/D-05/D-10/D-17 |
| ¿Cómo se construyen y relacionan claves de actividad, recompensa, cargo y entrega, y qué ocurre ante contenido conflictivo, errores y reintentos? | Pendiente | Partes A/B/C, Core y juegos | ORM e integración | Acordar antes de servicios críticos y contratos; conservar semántica local V1 como antecedente, no extenderla sin acuerdo | §§8–9; A-13; ERD §11 |
| ¿Cómo se distribuyen comprobaciones de Ecomotor, proceso comercial de Shop, validación/cargo de Bank y entrega de Inventory? | Pendiente | Partes A/B/C; Óscar ante ambigüedad funcional | ORM e integración | Necesario antes del flujo completo de compra; Ecomotor consulta al propietario del saldo, no lo duplica | §§4 y 8 |
| ¿Qué frontera transaccional, rollback o recuperación de fallos parciales conecta XP, monedas, objetos y compras? | Pendiente | Partes A/B/C y Equipo 5; Core si afecta a ejecución compartida | ORM e integración | Resolver antes de implementar operaciones coordinadas. D-19 no garantiza atomicidad global; no se impone aquí una estrategia | §9; D-19; ERD §17 |
| ¿Qué contratos A→Inventory/Equipment permiten conceder, consumir, validar posesión y equipar sin escrituras ajenas ni incoherencias concurrentes? | Pendiente | Partes A/B y C para entrega comercial | ERD V2 e integración | Acordar antes de flujos definitivos; concesión y equipamiento son operaciones distintas | §8; A-08/A-11; ERD §16 |
| ¿Qué contratos REST, consultas de progreso/stats, errores y versiones necesitan los consumidores? | Pendiente | Equipo 5, Core y juegos | Integración | Acordar antes de integración externa; servicios Python internos pueden diseñarse sin HTTP obligatorio | §§8 y 10 |
| ¿Qué eventos WebSocket se incluyen en V1, quién los produce/consume y quién mantiene su infraestructura y autorización? | Pendiente | Core, Equipo 5 y juegos; Óscar para alcance evaluable | Integración y planificación V1 | Arquitectura objetivo documental conocida; cobertura puede aplazarse solo según alcance acordado | §§8, 10 y 11 |

## 5. Preguntas al profesor Óscar y alcance V1

| Pregunta concreta | Estado | Responsable de validación | Impacto | Prioridad y condición | Referencia |
| --- | --- | --- | --- | --- | --- |
| ¿Qué aclaraciones resuelven las reglas ambiguas de evolución, especializaciones y efectos de objetos identificadas en §3, incluidas diferencias entre referencias anteriores y posteriores? | Pendiente de confirmación | Óscar; Equipo 5 prepara preguntas concretas | ERD V2 y ORM | Priorizar las reglas que cambian estructura del dominio incluido en V1; no solicitar al profesor que diseñe el ORM | §§2, 7 y 12 |
| ¿Cuáles son los valores oficiales de umbrales, XP/monedas por actividad, precios, contenido de conjuntos y parámetros de especializaciones/consumibles? | Pendiente de confirmación | Óscar; A/B/C para incorporar configuración | ORM y planificación V1 | Parámetros sustituibles no bloquean por sí solos el ERD; uso de datos provisionales depende de validar D-16 | §5; D-16 |
| ¿Qué recorrido y evidencia cubren la demo evaluable, tomando Prehistoria, Grecia y Roma como demostración inicial contemplada en DAR3? | Pendiente de confirmación | Óscar y Equipo 5; juegos participantes | Planificación V1 e integración | Acordar antes de cerrar el backlog mínimo; demo no equivale a catálogo completo de siete etapas | §11 |
| ¿Qué cobertura V1 se exige para historiales, Museo, RPG completo, WebSockets, integraciones externas y pedidos físicos? | Pendiente de confirmación | Óscar; Equipo 5 y equipos afectados para planificación | Planificación V1, ERD V2 e integración | Requisitos conservados; priorizar cobertura, no declarar funcionalidades eliminadas. Extensiones pueden aplazarse por acuerdo | §§10–12 |
| ¿Cómo encajan tienda estética, objetos de combate y consumibles con los conjuntos históricos, incluida la regla anterior de sets históricos no comprables? | Pendiente de confirmación | Óscar y Partes B/C, con A | ERD V2 e integración | Aclarar antes de fijar restricciones comerciales afectadas; no dar la regla V1 por revisada | §§4, 7 y 12; antecedentes V1 |
| ¿PR07 sustituye la indicación de User estándar por CustomUser y exige registro/login/logout en cada repositorio temporal? | Pendiente de confirmación | Óscar y Core | ORM de usuarios e integración | D-17 mantiene D-09/D-10 hasta respuesta: sin auth paralela ni cambios de User/migraciones. Trabajo compatible puede continuar | D-05/D-09/D-10/D-17 |
| ¿Qué dos o más entidades deben cubrir el CRUD evaluable y con qué permisos, sin editar arbitrariamente estados derivados o historiales? | Pendiente de confirmación | Óscar y Equipo 5 | Planificación V1 y ORM afectado | Necesario antes del CRUD definitivo; no bloquea todo el diseño de dominio | PR07 en decisions.md; §12 |
| ¿Los 15 días y entregables Git son calendario obligatorio o guía/rúbrica? | Pendiente de confirmación | Óscar; Equipo 5 para ajustar plan | Planificación V1 | Aclarar antes de comprometer calendario; no bloquea ERD conceptual | PR07 en decisions.md; team5-work-plan.md |

## 6. Trabajo posterior y verificaciones

Estas son tareas dependientes de las decisiones anteriores, no nuevas preguntas
arquitectónicas ni acuerdos pendientes de aprobación:

| Trabajo | Dependencia y responsable | Verificación necesaria |
| --- | --- | --- |
| Revisar ERD/diccionario V2 de Parte A y consolidar A/B/C | Parte A y Equipo 5, tras resolver detalles estructurales de §§2–3 | Cardinalidades, restricciones, reglas de borrado y coherencia con decisiones vigentes; revisión explícita de incompatibilidades A-01…A-16 |
| Implementar servicios, ORM, migraciones y datos maestros | A/B/C, desde diseño revisado y contratos acordados; parámetros provisionales sujetos a D-16 | Integridad, inicialización y tratamiento de perfiles existentes; revisar antecedente M-01 antes de migrar, sin inventar estado ni borrar datos |
| Verificar operaciones críticas e integración | Responsables de servicios y equipos consumidores, con coordinación de §4 definida | Tests de dominio, idempotencia, fallos parciales, permisos y contratos; detalle en arquitectura §11 |
| Verificar concurrencia SQLite | Equipo 5 y propietarios de servicios, bajo D-19 vigente | `TransactionTestCase` y al menos una ejecución SQLite file-backed; rollback y reintentos según D-19 |
| Completar entregables PR07 | Equipo 5, después de aclarar alcance evaluable en §5 | Admin, URLs/vistas/templates, navegación, formularios, CRUD, permisos y tests; evidencias Git/PR y aportaciones individuales |
| Revisar documentación y plan operativo | Equipo 5, sin cambiar estados por notas editoriales | Enlaces Markdown, finales de línea y coherencia entre arquitectura, decisiones, ERD y [plan de trabajo](team5-work-plan.md) |

La referencia de arquitectura §12 que aún dice que el registro no incorpora el
ERD quedó desactualizada tras `ca8d182`; requiere corrección documental posterior
autorizada. No se modifica arquitectura en esta actualización. Resolver una fila
de esta lista requerirá evidencia del acuerdo y, cuando proceda, su registro
formal en decisions.md; ninguna se considera aprobada por publicarla aquí.
