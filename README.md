# duckyarenas-team5

Repositorio del Equipo 5 del proyecto de clase DuckyArenas.

## Estado actual

Esta fase prepara únicamente el repositorio y su documentación. Todavía no hay
proyecto Django, apps, modelos, migraciones, dependencias ni lógica de negocio.
No hay instrucciones de instalación o ejecución porque aún no existe una aplicación.

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
- `develop` será la rama de integración del Equipo 5.
- El trabajo futuro se realizará en ramas `feature/*`, `fix/*` y `docs/*`.
- El Equipo 0 es responsable del User, la autenticación y la integración global.
  El Equipo 5 no creará un User propio.

Estas convenciones documentan el trabajo futuro; esta preparación no crea ramas
ni configura protecciones de ramas.

## Decisiones pendientes

Estamos esperando el documento de un integrante del equipo que recoge las
decisiones tomadas en clase con el profesor. Hasta revisarlo, no se fijan modelos,
contratos de recompensas, reglas de XP ni arquitectura funcional definitiva.

## Documentación

- [Arquitectura: alcance y límites confirmados](docs/architecture.md).
- [Decisiones confirmadas y procedencia](docs/decisions.md).
- [Decisiones pendientes](docs/pending-decisions.md).
