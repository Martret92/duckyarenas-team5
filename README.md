# DuckyArenas · Team 5

Repositorio del Equipo 5 del proyecto de clase DuckyArenas.

## Estado actual

Baseline verificada el 18/10/2026: `develop` en
`b42cb5fdd5c4509670a337c1c79e260714c78c9f`, con S7-A integrado por
[PR #32](https://github.com/Martret92/duckyarenas-team5/pull/32).

Parte A incluye progresión pura S1/S1.1, catálogos y perfiles de Día 4, estadísticas,
historiales y migraciones; Admin seguro de Día 5; inicialización local atómica e
idempotente S2-A; concesión transaccional de XP, puntos de nivel y evolución S3;
consultas internas S4-A; página personal de lectura S5-A; carga explícita de JSON
y diagnóstico S6-A; asignación de puntos solo en Actual, coste 1:1 e historial
idempotente `StatAllocationEvent` S7-A (`0005_stat_allocation_event`).
Las PR y contratos de cada incremento están en el
[estado vigente de arquitectura](docs/architecture.md#21-estado-vigente-de-implementación--doc-1).

Se mantienen `apps.ecomotor` y `apps.users`, User estándar de Django y el perfil
`UserProfileBank` sin integración económica. La vista personal usa autenticación
Django existente y `request.user`; su URL local aún no está montada en las rutas
globales. No se ha añadido login propio ni autenticación paralela a Core.

Rewards, Bank/Shop, Duckies y juegos no están integrados. S8-A está aprobado
internamente y pausado, sin implementar. La configuración inicial sigue ausente:
S6-A carga un candidato, sin instalarlo ni aprobar valores funcionales. La presencia
de servicios y migraciones no habilita por sí sola su uso real con jugadores.

Última regresión comunicada: **407 tests correctos**; no se ha vuelto a ejecutar
la suite en DOC-1, que solo cambia documentación. `main` representa estados
estables y `develop` es la rama de integración del Equipo 5.

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
- [Plan de trabajo del Equipo 5](docs/team5-work-plan.md): plan operativo, reparto interno acordado, hitos, dependencias y backlog del Equipo 5.
