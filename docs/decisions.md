# Registro de decisiones

Este es el registro principal de acuerdos y decisiones técnicas. Las propuestas
pendientes se mantienen separadas de las decisiones confirmadas.

## Requisitos de referencia: DAR3

DAR3, sección 9 (páginas 48-50), asigna al Equipo 5 Ecomotor y evolución, avatar e
inventario, Ecommerce y DuckyBank, y el servicio común de recompensas. No asigna
individualmente estas partes a los integrantes.

La sección 10 (páginas 50-53) requiere acordar el contrato de recompensas entre
el Equipo 5 y el Equipo 0; no implica que ese contrato esté ya decidido.
Fuente: `DAR3_ (1).pdf`, consultado y no copiado al repositorio. El alcance y los
requisitos se resumen en [architecture.md](architecture.md).

## Decisiones confirmadas

`Vigente` indica que la decisión sigue aplicándose. `Cumplida` identifica una
decisión limitada a una fase ya ejecutada. `Superada` se reserva para decisiones
reemplazadas claramente por otras; ninguna se clasifica así actualmente.

| ID | Decisión | Origen | Estado |
| --- | --- | --- | --- |
| D-01 | Trabajar inicialmente en repositorios independientes por equipo y posteriormente integrar en el repositorio común del Equipo 0. | Profesor / clase | Vigente |
| D-02 | `main` representa estados estables. | Equipo 5 | Vigente |
| D-03 | `develop` es la rama de integración del Equipo 5. | Equipo 5 | Vigente |
| D-04 | Usar ramas `feature/*`, `fix/*` y `docs/*` para el trabajo. | Equipo 5 | Vigente |
| D-05 | El Equipo 0 es responsable del User, la autenticación y la integración global; el Equipo 5 no creará un User propio. | Profesor / clase | Vigente |
| D-06 | Limitar el setup inicial a la configuración documental del repositorio, sin implementar Django ni añadir dependencias en aquella fase. | Equipo 5 | Cumplida |
| D-07 | No fijar como definitivos los modelos de dominio, contratos de recompensas, reglas de XP o arquitectura funcional que dependan de decisiones todavía pendientes del profesor o del equipo. | Equipo 5 | Vigente |
| D-08 | Crear el bootstrap Django en `config` y la app provisional `ecomotor`, con Django 5.2.17, sin lógica de dominio. | Equipo 5 | Cumplida |
| D-09 | Crear la app Django `users` y utilizar el User estándar de Django, sin crear un User personalizado ni heredar de `AbstractUser`. | Profesor / clase | Vigente |
| D-10 | El Equipo 5 no implementará login ni autenticación en su repositorio temporal; la integración global de usuarios y autenticación se realizará posteriormente en el proyecto común. | Profesor / clase | Vigente |
| D-11 | Centralizar en `users/models.py` los perfiles específicos del Equipo 5, inicialmente `UserProfileEcomotor` y `UserProfileBank`, relacionados uno a uno con el usuario. | Profesor / clase | Vigente |
| D-12 | En la implementación inicial, los perfiles contienen únicamente la relación con el usuario, además del identificador automático. Se utiliza `settings.AUTH_USER_MODEL` con `on_delete=models.CASCADE` y no se añaden todavía campos de negocio ni signals de creación automática. | Implementación del Equipo 5 | Vigente |

D-06 y D-08 corresponden al setup y al bootstrap ya ejecutados. D-07 permite
avanzar sin dar por definitivos los aspectos sujetos a decisiones pendientes.
D-09 a D-11 resuelven la estructura base de
usuarios y perfiles, sin decidir las reglas de negocio. Los detalles técnicos
de D-12 son elecciones de implementación del Equipo 5, no acuerdos atribuidos
al profesor. La integración global sigue a cargo del profesor y del Equipo 0.

## Propuestas pendientes de validación

D-13 a D-16 requieren validación por los tres integrantes del Equipo 5, incluida
la confirmación con Félix y Henry. No son decisiones definitivas.

| ID | Propuesta | Origen | Validación pendiente |
| --- | --- | --- | --- |
| D-13 | Establecer inicialmente a Jaime como responsable principal de Parte A (Ecomotor y evolución), Félix de Parte B (Avatar e inventario) y Henry de Parte C (Ecommerce y DuckyBank). | Propuesta interna | Tres integrantes del Equipo 5, incluida la confirmación con Félix y Henry. DAR3 no asigna individualmente estas partes. |
| D-14 | Mantener el servicio común de recompensas como responsabilidad compartida. Vincular la coordinación inicial del contrato/orquestación a Parte A; B y C proporcionarían las operaciones de inventario y economía, respectivamente. | Propuesta interna | Tres integrantes del Equipo 5, incluida la confirmación con Félix y Henry. |
| D-15 | Adoptar fronteras iniciales revisables: A sería propietaria de XP, épocas y evolución; B de catálogo, inventario y equipamiento; C de DuckyCoins, wallet, transacciones, tienda y compras. Recompensas orquestaría sin duplicar lógica de negocio. | Propuesta interna | Tres integrantes del Equipo 5, incluida la confirmación con Félix y Henry. No fija modelos ni contrato técnico definitivo. |
| D-16 | Permitir datos ficticios/provisionales de desarrollo y demostración hasta recibir datos oficiales del profesor, identificados como provisionales, nunca como requisitos reales y separados de la lógica. Evitar números mágicos en servicios. Los tests podrían usar umbrales y recompensas propios solo para verificar comportamiento. | Propuesta interna | Tres integrantes del Equipo 5, incluida la confirmación con Félix y Henry. DAR3 no proporciona todos los valores numéricos definitivos. |

Como parte de D-16, la arquitectura se diseñaría para sustituir valores puramente
paramétricos, como umbrales y cantidades de recompensa, por datos oficiales sin
modificar la lógica de negocio. Si el profesor cambia también las reglas
funcionales, se revisaría la arquitectura correspondiente. No se fijan valores
concretos ni se resuelven las reglas pendientes mediante esta propuesta.

El detalle arquitectónico está en [architecture.md](architecture.md). Las
cuestiones sin resolver se mantienen en
[pending-decisions.md](pending-decisions.md).
