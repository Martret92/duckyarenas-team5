# Decisiones pendientes

Este documento reúne cuestiones abiertas y tareas documentales o de adaptación
pendientes. La estructura base vigente de usuarios y perfiles está registrada en D-09 a D-12 del
[registro de decisiones](decisions.md). El alcance de DAR3 y la estructura
actual se describen en [architecture.md](architecture.md).

## 1. Propuestas pendientes de validación

D-13 a D-16 requieren validación por los tres integrantes del Equipo 5, incluida
la confirmación con Félix y Henry:

- **D-13:** reparto de responsabilidades A/B/C: Jaime, Félix y Henry, respectivamente.
- **D-14:** responsabilidad compartida de recompensas, coordinación inicial desde A
  y operaciones de inventario y economía proporcionadas por B y C.
- **D-15:** fronteras iniciales entre A/B/C y orquestación sin duplicar lógica.
- **D-16:** política de datos provisionales, identificados y separados de la lógica,
  sin números mágicos y con datos propios de tests. Sustitución de parámetros por
  datos oficiales y revisión de arquitectura si cambian las reglas funcionales.

El contenido completo de las propuestas está en [decisions.md](decisions.md).
El [plan de trabajo](team5-work-plan.md) propone además hitos, backlog, autonomía
y revisión conjunta. Su validación no está implícita en la documentación del plan.

## 2. Arquitectura interna: documentación y diseño pendientes

Las reglas funcionales conocidas están en [architecture.md](architecture.md).
Ya están aclarados el progreso histórico 1–9, la XP acumulativa que no se gasta
y su separación de la barra visual; el set inicial de Prehistoria, la concesión
conjunta de seis piezas, el equipamiento automático, la conservación y
reutilización de sets sin cambiar progreso; las evoluciones múltiples; la
separación y conservación del progreso por especialización y la posibilidad de
cambiarla; y la separación de sets históricos y consumibles con cantidades.
No se mantienen estas reglas como preguntas abiertas.

Parte A ya tiene una arquitectura interna V1 aceptada (A-01…A-16). Falta
documentar su detalle desde «01 · Ecomotor y evolución» e incorporar su ERD y
diccionario revisados en un PR documental posterior. No se reconstruye aquí su
contenido ni se presenta toda Parte A como aún sin diseñar.

Los siguientes ámbitos deben quedar documentados y revisados por el Equipo 5
antes de implementar modelos. Para Parte A, esto significa incorporar el diseño
aceptado; para los diseños aún abiertos, tomar las decisiones técnicas necesarias,
sin esperar modelos concretos del profesor ni tratarlos como bloqueos externos:

- Modelo Django del XP acumulado e historial, su ubicación y relación con perfiles.
- Modelos de épocas, época actual e historial de evolución, incluidos los eventos
  de evoluciones múltiples.
- Modelos de catálogo, sets, piezas, inventario, equipamiento y cantidades de consumibles.
- Modelos de wallet, transacciones, catálogo comercial, tienda y compras.
- Representación separada de especialización activa y progreso/rango conservado
  de cada especialización; operación para volver al punto de Era Digital y cambiarla.
- Campos concretos de `UserProfileEcomotor` y `UserProfileBank`, y los demás
  modelos, relaciones y restricciones que no estén cubiertos por los puntos anteriores.
- Contratos internos A/B/C, consistencia entre operaciones, idempotencia técnica
  y concurrencia, para revisión conjunta durante la arquitectura.

### Reglas funcionales todavía abiertas

- Reglas de XP de dominio y requisitos/umbrales para progresar desde la especialización elegida a Junior, Middle, Senior y Master.
- Uso concreto de consumibles y sus efectos en cada modo de juego.
- Encaje de la tienda estética descrita en DAR3 con el catálogo de combate de las
  aclaraciones de clase, manteniendo los sets históricos no comprables.
- Aclarar las diferencias entre los planes anteriores de DAR3 y sus secciones
  9 y 10 cuando afecten a reglas no resueltas por las aclaraciones conocidas.

## 3. Datos oficiales pendientes

- Umbrales reales de XP por época.
- XP real concedida por actividades.
- Cantidades reales de DuckyCoins.
- Catálogo y contenido definitivo de los seis elementos de cada set histórico.
- Parámetros oficiales de especializaciones y XP de dominio.
- Contenido definitivo de sets y objetos, precios y efectos definitivos de consumibles.

Los valores provisionales no equivalen a requisitos oficiales. No se fijan
cantidades ni umbrales concretos en estos documentos.
Una cuestión puramente paramétrica no debe bloquear el desarrollo: el plan
propone datos de prueba identificados y separados de la lógica, bajo la política
D-16 aún pendiente de validación. Cambios de reglas funcionales requieren revisión.

## 4. Integración pendiente

- Contrato técnico del servicio común de recompensas: formatos, validación de
  origen y coordinación entre el Equipo 5 y el Equipo 0.
- Clave definitiva de idempotencia para evitar recompensas duplicadas.
- Integración con el Equipo 0: usuarios y autenticación global, incorporación al
  repositorio común y acuerdos de entorno.
- Integración con los equipos 1–4: resultados validados de actividades, interfaces
  y coordinación con el servicio de recompensas.

## 5. Preguntas al profesor derivadas de PR07

1. ¿La exigencia de extender `AbstractUser` y configurar un CustomUser en PR07
   sustituye la indicación anterior de utilizar el User estándar sin `AbstractUser`?
2. ¿Cada repositorio temporal debe implementar registro, login y logout, o la
   autenticación global sigue siendo responsabilidad del Equipo 0?
3. ¿Qué entidades concretas deben cubrir el CRUD evaluable? PR07 pide CRUD completo
   de al menos dos entidades principales; falta concretarlo para este repositorio.
4. ¿Los 15 días y sus entregables Git son obligatorios literalmente o forman
   parte de una guía/rúbrica de ejecución?

Hasta aclarar los dos primeros puntos se mantienen D-09 y D-10, según D-17:
User estándar, sin CustomUser, autenticación local ni cambios de `AUTH_USER_MODEL`
o migraciones por este conflicto. Los permisos se planifican sin dar por resuelta
la arquitectura de autenticación.

## 6. Trabajo interno de adaptación a PR07

Estas tareas no requieren que el profesor diseñe la arquitectura del Equipo 5.
Se ejecutarán en PR posteriores; las cuestiones de la sección 5 siguen separadas:

- Preparar ERD y diccionario de datos antes de nuevos modelos; documentar
  cardinalidades, restricciones y reglas `on_delete`.
- Incorporar el ERD revisado de Parte A y el detalle de su arquitectura aceptada.
- Implementar posteriormente modelos y migraciones a partir del diseño revisado,
  y registrar los modelos principales en Admin.
- Preparar URLs, vistas, templates, navegación, listados, detalles, formularios
  y CRUD; las entidades evaluables se concretarán con la respuesta del profesor.
- Implementar permisos y seguridad compatibles con la aclaración de usuarios.
- Ampliar tests de modelos, vistas, operaciones y permisos, además de concurrencia
  e idempotencia de los dominios y del servicio común.
- Mantener evidencias Git y PR y aportaciones identificables de cada integrante.

La aceptación de Parte A no resuelve los contratos internos A/B/C y Rewards.

La adaptación a `apps/` ya está completada y validada según D-18, con rutas Python
canónicas `apps.*`, labels Django conservados y sin cambios de modelos o migraciones.
El Día 2 (ERD y diccionario) sigue pendiente; la aclaración de usuarios y
autenticación continúa bajo D-17.
