# Decisiones pendientes

Este documento reúne solo cuestiones abiertas. La estructura base de usuarios
y perfiles está resuelta en D-09 a D-12 del
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

## 2. Arquitectura de dominio por diseñar por el Equipo 5

Las reglas funcionales conocidas están en [architecture.md](architecture.md).
Ya están aclarados el progreso histórico 1–9, la XP acumulativa que no se gasta
y su separación de la barra visual; el set inicial de Prehistoria, la concesión
conjunta de seis piezas, el equipamiento automático, la conservación y
reutilización de sets sin cambiar progreso; las evoluciones múltiples; la
separación y conservación del progreso por especialización y la posibilidad de
cambiarla; y la separación de sets históricos y consumibles con cantidades.
No se mantienen estas reglas como preguntas abiertas.

Corresponde al Equipo 5 diseñar y revisar las siguientes decisiones técnicas,
sin esperar modelos concretos del profesor ni tratarlas como bloqueos externos:

- Modelo Django del XP acumulado e historial, su ubicación y relación con perfiles.
- Modelos de épocas, época actual e historial de evolución, incluidos los eventos
  de evoluciones múltiples.
- Modelos de catálogo, sets, piezas, inventario, equipamiento y cantidades de consumibles.
- Modelos de wallet, transacciones, catálogo comercial, tienda y compras.
- Representación separada de especialización activa y progreso/rango conservado
  de cada especialización; operación para volver al punto de Era Digital y cambiarla.
- Campos concretos de `UserProfileEcomotor` y `UserProfileBank`, y los demás
  modelos, relaciones y restricciones que no estén cubiertos por los puntos anteriores.
- Contratos internos A/B/C, consistencia entre operaciones y mecanismo técnico
  de idempotencia, para revisión conjunta durante la arquitectura.

### Reglas funcionales todavía abiertas

- Reglas de XP de dominio y requisitos/umbrales para progresar desde la especialización elegida a Junior, Middle, Senior y Master.
- Uso concreto de consumibles y sus efectos en cada modo de juego.
- Encaje de la tienda estética descrita en DAR3 con el catálogo de combate de las
  aclaraciones de clase, manteniendo los sets históricos no comprables.
- Revisar la documentación restante de clase y las diferencias entre planes
  anteriores de DAR3 y sus secciones 9 y 10 que no resuelvan estas aclaraciones.

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
