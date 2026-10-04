# Registro de decisiones confirmadas

Este documento distingue las decisiones comunicadas por el profesor/equipo de
los requisitos atribuidos a DAR3. No incorpora propuestas como decisiones aprobadas.

## 1. Requisitos procedentes de DAR3

Según DAR3, sección 9 (páginas 48-50), el Equipo 5 se encarga de Ecomotor
y evolución, avatar e inventario, Ecommerce y DuckyBank, y del servicio común de
recompensas. Son requisitos de alcance, no decisiones de implementación.

Fuente consultada: `DAR3_ (1).pdf`, facilitado por el equipo y no copiado al
repositorio. Los requisitos se resumen en [architecture.md](architecture.md).
La sección 10 (páginas 50-53) requiere acordar el contrato de recompensas entre
el Equipo 5 y el Equipo 0; no implica que ese contrato esté ya decidido.

## 2. Decisiones confirmadas del profesor y del equipo

| ID | Decisión | Procedencia comunicada |
| --- | --- | --- |
| D-01 | Trabajar inicialmente en repositorios independientes por equipo y posteriormente integrar en el repositorio común del Equipo 0. | Indicación del profesor, confirmada por el equipo en esta tarea. |
| D-02 | `main` representa estados estables. | Contexto confirmado por el equipo en esta tarea. |
| D-03 | `develop` será la rama de integración del Equipo 5. | Contexto confirmado por el equipo en esta tarea. |
| D-04 | Usar ramas `feature/*`, `fix/*` y `docs/*` para el trabajo futuro. | Contexto confirmado por el equipo en esta tarea. |
| D-05 | El Equipo 0 es responsable del User, la autenticación y la integración global; el Equipo 5 no creará un User propio. | Contexto confirmado por el equipo en esta tarea. |
| D-06 | Limitar esta fase a la configuración documental del repositorio, sin implementar Django ni añadir dependencias. | Instrucción del equipo para esta tarea. |
| D-07 | Esperar y revisar el documento de decisiones de clase antes de fijar modelos, contratos de recompensas, reglas de XP o arquitectura funcional definitiva. | Instrucción del equipo para esta tarea. |

Estas decisiones se registran como contexto de trabajo. Su documentación no
implica que ya existan ramas, protecciones, contratos o mecanismos de integración.

La responsabilidad del Equipo 0 también aparece en DAR3, sección 4 (página 38)
y sección 10 (página 51). Las propuestas de perfiles y relaciones del PDF no
se convierten en modelos aprobados: prevalece la instrucción de no crear un
User propio y esperar el documento de clase para definir la integración.

## 3. Decisiones todavía pendientes

Las cuestiones sin resolver están en [pending-decisions.md](pending-decisions.md).
Cuando llegue el documento de clase, se contrastará con este registro y se
incorporarán los acuerdos confirmados indicando su fuente. Hasta entonces, las
cuestiones pendientes no deben tratarse como decisiones aprobadas.
