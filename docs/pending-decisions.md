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

## 2. Dominio pendiente

- Ubicación y modelo del XP acumulado, y su relación con los perfiles.
- Historial de XP y registro de sus cambios.
- Modelo de épocas, representación de la época actual e historial de evolución.
- Catálogo de piezas y modelo y reglas de desbloqueo.
- Especializaciones y XP de dominio.
- Campos concretos de `UserProfileEcomotor` y `UserProfileBank`, y los demás
  modelos de dominio y sus relaciones y restricciones, incluidos los de economía
  y wallet. No se han decidido campos de negocio ni reglas definitivas.
- Recibir la documentación restante de clase y aclarar las diferencias entre
  los planes anteriores de DAR3 y sus secciones 9 y 10 antes de cerrar el dominio.

## 3. Datos oficiales pendientes

- Umbrales reales de XP por época.
- XP real concedida por actividades.
- Cantidades reales de DuckyCoins.
- Catálogo y reglas oficiales de desbloqueo de piezas.
- Parámetros oficiales de especializaciones y XP de dominio.

Los valores provisionales no equivalen a requisitos oficiales. No se fijan
cantidades ni umbrales concretos en estos documentos.

## 4. Integración pendiente

- Contrato técnico del servicio común de recompensas: formatos, validación de
  origen y coordinación entre el Equipo 5 y el Equipo 0.
- Clave definitiva de idempotencia para evitar recompensas duplicadas.
- Integración con el Equipo 0: usuarios y autenticación global, incorporación al
  repositorio común y acuerdos de entorno.
- Integración con los equipos 1–4: resultados validados de actividades, interfaces
  y coordinación con el servicio de recompensas.
