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
| A4.4 · #80 | Arquitectura conceptual integrada; antecedentes conservados. |
| A4.4.1 | Frontera mínima implementada para revisión en PR sobre 706181d1201ffc677f10230aca321c472d222190; entrada real siempre cerrada, sin fuente autorizada integrada. No integrada hasta merge autorizado. |

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
a catálogo ni autorización mediante booleanos. El corte conceptual no fijaba firmas
Python; §9 concreta ahora únicamente la API interna mínima cerrada de A4.4.1.
No endpoints, credenciales, certificados, tokens o autenticación definitiva.

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

## 9. A4.4.1 · Frontera mínima y ensayo estructural

El corte conceptual de #80 presentaba A4.4.1 como candidata sujeta a revisión.
El traspaso posterior de 02C aprueba esta concreción interna mínima, sin reabrir
las cinco decisiones A4.4 ni aprobar fuentes o reglas externas.

```python
resolve_target_stats_configuration(
    *, option_code: str, increments,
) -> PreparedTargetStatsConfiguration
```

En este incremento **siempre lanza TargetStatsSourceUnavailableError**: no hay
fuente confiable integrada/aprobada y nunca devuelve una configuración resuelta.
La anotación de retorno no acredita una salida disponible actualmente. No inspecciona
opción ni incrementos para fingir validación de catálogo, publicación o elegibilidad;
también ante entradas mal formadas prevalece la indisponibilidad de fuente.
Los dos argumentos son obligatorios y keyword-only. No acepta proveedor/source,
definición/bases, presupuesto/versiones, flags de confianza, jugador, rol o permisos;
argumentos ajenos producen TypeError de firma, no configuran una fuente.
Sin I/O, BD, mutación, configuración global o llamadas a preparación. No fallback
a la demo, sus etiquetas, 45 puntos o bases cero. No proveedor por defecto ni
registro inyectable de proveedores. La entrada real no llama al ensayo privado.

Ensayo privado, separado y sin autoridad:

```python
_prepare_untrusted_resolution_candidate(
    *, option_code: str, definition: TargetStatsDefinitionSnapshot,
    increments, budget: int,
    expected_catalog: TargetStatsCatalogContext | None = None,
) -> PreparedTargetStatsConfiguration
```

Exige opción str exacto no vacía ni compuesta solo de espacios; no normaliza
su identidad ni impone máximos físicos. Delega definición, incrementos, presupuesto
y contexto explícitos en prepare_target_stats_configuration de A4.3.1, que revalida
con A4.2.1 y calcula mediante A4.1. Compara la opción solicitada exactamente con
la definición revalidada de la propuesta. Solo devuelve PreparedTargetStatsConfiguration,
con sus copias defensivas y garantías inmutables; no certificado o dataclass de
confianza. Versiones de catálogo/definición distintas son válidas; expected_catalog
sigue siendo comparación estructural, sin autoridad. Presupuesto obligatorio,
sin 45 predeterminado; omitirlo produce TypeError y un valor inválido conserva
el error numérico A4.1. No se replica validación de atributos ni aritmética.

Jerarquía mínima, derivada de ValueError:

- TargetStatsResolutionError: base.
- TargetStatsSourceUnavailableError: rechazo incondicional de la entrada real.
- InvalidTargetStatsResolutionRequestError: identidad solicitada inválida en el ensayo.
- TargetStatsResolutionOptionMismatchError: opción solicitada distinta de la definición validada.

Errores de A4.1/A4.2.1/A4.3.1 se propagan sin envolver ni perder significado.
Mensajes propios sin identidades opacas, datos privados o detalles de proveedores.
Sin errores HTTP, autenticación o publicación simulada. Un ensayo exitoso nunca
autoriza ni confirma una configuración real.

### Dependencias abiertas

| Propietario | Pendiente |
| --- | --- |
| Óscar | Bases oficiales por opción, presupuesto definitivo y posibles reglas funcionales adicionales. |
| A3 / Parte A | Catálogo objetivo versionado, compatibilidad histórica, procedencia, migración y transición controlada; fuente y autoridad de publicación acordadas. |
| Core / Equipo 0 | Identidad, autorización, permisos, ciclo de vida y conservación, incluidas dependencias A3.5. |
| Henry | Relación opción jugable / Ducky físico. |
| Consumidores | Contrato de lectura de estadísticas desde Ecomotor. |

Ninguna dependencia queda cerrada. La resolución autorizada efectiva y los servicios
persistentes siguen sin implementar; solo existe la frontera que rechaza. No se
crean fuentes oficiales, proveedores sintéticos de producción ni permisos.

## 10. Pruebas de A4.4.1 y pruebas pendientes

25 tests sintéticos unittest.TestCase cubren rechazo incondicional, firma cerrada,
ausencia de preparación durante rechazo, datos hostiles no inspeccionados, errores
seguros, composición privada con A4.3.1, opción y contexto discordantes, definición
ausente/manipulada, incrementos/duplicados, presupuesto obligatorio/inválido/excedido,
gasto completo/parcial/cero, errores originales, inmutabilidad, copias, entradas
intactas, determinismo/independencia y ejecución aislada sin Django/demo/servicios.
Ejecuciones de tests nuevos mediante Django y unittest, regresiones y suite completa
registradas con resultados reales en la PR de implementación; no atribuidas a #80.

Siguen pendientes pruebas de fuentes reales, fallo de proveedor aprobado,
publicación/pertenencia, ambigüedad, retirada/sustitución/vigencia y elegibilidad.
Sin fuente aprobada no pueden clasificarse esos casos en la entrada real: todos
se rechazan por indisponibilidad, sin fingir garantías. Permisos Core, concurrencia,
transacciones, idempotencia y persistencia se probarán en servicios futuros.
