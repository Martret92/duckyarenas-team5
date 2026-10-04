# Decisiones pendientes

Estado: pendientes de revisar el documento de un integrante del equipo que
recoge las decisiones tomadas en clase con el profesor.

## 1. Requisitos procedentes de DAR3

El alcance del Equipo 5 comprende Ecomotor y evolución, avatar e inventario,
Ecommerce y DuckyBank, y el servicio común de recompensas: DAR3, sección 9
(páginas 48-50). Fuente consultada: `DAR3_ (1).pdf`, facilitado por el equipo
y no copiado al repositorio. Los requisitos se resumen en
[architecture.md](architecture.md).

## 2. Decisiones ya confirmadas

El trabajo empieza en repositorios independientes y después se integra en el
repositorio común del Equipo 0. `main` representa estados estables, `develop`
será la integración del Equipo 5 y se usarán ramas `feature/*`, `fix/*` y `docs/*`.
El User, la autenticación y la integración global corresponden al Equipo 0;
el Equipo 5 no creará un User propio.

Esta fase solo prepara documentación y exclusiones de Git. El registro completo
de decisiones y su procedencia está en [decisions.md](decisions.md).

## 3. Cuestiones todavía pendientes

Las siguientes cuestiones son puntos por aclarar, no propuestas aprobadas:

| Cuestión | Qué falta confirmar |
| --- | --- |
| Documento de clase | Recibirlo y revisar los acuerdos recogidos con el profesor. |
| Discrepancias de DAR3 | Contrastar los planes anteriores del PDF y sus referencias a otros repartos con las secciones 9 y 10 y los acuerdos de clase. |
| Arquitectura funcional | Organización de las áreas y sus límites de implementación. |
| Modelos | Entidades, relaciones y restricciones de las áreas del Equipo 5. |
| Identidad y autenticación | Forma de integrar las áreas del Equipo 5 con el User y la autenticación a cargo del Equipo 0. |
| Recompensas | Acordar con el Equipo 0 el contrato del servicio y con los equipos 1 a 4 los resultados de entrada, conforme a la sección 10; concretar formatos, validación de origen y prevención de duplicados. |
| XP y evolución | Valores, umbrales y reglas concretas de XP, recompensas, épocas, piezas y evolución; DAR3 exige estas capacidades, pero aquí no se fijan sus parámetros. |
| Integración en Equipo 0 | Procedimiento y acuerdos técnicos para incorporar el trabajo al repositorio común. |
| Entorno de desarrollo | Versiones, dependencias y configuración necesarias cuando se autorice la implementación. |

No se fijan valores de XP, formatos de contratos, esquemas de datos ni soluciones
técnicas para estas cuestiones. Tras revisar el documento de clase, se registrarán
los acuerdos confirmados y su procedencia en [decisions.md](decisions.md), y se
actualizará [architecture.md](architecture.md) cuando corresponda.
