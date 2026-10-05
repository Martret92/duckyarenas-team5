# Arquitectura: alcance y límites

Estado: bootstrap Django y estructura de perfiles confirmada en clase.
No define una arquitectura funcional definitiva.

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
información mínima a intercambiar, pero esta preparación no define una API,
una firma de función ni un esquema de datos definitivo.

Estos son requisitos para el trabajo futuro. Las decisiones de clase que se
recogen a continuación solo concretan la estructura base de usuarios y perfiles;
no se adoptan las propuestas técnicas de dominio del PDF.

DAR3 distingue Parte A (Ecomotor y evolución), Parte B (Avatar e inventario),
Parte C (Ecommerce y DuckyBank) y el servicio común de recompensas. No asigna
individualmente estas partes a los tres integrantes. Define capacidades de XP,
épocas, evolución y recompensas, pero no proporciona todos los valores numéricos
definitivos; las tablas y datos oficiales pendientes se solicitarán al profesor.

## 2. Decisiones confirmadas del profesor y del equipo

El profesor ha indicado que cada equipo trabajará inicialmente en un repositorio
independiente y que posteriormente se integrará en el repositorio común del Equipo 0.

El Equipo 0 es responsable del User, la autenticación y la integración global.
En la reunión con el profesor, comunicada por el equipo el 5 de octubre de 2026,
se confirmó crear la app Django `users` y seguir utilizando el User estándar de
Django. No se crea un User propio, no se hereda de `AbstractUser` y no se modifica
`AUTH_USER_MODEL`. El profesor integrará posteriormente autenticación, login y
User global.

Los datos específicos de cada ámbito se conectan al usuario mediante perfiles
con `OneToOneField`, centralizados en `users/models.py`. Para el Equipo 5 se
confirman `UserProfileEcomotor` y `UserProfileBank`. Cada uno contiene únicamente
su identificador automático y una relación `user` con `settings.AUTH_USER_MODEL`
y `on_delete=models.CASCADE`. Esto permite un perfil de cada tipo por usuario.
No se generan perfiles automáticamente mediante signals.

`main` representa estados estables y `develop` será la rama de integración del
Equipo 5. Las ramas futuras usarán `feature/*`, `fix/*` o `docs/*` según el trabajo.

El repositorio contiene el proyecto Django con configuración en `config`, la app
provisional `ecomotor` y la app `users` registrada en `INSTALLED_APPS`. Esta fase
añade la migración inicial de los dos perfiles y tests de creación y unicidad,
sin implementar autenticación ni lógica de dominio.

## 3. Propuestas internas pendientes de validación por el Equipo 5

Las propuestas D-13 a D-16 están pendientes de confirmar con Félix y Henry y de
validación por los tres integrantes del Equipo 5; no son decisiones definitivas.

### Propuesta de reparto interno

La siguiente distribución es una propuesta de reparto interno pendiente de validación por el Equipo 5
(D-13), no una asignación individual realizada por DAR3:

| Responsable principal propuesto | Parte |
| --- | --- |
| Jaime | Parte A: Ecomotor y evolución. |
| Félix | Parte B: Avatar e inventario. |
| Henry | Parte C: Ecommerce y DuckyBank. |

Se propone que el servicio común de recompensas sea responsabilidad compartida del Equipo 5.
La coordinación inicial de su contrato y orquestación se vincularía a Parte A;
las operaciones de inventario y economía deberán ser proporcionadas por las
partes B y C, respectivamente, si se valida la propuesta D-14.

### Fronteras arquitectónicas iniciales, revisables

Estas fronteras se proponen en D-15 y están pendientes de validación por el Equipo 5:

- Parte A es propietaria de XP, épocas y evolución.
- Parte B es propietaria del catálogo, inventario y equipamiento.
- Parte C es propietaria de DuckyCoins, wallet, transacciones, tienda y compras.
- El servicio de recompensas orquesta estas áreas sin duplicar su lógica de negocio.

Estas fronteras no fijan los modelos internos ni el contrato técnico definitivo.

### Política de datos provisionales

Hasta recibir las tablas y datos oficiales del profesor, D-16 propone usar
valores ficticios o provisionales para desarrollar y probar (D-16):

- Nunca se documentarán como requisitos reales.
- Se identificarán claramente como datos provisionales o de demostración.
- Se mantendrán separados de la lógica de negocio para poder sustituirse.
- No se introducirán números mágicos en los servicios.
- Los tests podrán usar umbrales y recompensas propios, exclusivamente para
  verificar comportamiento.

La arquitectura se diseñará para que los valores puramente paramétricos —por ejemplo, umbrales y cantidades de recompensa— puedan sustituirse por los datos oficiales sin modificar la lógica de negocio. Si el profesor modifica también las reglas funcionales, se revisará la arquitectura correspondiente.

Esta propuesta de política no establece valores concretos de XP,
DuckyCoins o umbrales, ni decide las reglas de dominio todavía pendientes.

## 4. Decisiones pendientes

Validación del reparto interno y fronteras D-13 a D-16 por los tres integrantes del Equipo 5.

Quedan pendientes los campos concretos de `UserProfileEcomotor` y
`UserProfileBank`, los demás modelos de dominio, la estructura funcional, los
contratos de recompensas y los mecanismos de integración. Las reglas de XP,
DuckyCoins, nivel, evolución, wallet y demás lógica de negocio todavía no se
han decidido ni implementado. DAR3 define requisitos funcionales sobre XP, evolución y economía, pero no fija la estructura definitiva de estos perfiles ni todos los campos y parámetros concretos.
La existencia de un servicio común de recompensas no determina por sí sola su
implementación ni su forma de comunicación.

Siguen pendientes los umbrales reales de XP por época, las cantidades reales de
XP por actividad y de DuckyCoins, el catálogo y las reglas definitivas de
desbloqueo de piezas, las reglas de especializaciones y XP de dominio, el contrato
técnico definitivo de recompensas, los modelos internos definitivos de
XP/evolución, la clave definitiva de idempotencia y los detalles de integración
con los equipos 0–4. El uso de datos provisionales no resuelve estos acuerdos.

El PDF contiene planes anteriores con referencias a otros repartos de equipos,
modelos y funciones concretas (por ejemplo, páginas 19-31), además del reparto
de la sección 9. Esas diferencias se contrastarán con el documento de clase;
no se trasladan como acuerdos definitivos a este repositorio.

Los acuerdos de estructura de perfiles ya comunicados se aplican en esta fase.
Para concretar el dominio se espera la documentación restante y los acuerdos con
el profesor. Véase [el registro de cuestiones pendientes](pending-decisions.md).
