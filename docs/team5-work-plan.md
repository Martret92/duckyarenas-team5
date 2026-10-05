# Plan de trabajo · Equipo 5

Estado: propuesta operativa para revisión por los tres integrantes del Equipo 5.

[architecture.md](architecture.md) describe arquitectura y límites;
[decisions.md](decisions.md) registra decisiones confirmadas y separa propuestas;
[pending-decisions.md](pending-decisions.md) recoge asuntos abiertos.
Este plan sirve como guía práctica de trabajo, no como aprobación de modelos o contratos.

## 1. Alcance y procedencia

DAR3, sección 9 (páginas 48-50 del PDF consultado), atribuye al Equipo 5:

- Parte A: Ecomotor y evolución.
- Parte B: Avatar e inventario.
- Parte C: Ecommerce y DuckyBank.
- Servicio común de recompensas.

DAR3 exige progreso, inventario, economía y recompensas validados por el servidor,
prevención de duplicados y consistencia de las compras. El servidor es la fuente
de verdad para XP, evolución, inventario, DuckyCoins, compras y recompensas.
La sección 10 requiere coordinación de recompensas con el Equipo 0 y los juegos.
DAR3 no asigna individualmente A/B/C a Jaime, Félix y Henry.

Las reglas de la sección 2 son aclaraciones funcionales conocidas de clase e
información funcional disponible para este plan. No se presentan como citas
textuales de DAR3 cuando el documento no las detalla exactamente.
El reparto, las fronteras, la autonomía, los hitos y el backlog son propuestas
internas. Los modelos concretos, contratos y mecanismos técnicos se decidirán
durante la arquitectura; este documento no los diseña.

## 2. Modelo funcional conocido

### Progreso histórico

| Nivel histórico | Época |
| --- | --- |
| 1 | Prehistoria |
| 2 | Grecia |
| 3 | Roma |
| 4 | Edad Media |
| 5 | Renacimiento |
| 6 | Revolución Industrial |
| 7 | Siglo XX |
| 8 | Era Espacial |
| 9 | Era Digital |

El usuario comienza en Prehistoria. La XP total es acumulativa y no se gasta.
Puede mostrarse una barra relativa hacia el siguiente nivel, calculada a partir
del progreso y los umbrales; no sustituye ni reduce la XP histórica acumulada.
Los umbrales reales todavía no son oficiales. El plan propone usar valores
provisionales separados de la lógica, según la política pendiente D-16.

### Evolución y sets históricos

- Cada época tiene seis piezas principales.
- Al iniciar el juego, se conceden y equipan automáticamente las seis de Prehistoria.
- Al evolucionar, se conceden juntas las seis piezas de la nueva época y se equipa
  automáticamente el nuevo set.
- Los sets anteriores se conservan permanentemente y pueden volver a equiparse libremente.
- Las piezas históricas no se compran con DuckyCoins.
- Equipar un set antiguo cambia solo la apariencia, no la época real ni el progreso.

Si una concesión de XP atraviesa varios umbrales, se procesan todas las evoluciones
intermedias, se registra cada evolución y se concede cada set correspondiente.
Al final queda equipado el set de la época más avanzada alcanzada.

### Especializaciones

Después de Era Digital se puede elegir Developer, Ciberseguridad, AdminSys,
Gamer o Data & AI. Cada especialización tiene progreso independiente:

`Inicial → Junior → Middle → Senior → Master`

Puede explicarse conceptualmente como niveles 10–14, pero se recomienda mantener
separados el progreso histórico global, la especialización activa y el progreso
o rango de cada especialización. No es una continuación obligatoria del mismo
nivel histórico ni una propuesta de campos Django.

Se puede cambiar de especialización volviendo al punto de Era Digital. El cambio
no elimina XP histórica ni progreso anterior: cada especialización conserva su
rango. Por ejemplo, un usuario puede tener Gamer = Senior y Developer = Junior.
La navegación o transición concreta para volver a ese punto está por diseñar.
Siguen pendientes las reglas de XP de dominio y los requisitos y umbrales de rangos.

### Tipos de objetos

| Tipo | Obtención y comportamiento |
| --- | --- |
| Sets históricos | Apariencia; seis piezas por época; obtenidos por evolución; permanentes y no comprables. |
| Objetos de combate | Distintos del set histórico; comprados con DuckyCoins; consumibles con múltiples unidades, por ejemplo x1, x3 o x5. |

Se conocen inicialmente tres objetos de ataque y tres de defensa. No se fijan
efectos ni precios definitivos. La utilización concreta por cada modo de juego
sigue pendiente. DAR3 también contempla una tienda estética; se debe aclarar su
encaje con este catálogo comercial sin convertir los sets históricos en compras.

## 3. Reparto y fronteras propuestos

Pendiente de revisión por los tres integrantes del Equipo 5, incluida la
confirmación con Félix y Henry (D-13 a D-15). No es una asignación individual de DAR3.

### Jaime · Parte A

Responsabilidad principal propuesta: XP acumulada, historial de XP, épocas,
umbrales, evolución automática, historial de evolución y progreso histórico.
Incluye la base del progreso por especializaciones, la integración de XP con
Rewards y la coordinación inicial del contrato común de recompensas.
Parte A decide cuándo ocurre una evolución. No debe implementar inventario.

### Félix · Parte B

Responsabilidad principal propuesta: catálogo de objetos, sets históricos,
piezas principales, inventario, equipamiento, apariencia actual y conservación
de sets. Incluye equipamiento automático tras evolución, objetos de combate,
cantidades de consumibles y datos necesarios para Museo.
Parte B decide cómo se representa y modifica el inventario. No debe recalcular
XP ni evolución.

### Henry · Parte C

Responsabilidad principal propuesta: wallet, saldo DuckyCoins, historial financiero,
ingresos y gastos, tienda, catálogo comercial, precios y compras. Incluye validar
saldo suficiente, proteger frente a compras repetidas y mantener consistencia
entre saldo, transacción e inventario.
Parte C decide y valida la operación económica. No debe crear un inventario paralelo.

### Propiedad de dominio propuesta

| Dominio | Propietario propuesto |
| --- | --- |
| XP | A |
| Épocas | A |
| Evolución | A |
| Especializaciones/progreso de dominio | A |
| Catálogo de objetos | B |
| Sets históricos | B |
| Inventario | B |
| Equipamiento | B |
| Consumibles poseídos | B |
| DuckyCoins | C |
| Wallet | C |
| Transacciones | C |
| Tienda | C |
| Compras | C |

A decide evolución → B concede/equipa set. C valida compra → B añade consumibles.
Rewards concede XP mediante A y monedas mediante C. Ninguna parte debe modificar
directamente el estado interno de otra si existe una operación de dominio para hacerlo.

## 4. Servicio común de recompensas y dependencias

La propuesta D-14 mantiene Rewards como responsabilidad compartida. Debe orquestar
y utilizar las operaciones propietarias, sin duplicar lógica de negocio.
Su flujo conceptual es:

`resultado validado → comprobar duplicado → registrar evento → XP → DuckyCoins → evolución/objetos → resumen`

En el reparto propuesto, Jaime/A aporta XP y evolución, Félix/B concesión de
objetos e inventario, y Henry/C DuckyCoins y registro financiero. La coordinación
inicial desde A no convierte Rewards en propietario de inventario o economía.
El flujo no fija una firma de función, una API ni el orden técnico de escrituras.
La idempotencia general y la consistencia entre dominios se revisarán conjuntamente.

Dependencias internas:

- A depende de B para materializar sets y equipamiento.
- B depende de A para saber cuándo hay evolución.
- C depende de B para entregar consumibles comprados.
- Rewards depende de A/B/C y del resultado validado de los equipos de juego.

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

El orden H1–H6 es una propuesta de ejecución. A/B/C pueden avanzar en paralelo
tras acordar las operaciones que conectan sus dominios. Los hitos no fijan fechas.

| Hito | Entregable y dependencias |
| --- | --- |
| H0 · Base | Completado: repositorio, bootstrap, `users`, `ecomotor`, perfiles base y documentación inicial. |
| H1 · Arquitectura y modelos mínimos | A: XP, historial, épocas, evolución y especializaciones mínimas. B: catálogo, sets, inventario, equipamiento y consumibles/cantidades. C: wallet, transacciones, tienda y compra. Compartido: Rewards v0, contratos internos e idempotencia. Diseñar y revisar antes de implementar los modelos concretos. |
| H2 · Servicios de dominio | A: concesión de XP (grant XP), progreso y evolución. B: conceder sets, equipar, inventario y cantidades. C: ingresos, gastos y compra. Consumir las operaciones acordadas en H1 y probar sus reglas. |
| H3 · Vertical mínima | Actividad simulada → XP + monedas → evolución → nuevo set → compra de consumible → inventario. Para demo bastan Prehistoria, Grecia y Roma, como contempla DAR3; el recorrido con consumible incorpora las aclaraciones de clase. |
| H4 · Historial y Museo | A: historial XP/evolución. B: sets históricos y apariencia/Museo. C: historial DuckyBank. Depende de los estados y eventos de H2–H3. |
| H5 · Robustez | Concurrencia, duplicados, saldo no negativo, coherencia compra/inventario, evolución única, conservación de progreso y restricciones. Los tests críticos empiezan en H1–H2; aquí se completa la revisión transversal. |
| H6 · Integración y demo | Equipos 1–4, Equipo 0, contrato final Rewards, datos demo, documentación y tests integrados. Depende de los contratos externos y del recorrido mínimo estable. |

## 7. Backlog inicial por integrante

Orden de prioridad propuesto, sujeto a validar el reparto. Cada paso utiliza las
aclaraciones funcionales conocidas y mantiene pendientes las decisiones técnicas.

### Jaime

1. Diseñar en H1 el XP acumulado y su historial, épocas/umbrales, época actual e
   historial de evolución; separar barra visual y XP histórica.
2. Diseñar la base de especializaciones independientes y conservación de rangos,
   sin inventar XP de dominio ni requisitos oficiales.
3. Coordinar con B/C las operaciones internas y Rewards v0, incluida idempotencia.
4. Construir en H2 concesión de XP, progreso y evolución, con múltiples umbrales;
   solicitar a B cada set y dejar equipado el más avanzado.
5. Conectar la vertical H3, completar historial H4 y robustez H5.
6. Apoyar contrato final, integración de juegos y demo H6.

### Félix

1. Diseñar en H1 catálogo, seis piezas por set, inventario y equipamiento;
   separar sets permanentes de consumibles con cantidades.
2. Acordar con A la inicialización y concesión/equipamiento de sets, y con C la
   entrega de consumibles comprados, sin duplicar inventarios.
3. Construir en H2 set inicial, concesión de sets, equipamiento y cantidades;
   conservar y reutilizar sets sin alterar el progreso real.
4. Conectar el inventario de H3 y preparar apariencia y datos de Museo H4.
5. Probar piezas únicas, cantidades, aislamiento entre usuarios y concurrencia H5.
6. Integrar concesión de objetos de Rewards y preparar datos demo/documentación H6.

### Henry

1. Diseñar en H1 wallet, saldo, transacciones, catálogo comercial, tienda y compra.
2. Acordar con B la entrega de consumibles y con Rewards los ingresos y el registro
   financiero; revisar conjuntamente compras repetidas y consistencia.
3. Construir en H2 ingresos, gastos y compra validada en servidor, con saldo suficiente.
4. Conectar monedas y compra de consumible de H3; completar historial DuckyBank H4.
5. Verificar en H5 saldo no negativo, atomicidad y reenvíos sin compras duplicadas.
6. Apoyar contrato final, integración y datos comerciales demo H6.

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

Siguen pendientes:

- Umbrales oficiales, XP oficial por actividad y DuckyCoins oficiales.
- Contenido definitivo de sets, precios y efectos definitivos de consumibles.
- XP de dominio y requisitos de rangos.
- Formato final equipos 1–4 → Rewards y contrato definitivo con Equipo 0.
- Utilización concreta de consumibles por modos de juego.
- Modelos Django concretos, contratos internos y mecanismo técnico de idempotencia,
  que deberán diseñarse y revisarse por el Equipo 5 durante H1.

### Fuera de prioridad en la primera versión

Contenido final de todas las épocas, especializaciones completas, efectos avanzados,
Techies, cotización variable y ampliaciones innecesarias para la demo mínima.
Esto no elimina la base mínima de especializaciones prevista en H1 ni su conservación.
Techies y cotización variable están fuera de la primera entrega según DAR3;
la priorización restante es parte de esta propuesta operativa.

## 9. Tests mínimos por área

Estos tests se proponen para verificar requisitos y aclaraciones funcionales;
no existen todavía como tests implementados de dominio.

| Área | Comprobaciones mínimas |
| --- | --- |
| A | XP acumulativa; XP no se gasta; evolución por umbral; múltiples umbrales en una recompensa; historial; conservación del progreso; no duplicar evolución. |
| B | Set inicial; set completo al evolucionar; equipamiento automático; conservar sets anteriores; reequipar un set anterior sin cambiar época; no duplicar piezas únicas; cantidades de consumibles; aislamiento entre usuarios. |
| C | Ingresos; saldo suficiente; saldo no negativo; compra; atomicidad saldo/transacción/inventario; reenvío no duplica compra. |
| Rewards | Una actividad no se recompensa dos veces; utiliza dominios propietarios; devuelve resumen coherente. |

## 10. Definition of Done

Como criterio operativo propuesto, una funcionalidad se considera terminada cuando:

- Cumple el requisito y las reglas críticas se validan en servidor.
- Tiene tests y respeta las fronteras de dominio.
- Está integrada y otro integrante puede comprenderla.
- Está documentada si introduce decisiones importantes.
- El PR tiene una responsabilidad clara.

Estos criterios recogen la orientación de entrega integrada de DAR3 y añaden la
organización interna propuesta; no constituyen una cita textual del documento.

## 11. Git y mantenimiento del plan

Se mantienen las convenciones registradas: `main` estable, `develop` para
integración y ramas `feature/*`, `fix/*` y `docs/*`. Para integrar se requiere PR,
como práctica de revisión prevista en DAR3 y en esta guía operativa.

El plan debe actualizarse cuando se valide el reparto, cambie un hito, llegue
información del profesor, se acuerden contratos, cambien fronteras o se resuelvan
dependencias. Las decisiones definitivas importantes deberán registrarse también
en [decisions.md](decisions.md) cuando se aprueben; este plan no las confirma.
