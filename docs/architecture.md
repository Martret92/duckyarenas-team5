# Arquitectura: alcance y límites

El proyecto tiene una estructura base de usuarios y perfiles, sin lógica de
dominio implementada. Parte A dispone de una arquitectura interna V1 aceptada;
su detalle y los contratos compartidos aún no están documentados o validados aquí.

## 1. Requisitos procedentes de DAR3

Fuente consultada: `DAR3_ (1).pdf`, sección 9, páginas 48-50. La numeración de
páginas corresponde al PDF facilitado por el equipo, no copiado al repositorio.

| Área | Responsabilidad confirmada |
| --- | --- |
| Ecomotor y evolución | XP histórica, épocas y umbrales, desbloqueo de piezas, evolución automática, historial de épocas y equipamiento, Museo Ducky y preparación de especializaciones y XP de dominio. |
| Avatar e inventario | Catálogo e inventario, equipar y desequipar, impedir objetos incompatibles en una zona, distinguir seis piezas principales de complementos estéticos y mostrar la apariencia en perfil y home. |
| Ecommerce y DuckyBank | Cartera de DuckyCoins, historial, tienda estética, compras validadas en servidor con saldo suficiente, actualización conjunta de saldo/transacción/inventario y protección ante reenvíos. |
| Recompensas | Recibir resultados validados de los equipos 1 a 4, comprobar origen e identidad, evitar recompensar dos veces una actividad, registrar el evento, conceder XP y monedas, desbloquear o evolucionar cuando corresponda y devolver un resumen. |

Para la demostración, DAR3 contempla Prehistoria, Grecia y Roma. Techies y la
cotización variable quedan fuera de la primera entrega (sección 9).
La demostración mínima recorre una actividad de QuizArenas, la recompensa, el
desbloqueo de una pieza, la compra y el equipamiento de un accesorio, con historial.

La sección 10 (páginas 50-53) atribuye el acuerdo del contrato de recompensas al
Equipo 5 junto con el Equipo 0. Cada equipo de juego aporta su formato de resultados;
el catálogo de épocas y piezas corresponde al Equipo 5. El documento enumera
información mínima a intercambiar, pero aún no se ha definido una API,
una firma de función ni un esquema de datos definitivo.

Estos requisitos orientan el trabajo futuro; no implican adoptar las propuestas
técnicas de dominio del PDF.

DAR3 distingue Parte A (Ecomotor y evolución), Parte B (Avatar e inventario),
Parte C (Ecommerce y DuckyBank) y el servicio común de recompensas. No asigna
individualmente estas partes a los tres integrantes. Define capacidades de XP,
épocas, evolución y recompensas, pero no proporciona todos los valores numéricos
definitivos; las tablas y datos oficiales pendientes se solicitarán al profesor.

## 2. Estructura actual y límites conocidos

El proyecto Django utiliza el paquete de configuración `config`. Están
registradas las apps `ecomotor`, todavía provisional, y `users`.

Según lo acordado en clase con el profesor, `users` utiliza el User estándar de
Django, sin User personalizado ni herencia de `AbstractUser`. Los perfiles
específicos del Equipo 5 se centralizan en `users/models.py`: inicialmente
`UserProfileEcomotor` y `UserProfileBank`, relacionados uno a uno con el usuario
(D-09 y D-11).

Como elección técnica de implementación del Equipo 5, cada perfil contiene un
identificador automático y una relación `user` con `settings.AUTH_USER_MODEL`,
usando `on_delete=models.CASCADE`. No se ha modificado `AUTH_USER_MODEL`, no hay
campos de negocio ni signals para crear perfiles automáticamente (D-12).
La migración inicial y los tests verifican la creación y unicidad de ambos perfiles.

El Equipo 5 no implementará login ni autenticación en este repositorio temporal.
La integración global de usuarios y autenticación corresponde al proyecto común,
a cargo del profesor y del Equipo 0 (D-05 y D-10).

No hay todavía lógica de XP, épocas, evolución, recompensas, inventario ni economía.
Los acuerdos confirmados y las decisiones técnicas se registran en
[decisions.md](decisions.md).

Parte A ha aceptado internamente su arquitectura V1, identificada como A-01…A-16.
Su contenido no está disponible en este repositorio y no se reconstruye en este
documento. Se documentará desde «01 · Ecomotor y evolución»; su ERD revisado y
diccionario de datos se incorporarán en un PR documental posterior, antes de
implementar nuevos modelos. Esta aceptación interna no aprueba los contratos
compartidos con B/C ni Rewards, que requieren validación conjunta.

## 3. Aclaraciones funcionales conocidas de clase

Las siguientes reglas proceden de las aclaraciones de clase y la información
funcional disponible. No son citas textuales de DAR3 cuando este no las detalla.

El progreso histórico comprende los niveles 1–9: Prehistoria, Grecia, Roma,
Edad Media, Renacimiento, Revolución Industrial, Siglo XX, Era Espacial y Era
Digital. El usuario comienza en Prehistoria. La XP histórica es acumulativa y no
se gasta; una barra visual puede mostrar progreso relativo hacia el siguiente
nivel sin sustituir ni reducir esa XP. Los umbrales oficiales siguen pendientes.

Cada época tiene seis piezas principales. Al iniciar el juego se conceden y
equipan las seis de Prehistoria. Al evolucionar se conceden juntas las seis de
la nueva época y se equipa automáticamente ese set. Los sets anteriores se
conservan y pueden reequiparse libremente: la apariencia es independiente de
la época real y del progreso. Las piezas históricas no se compran con DuckyCoins.

Si una concesión de XP cruza varios umbrales, deben procesarse y registrarse todas
las evoluciones intermedias y concederse todos sus sets. Queda equipado el set
de la época más avanzada alcanzada, sin omitir el historial intermedio.

El progreso por especialización se separa del histórico. Tras Era Digital se
puede elegir Developer, Ciberseguridad, AdminSys, Gamer o Data & AI. Cada una
conserva su rango independiente (Inicial, Junior, Middle, Senior, Master).
Cambiar de especialización volviendo al punto de Era Digital no elimina XP
histórica ni progreso previo. La especialización activa y sus rangos no deben
tratarse como una continuación obligatoria del nivel histórico. Siguen pendientes
la XP de dominio, los requisitos de rangos y la transición técnica del cambio.

Los sets históricos son permanentes y distintos de los objetos de combate.
Estos últimos son consumibles comprados con DuckyCoins y admiten múltiples
unidades; se conocen inicialmente tres de ataque y tres de defensa. Efectos,
precios y utilización concreta por cada juego siguen pendientes.
El diseño interno V1 de Parte A está aceptado, pendiente de documentar en detalle.
Los modelos concretos del conjunto del proyecto y sus contratos compartidos no
se dan por definidos mediante estas aclaraciones.

El recorrido operativo, los hitos y las dependencias están en
[team5-work-plan.md](team5-work-plan.md), como propuesta para revisión conjunta.

## 4. Propuestas arquitectónicas pendientes de validación

D-13 a D-16 son propuestas internas pendientes de validación por los tres
integrantes del Equipo 5, incluida la confirmación con Félix y Henry.

### Reparto interno y coordinación de recompensas

D-13 propone este reparto, que no constituye una asignación individual de DAR3:

| Responsable principal propuesto | Parte |
| --- | --- |
| Jaime | Parte A: Ecomotor y evolución. |
| Félix | Parte B: Avatar e inventario. |
| Henry | Parte C: Ecommerce y DuckyBank. |

D-14 propone que recompensas sea responsabilidad compartida del Equipo 5, con
coordinación inicial del contrato y la orquestación desde Parte A. Las operaciones
de inventario y economía serían proporcionadas por B y C, respectivamente.

### Fronteras entre áreas

D-15 propone estas fronteras iniciales, revisables:

- Parte A: XP, épocas y evolución.
- Parte B: catálogo, inventario y equipamiento.
- Parte C: DuckyCoins, wallet, transacciones, tienda y compras.
- Recompensas: orquestar las áreas sin duplicar su lógica de negocio.

Las fronteras propuestas no fijan los modelos internos ni el contrato técnico.

### Datos provisionales

Mientras no se disponga de los datos oficiales, se propone utilizar valores
provisionales para desarrollo y pruebas (D-16):

- Identificarlos como datos provisionales o de demostración, nunca como requisitos reales.
- Mantenerlos separados de la lógica de negocio para poder sustituirlos.
- Evitar números mágicos en los servicios.
- Permitir umbrales y recompensas propios en los tests, solo para verificar comportamiento.

La arquitectura se diseñaría para sustituir valores puramente paramétricos,
como umbrales y cantidades de recompensa, por datos oficiales sin modificar
la lógica de negocio. Si el profesor cambia también las reglas funcionales,
se revisaría la arquitectura correspondiente.

## 5. Impacto de PR07: estructura, proceso y evaluación

Fuente directa: Documento PR07 · Ciclo de vida de una aplicación web, facilitado
por el profesor (17 páginas), no copiado al repositorio. DAR3 sigue siendo la
fuente funcional principal. PR07 complementa el proyecto con requisitos y criterios de estructura, proceso, entregables y
evaluación; no sustituye automáticamente los acuerdos de clase ni decide la
arquitectura funcional del Equipo 5.

PR07 sitúa las aplicaciones bajo `apps/` (páginas 4-6). Actualmente `ecomotor/`
y `users/` están en raíz. Su reorganización es una adaptación técnica pendiente;
este PR documental no mueve apps ni cambia configuración, modelos o migraciones.

Antes de implementar nuevos modelos, PR07 pide un ERD y un diccionario de datos,
con entidades, cardinalidades y reglas `on_delete` documentadas (página 5).
Después contempla modelos y migraciones, registro de modelos principales en
Admin, URLs y vistas, templates y navegación, listados y detalles, formularios
y CRUD de al menos dos entidades principales (páginas 6-9). El alcance concreto
del CRUD evaluable debe aclararse con el profesor, sin suponer que autoriza a
editar directamente estados derivados o historiales de dominio.

Incluye permisos, seguridad y tests, así como evidencia mediante Git y PR y
aportaciones identificables de cada integrante (páginas 10-11 y 17). Estos trabajos
se incorporan al [plan operativo](team5-work-plan.md), sin implementarlos aquí.

### Contradicción sobre usuarios y autenticación

El plan detallado de PR07 pide `apps/users`, extender `AbstractUser`, configurar
`AUTH_USER_MODEL` e implementar registro, login y logout (página 5). Esto contradice
D-09 y D-10. El resumen inicial menciona el usuario personalizado de forma
condicional (página 1), por lo que tampoco resuelve por sí solo esa contradicción.

Hasta aclararlo con el profesor se mantienen D-09 y D-10: User estándar, sin
CustomUser ni autenticación local. No se cambia `AUTH_USER_MODEL` ni se modifican
migraciones. Cualquier cambio posterior se registrará como nueva decisión.
También debe aclararse si los 15 días y sus entregables Git son un calendario
literal obligatorio o una guía/rúbrica: PR07 utiliza ambas formulaciones.
Las preguntas se recogen en [pending-decisions.md](pending-decisions.md).

## 6. Límites todavía sin resolver

DAR3 define requisitos funcionales sobre XP, evolución y economía, pero no fija
la estructura definitiva de los perfiles ni todos sus campos y parámetros.
Falta documentar el diseño interno aceptado de Parte A e incorporar su ERD
revisado. Siguen pendientes los diseños no aceptados y los contratos compartidos,
las reglas no resueltas por las aclaraciones funcionales anteriores, así como los
datos oficiales, el contrato de recompensas y su integración. La existencia de
un servicio común no determina su implementación ni su forma de comunicación.

Los planes técnicos antiguos de DAR3 (páginas 19-31) y las propuestas internas
del equipo pueden utilizarse como referencia, pero no se adoptan automáticamente.
Las propuestas sobre organización por apps, reparto o contrato de recompensas
no constituyen requisitos oficiales ni decisiones aprobadas mientras no se
registren como tales.

La arquitectura interna corresponde al Equipo 5 y puede seguir diseñándose.
Debe respetar DAR3, las aclaraciones funcionales conocidas, los condicionantes
de PR07 y las necesidades de integración. La aceptación interna V1 de Parte A
no fija por sí sola la estructura del conjunto ni un contrato técnico de Rewards.

Las cuestiones abiertas se mantienen en
[pending-decisions.md](pending-decisions.md).
