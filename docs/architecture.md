# Arquitectura: alcance y límites

Estado: documentación inicial. No define una arquitectura funcional definitiva.

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

Estos son requisitos para el trabajo futuro. No se crean modelos, endpoints,
apps Django ni despliegues, y no se adoptan las propuestas técnicas del PDF.

## 2. Decisiones confirmadas del profesor y del equipo

El profesor ha indicado que cada equipo trabajará inicialmente en un repositorio
independiente y que posteriormente se integrará en el repositorio común del Equipo 0.

El Equipo 0 es responsable del User, la autenticación y la integración global.
El Equipo 5 no creará un User propio. La forma de referenciar o consumir esa
identidad se decidirá cuando estén disponibles las decisiones de clase y la
coordinación correspondiente.

`main` representa estados estables y `develop` será la rama de integración del
Equipo 5. Las ramas futuras usarán `feature/*`, `fix/*` o `docs/*` según el trabajo.

La preparación actual se limita al README, las reglas de exclusión de Git y esta
documentación. No incorpora dependencias ni estructura de aplicación.

## 3. Decisiones pendientes

Quedan pendientes la estructura funcional, los modelos y sus relaciones, los
contratos de recompensas, las reglas de XP y los mecanismos de integración.
La existencia de un servicio común de recompensas no determina por sí sola su
implementación ni su forma de comunicación.

El PDF contiene planes anteriores con referencias a otros repartos de equipos,
modelos y funciones concretas (por ejemplo, páginas 19-31), además del reparto
de la sección 9. Esas diferencias se contrastarán con el documento de clase;
no se trasladan como acuerdos definitivos a este repositorio.

Antes de concretarlos, se revisará el documento pendiente que recoge lo acordado
en clase con el profesor. Véase [el registro de cuestiones pendientes](pending-decisions.md).
