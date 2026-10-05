# DuckyArenas · Team 5

Repositorio del Equipo 5 del proyecto de clase DuckyArenas.

## Estado actual

Existe el proyecto Django con las apps `ecomotor` y `users` bajo `apps/`, los perfiles base
`UserProfileEcomotor` y `UserProfileBank`, migraciones y tests básicos. El
repositorio incluye documentación de arquitectura, decisiones y planificación.

Se utiliza el User estándar de Django; no se ha implementado autenticación local.

Todavía no hay lógica funcional de XP, evolución, recompensas, inventario,
tienda o economía. `main` representa estados estables y `develop` es la rama
de integración del Equipo 5.

## Requisitos procedentes de DAR3

Según DAR3, sección 9 (páginas 48-50), el Equipo 5 es responsable de:

- Ecomotor y evolución.
- Avatar e inventario.
- Ecommerce y DuckyBank.
- Servicio común de recompensas.

Fuente consultada: `DAR3_ (1).pdf`, facilitado por el equipo y no copiado al
repositorio. Los requisitos y sus referencias se resumen en
[architecture.md](docs/architecture.md); sus propuestas técnicas no se adoptan
como decisiones de implementación en esta fase.

## Decisiones confirmadas del profesor y del equipo

- Cada equipo trabajará inicialmente en un repositorio independiente, según lo
  indicado por el profesor. Después se integrará en el repositorio común del Equipo 0.
- `main` representa estados estables.
- `develop` es la rama de integración del Equipo 5.
- El trabajo futuro se realizará en ramas `feature/*`, `fix/*` y `docs/*`.
- El Equipo 0 es responsable del User, la autenticación y la integración global.
  El Equipo 5 no creará un User propio.

## Decisiones pendientes

Las cuestiones abiertas están centralizadas en
[docs/pending-decisions.md](docs/pending-decisions.md). El Equipo 5 puede avanzar
en su arquitectura interna; siguen pendientes parámetros oficiales, reglas
funcionales no definidas y contratos con otros equipos cuando corresponda.

## Documentación

- [Arquitectura: alcance y límites](docs/architecture.md).
- [Registro de decisiones](docs/decisions.md).
- [Decisiones pendientes](docs/pending-decisions.md).
- [Plan de trabajo del Equipo 5](docs/team5-work-plan.md): plan operativo, reparto propuesto, hitos, dependencias y backlog del Equipo 5.
