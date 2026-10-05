# Decisiones pendientes

Estado: estructura de usuarios y perfiles confirmada en clase; pendientes los
campos y las reglas de dominio, así como la documentación restante de clase.

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

En clase con el profesor, según lo comunicado por el equipo el 5 de octubre de
2026, se confirmó la app `users`, el User estándar de Django y los perfiles
específicos centralizados en `users/models.py`, con relación `OneToOneField`.
Se crean inicialmente `UserProfileEcomotor` y `UserProfileBank`, con relación a
`settings.AUTH_USER_MODEL` y borrado en cascada, sin campos de negocio ni signals.
No se hereda de `AbstractUser` ni se cambia `AUTH_USER_MODEL`. El profesor
integrará posteriormente autenticación, login y User global.

El bootstrap Django y `ecomotor` ya están integrados. Esta fase añade únicamente
la estructura de `users`, su migración inicial y tests. El registro completo de
decisiones y su procedencia está en [decisions.md](decisions.md).

## 3. Cuestiones todavía pendientes

Las siguientes cuestiones son puntos por aclarar, no propuestas aprobadas:

| Cuestión | Qué falta confirmar |
| --- | --- |
| Documentación restante de clase | Recibir y revisar los detalles de dominio; los acuerdos de estructura de perfiles ya comunicados quedan registrados. |
| Discrepancias de DAR3 | Contrastar los planes anteriores del PDF y sus referencias a otros repartos con las secciones 9 y 10 y los acuerdos de clase. |
| Arquitectura funcional | Organización de las áreas y sus límites de implementación. |
| Campos de perfiles | Campos concretos de `UserProfileEcomotor` y `UserProfileBank`; no se añaden XP, monedas, nivel, evolución, wallet ni otros datos de dominio. |
| Modelos de dominio | Entidades, relaciones y restricciones adicionales de las áreas del Equipo 5; la relación base de perfiles con el User ya está confirmada. |
| Integración global de identidad y autenticación | Detalles de la futura integración por el profesor; ya está decidido usar el User estándar y perfiles `OneToOneField`, sin implementar login en esta fase. |
| Recompensas | Acordar con el Equipo 0 el contrato del servicio y con los equipos 1 a 4 los resultados de entrada, conforme a la sección 10; concretar formatos, validación de origen y prevención de duplicados. |
| XP, DuckyCoins y demás lógica de negocio | Valores, umbrales y reglas concretas de progreso, recompensas, economía y evolución siguen sin decidirse; DAR3 establece capacidades, pero no se adoptan aquí parámetros ni implementaciones. |
| Integración en Equipo 0 | Procedimiento y acuerdos técnicos para incorporar el trabajo al repositorio común. |
| Entorno futuro | Acuerdos de entorno para la integración global; el bootstrap actual utiliza Django 5.2.17, sin añadir dependencias en esta fase. |

No se fijan valores de XP, DuckyCoins, formatos de contratos ni esquemas de datos
de dominio para estas cuestiones. La relación base de los perfiles es el único
esquema nuevo confirmado. Tras revisar la documentación restante de clase, se
registrarán los acuerdos confirmados y su procedencia en
[decisions.md](decisions.md), y se actualizará
[architecture.md](architecture.md) cuando corresponda.
