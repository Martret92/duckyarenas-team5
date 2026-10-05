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
| D-06 | Limitar el setup inicial a la configuración documental del repositorio, sin implementar Django ni añadir dependencias en aquella fase. | Instrucción del equipo para el setup inicial. |
| D-07 | Esperar las decisiones de clase antes de fijar modelos de dominio, contratos de recompensas, reglas de XP o arquitectura funcional definitiva. | Instrucción del equipo para el setup inicial; la estructura base de perfiles se confirma posteriormente en D-09 a D-12. |
| D-08 | Crear el bootstrap Django en `config` y la app provisional `ecomotor`, con Django 5.2.17, sin lógica de dominio. | Bootstrap aprobado e integrado por el equipo en el PR #1. |
| D-09 | Crear la app Django `users` y utilizar el User estándar de Django, sin User propio, sin heredar de `AbstractUser` y sin cambiar `AUTH_USER_MODEL`. | Decisión tomada en clase con el profesor, comunicada por el equipo el 5 de octubre de 2026. |
| D-10 | El profesor integrará posteriormente login, autenticación y User global. | Decisión tomada en clase con el profesor, comunicada por el equipo el 5 de octubre de 2026. |
| D-11 | Centralizar los perfiles específicos de cada ámbito en `users/models.py`, relacionados con `settings.AUTH_USER_MODEL` mediante `OneToOneField` y `on_delete=models.CASCADE`. | Decisión tomada en clase con el profesor, comunicada por el equipo el 5 de octubre de 2026; parámetros de relación confirmados para esta tarea. |
| D-12 | Crear inicialmente `UserProfileEcomotor` y `UserProfileBank`, sin campos de negocio ni signals de creación automática. | Perfiles confirmados en clase con el profesor; límites de implementación indicados por el equipo para esta tarea. |

Las decisiones conservan su procedencia y el alcance de cada fase. El bootstrap
ya está integrado; esta fase incorpora `users`, los dos perfiles y su migración
inicial. No se han definido contratos de recompensas ni mecanismos de integración
global por el mero hecho de documentarlos.

La responsabilidad del Equipo 0 también aparece en DAR3, sección 4 (página 38)
y sección 10 (página 51). La estructura de perfiles se basa en los nuevos acuerdos
de clase D-09 a D-12, no en adoptar automáticamente los modelos propuestos en el
PDF. Se mantiene la responsabilidad del profesor sobre la integración global.

## 3. Decisiones todavía pendientes

Las cuestiones sin resolver están en [pending-decisions.md](pending-decisions.md).
Los campos concretos de `UserProfileEcomotor` y `UserProfileBank` siguen pendientes.
XP, DuckyCoins y demás lógica de negocio todavía no se han decidido. Cuando llegue
la documentación restante de clase, se contrastará con este registro y se
incorporarán los acuerdos confirmados indicando su fuente. Las cuestiones
pendientes no deben tratarse como decisiones aprobadas.
