# A4.4 · Resolución confiable de estadísticas objetivo · Contrato conceptual v1

## 1. Autoridad, antecedentes y estado

A4.4-SOURCE-01, A4.4-INPUT-01, A4.4-RESOLVE-01, A4.4-LIFECYCLE-01 y
A4.4-FAIL-01: arquitectura interna aprobada por Equipo 5 en 02C el 21/10/2026,
sobre develop `529e6a03a8c97d745ffbeadc9da3c67b83edafd3`. DAR3 conserva autoridad
funcional; estas decisiones no son nuevas reglas de Óscar ni ratificación de Core,
Henry o consumidores. Se utiliza trazabilidad existente y el acuerdo comunicado
por Jaime, sin afirmar nueva consulta directa de fuentes externas.

[Decisiones](../decisions.md#a44--resolución-confiable-de-estadísticas-objetivo--21102026)
y [pendientes](../pending-decisions.md#29-a44--resolución-confiable-y-dependencias).

| Componente | Estado y garantía |
| --- | --- |
| [A4.1](ecomotor-target-stats-validation-v1.md) · #74 | Validador puro de reparto integrado; comprueba números, no autoridad. |
| [A4.2.1](ecomotor-target-stats-config-v1.md#9-a421--api-pura-concretada-en-01b) · #76 | Definición estructural validada; comparación opcional de catálogo, sin certificar confianza. |
| [A4.3.1](ecomotor-target-stats-preparation-v1.md#7-a431--api-pura-concretada-en-01b) · #78 | Preparador puro integrado; propuesta completa, no confirmación autorizada. |
| #79 · A4-PRESUPUESTO-PROV-01 | 45 puntos provisionales por opción, por decisión interna; no presupuesto definitivo ni autorización de una configuración real. |
| A4.4 / A4.4.1 | Arquitectura documentada; resolutor no implementado. A4.4.1 es candidato sujeto a revisión previa en 01B. |

Se mantienen las APIs validate_target_stats(bases, increments, *, budget),
validate_target_stats_definition(...) y prepare_target_stats_configuration(*,
definition, increments, budget, expected_catalog=None), sin cambios.

## 2. Cuatro fronteras

| Frontera | Responsabilidad |
| --- | --- |
| Estructura válida | Las APIs puras verifican tipos, cobertura y aritmética. No prueban publicación, procedencia, vigencia o permiso. |
| Resolución autorizada futura | Servidor obtiene o verifica definición y presupuesto desde fuentes autorizadas, identidad y contexto aplicables. |
| Preparación integrada A4.3.1 | Combina definición, incrementos y presupuesto explícito; produce una propuesta inmutable y determinista. |
| Confirmación persistente futura | Servicios propietarios confirman selección/configuración/redistribución con sus garantías de autorización, estado, revisiones, idempotencia e historia. |

Ninguna etapa pura equivale a autorización ni a configuración persistida.
Documentar la resolución tampoco implementa la confirmación.

## 3. Fuente confiable · A4.4-SOURCE-01

Separar el servicio de resolución de sus fuentes concretas. Alternativas futuras:

- Configuración versionada controlada por el servidor.
- Catálogo persistente en Django.
- Servicio propietario externo, solo si se acuerda su necesidad.

No se elige implementación física. La autoridad de publicación debe estar acordada:
estar almacenado en el servidor no demuestra aprobación oficial. Los fixtures
sintéticos de pruebas no son configuración publicada de producción.

## 4. Entradas y autoridad · A4.4-INPUT-01

La petición conceptual podrá incluir opción solicitada y seis incrementos.
Identidad del jugador, permisos, contexto confiable, definición, bases, presupuesto
y versiones aplicables deben obtenerse o verificarse en servidor y fuentes autorizadas.
El cliente no impone bases, presupuesto, versión publicada arbitraria, pertenencia
a catálogo ni autorización mediante booleanos. No se fijan firmas Python, endpoints,
credenciales, certificados, tokens o mecanismos definitivos de autenticación.

## 5. Resolución · A4.4-RESOLVE-01

Verificar conceptualmente identidad de opción, pertenencia a catálogo objetivo
autorizado, identidad/versión de catálogo, versión aplicable de definición, estado
y aplicabilidad de esta, presupuesto autorizado y elegibilidad/contexto cuando
correspondan. Después reutilizar A4.2.1 y A4.3.1 para validar y preparar.
No duplicar las garantías numéricas de A4.1 ni modificar estas APIs.

TargetStatsCatalogContext compara estructura aportada por el llamador; no certifica
confianza. Resolver correctamente tampoco confirma una configuración persistente.
La fuente real, publicación y obtención confiable siguen pendientes.

## 6. Versiones e historia por operación · A4.4-LIFECYCLE-01

| Operación futura | Datos y conservación |
| --- | --- |
| Primera configuración | Bases autorizadas aplicables a una configuración nueva. |
| Redistribución | Bases del snapshot confirmado; no sustituirlas silenciosamente por las actuales del catálogo. |
| Cambio de opción | Configuración propia previamente confirmada. |
| Lectura de estadísticas | Estado efectivo y configuración persistida, con coherencia de lectura. |

No imponer idéntica política de vigencia a todas las operaciones. Definiciones
retiradas, sustituidas, incompatibles o antiguas requieren reglas todavía pendientes.
Se conserva A4.2-SNAPSHOT-01; cambios de catálogo no recalculan silenciosamente
configuraciones confirmadas. [A3-CAT-01](ecomotor-transition-target-v1.md#3-catálogos-e-integridad-histórica--a3-cat-01)
separa catálogo objetivo e identidad histórica de V1. No se definen relaciones
Django, FKs, eventos, migraciones o políticas físicas de conservación.

## 7. Rechazo seguro · A4.4-FAIL-01

El servicio futuro rechaza sin efectos cuando no haya fuente autorizada disponible,
falten bases/presupuesto, existan versiones incompatibles o no pueda demostrarse
la elegibilidad exigida. Sin bases por defecto, presupuestos inventados, versiones
alternativas seleccionadas silenciosamente, flags de autoridad cliente,
configuraciones parciales confirmadas o reparaciones automáticas del historial.

La política transaccional definitiva se diseñará con servicios persistentes y
A3/Core. No se aprueban aquí nuevos protocolos de concurrencia, replay o persistencia.

## 8. Presupuesto provisional y límites

[A4-PRESUPUESTO-PROV-01](../decisions.md#doc-aclaraciones-2010--presupuesto-vestimentas-y-membresías--21102026)
adopta 45 puntos por opción, independientes, con reparto completo/parcial/cero.
Es parámetro de desarrollo aprobado internamente, revisable; el presupuesto
definitivo sigue pendiente. No prueba publicación de definición, procedencia o
autorización real. No introducir budget=45 implícito en validadores/preparador.
Una futura modificación con configuraciones persistidas exige política expresa
de versionado/tratamiento; no recálculo silencioso de confirmadas.

ATK/DEF/VEL/INT/LOG/CUACK y sus garantías puras se conservan. V1 no se reinterpreta:
log_stat sigue Logística y spe Especial / Especialización; S3 V1 único escritor
XP activo. No activar A2, Ecomotor objetivo, integraciones económicas o gráficas.

## 9. A4.4.1 candidato y dependencias

**Frontera de resolución cerrada por defecto**, candidata, no implementación
automáticamente aprobada. Posible mínimo: separar contrato de resolución de
validadores; rechazar sin fuentes autorizadas configuradas; pruebas con proveedores
sintéticos identificados que no se confundan con fuentes oficiales; ausencia de
efectos persistentes. En 01B deberá comprobarse antes de implementar que aporta
una garantía útil sin simular autorización. Sin clases, adaptadores físicos,
certificados o API definitiva elegidos por este documento.

| Propietario | Pendiente |
| --- | --- |
| Óscar | Bases oficiales por opción, presupuesto definitivo y posibles reglas funcionales adicionales. |
| A3 / Parte A | Catálogo objetivo versionado, compatibilidad histórica, procedencia, migración y transición controlada; fuente y autoridad de publicación acordadas. |
| Core / Equipo 0 | Identidad, autorización, permisos, ciclo de vida y conservación, incluidas dependencias A3.5. |
| Henry | Relación opción jugable / Ducky físico. |
| Consumidores | Contrato de lectura de estadísticas desde Ecomotor. |

Ninguna dependencia queda cerrada por esta arquitectura. Resolutor real y servicios
persistentes continúan sin implementación; no se crean fuentes oficiales ni permisos.

## 10. Pruebas futuras

Fuente autorizada no configurada; opción desconocida; catálogo/versión incompatibles;
definición ausente/ambigua/sustituida/retirada; presupuesto ausente/inválido; intento
de sustituir bases/presupuesto desde cliente; fallo de proveedor; reutilización
coherente A4.3.1; ausencia de escrituras/efectos; independencia de configuraciones;
no reinterpretación de snapshots históricos; regresión V1.

Permisos reales, concurrencia, transacciones, idempotencia y persistencia se probarán
en servicios integrados posteriores. No se crean ni ejecutan tests Django en esta
PR exclusivamente documental.
