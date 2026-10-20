# A4.3 · Preparación pura de configuraciones objetivo · Contrato conceptual v1

## 1. Autoridad, antecedentes y estado

A4.3-PREP-01, BOUNDARY-01, VERSION-01 y FAIL-01, aprobadas internamente por
Equipo 5 en 02C el 21/10/2026, sobre develop
`e612ed5cba8dfcd1e661649ff9f8459b9f4fb7fa`. DAR3 conserva autoridad funcional;
no se atribuye al profesor aprobación de APIs, valores numéricos, modelos Django
o mecanismos de autorización. Se usa trazabilidad existente, sin afirmar nueva
consulta directa de PDFs o contratos externos ratificados.

[Decisiones](../decisions.md#a43--preparación-pura-de-configuraciones-objetivo--21102026),
[pendientes](../pending-decisions.md#27-a43--preparación-y-fronteras-pendientes),
[A4.2](ecomotor-target-stats-config-v1.md),
[A4.1](ecomotor-target-stats-validation-v1.md),
[opciones 02C](ecomotor-playable-options-target-v1.md) y
[A3-CAT-01](ecomotor-transition-target-v1.md#3-catálogos-e-integridad-histórica--a3-cat-01).

| Incremento | Estado real |
| --- | --- |
| #73 / #74 | Arquitectura A4.1 e implementación pura integradas. |
| #75 / #76 | Arquitectura A4.2 y validador puro A4.2.1 integrados. |
| A4.3 / A4.3.1 | Arquitectura interna aprobada; preparador puro todavía no implementado. |

No modificar las APIs integradas ni crear aquí código, persistencia, fuentes
oficiales, endpoints, interfaces o activación del Ecomotor objetivo.

## 2. Preparación conceptual · A4.3-PREP-01

Entradas: definición válida e inmutable de estadísticas, validada mediante
A4.2.1; seis incrementos propuestos; presupuesto explícito separado.
Reutilizar A4.1 para validar reparto y calcular efectivas, sin duplicar
injustificadamente sus reglas numéricas/estructurales.

| API integrada | Papel conservado |
| --- | --- |
| validate_target_stats_definition(...) → TargetStatsDefinitionSnapshot | Identidad/versiones y seis bases; TargetStatsCatalogContext permite comparación estructural opcional, no autorización. |
| validate_target_stats(bases, increments, *, budget) → TargetStatsResult | Valida reparto/presupuesto y calcula bases+incrementos, utilizados/restantes. |

Resultado conceptual completo: identidad de opción, identidad y versión de catálogo
objetivo, versión de definición, seis bases canónicas usadas, seis incrementos
validados, presupuesto, puntos utilizados/restantes y seis estadísticas efectivas.
Inmutable, determinista y sin referencias mutables a entradas externas.
No identidad de jugador, selección activa o autorización demostradas por el cálculo.

Presupuesto independiente por configuración, no parte obligatoria de definición
de bases ni saldo consumido por configurar otro Ducky. Puntos pendientes permitidos.
**Preparación válida no es configuración autorizada ni confirmada.**

## 3. Tres responsabilidades · A4.3-BOUNDARY-01

| Capa | Responsabilidad y estado |
| --- | --- |
| Preparación pura | Combinar definición/incrementos/presupuesto, verificar estructura y aritmética. A4.3.1 futura; sin BD ni efectos. |
| Resolución autorizada futura | Servidor obtiene definición aplicable y presupuesto permitido desde fuentes confiables, comprobando contexto, elegibilidad y vigencia. No implementada/ratificada por esta documentación. |
| Confirmación persistente futura | Servicios propietarios confirman selección o redistribución con referencias, estado, revisiones, idempotencia e historial correspondientes. Fuera del preparador y condicionada a 02C/Core. |

No prueban autorización por sí solos: versión textual coincidente, contexto de
catálogo del cliente, definición estructuralmente válida, presupuesto del navegador,
booleano authorized=True o propuesta pura creada correctamente. Comparar datos
aportados no autentica su fuente. No definir certificado de confianza, token,
firma, contexto físico de autorización o mecanismo definitivo de obtención.

## 4. Identidad, versiones y conservación · A4.3-VERSION-01

La propuesta preserva identidad de opción/catálogo objetivo, versión de catálogo,
versión de definición y las seis bases utilizadas. Versiones no intercambiables
ni prueba de autenticidad del contenido. No elegir códigos oficiales o inferir
identidad desde nombres visibles.

Configuración realmente confirmada deberá conservar bases/procedencia usadas
según A4.2-SNAPSHOT-01; catálogo posterior no recalcula silenciosamente una
configuración anterior. A3-CAT-01 mantiene catálogo objetivo separado de V1.
No se añaden campos, tablas, relaciones o políticas de conservación aquí.
Formato histórico y contratos de persistencia/Core siguen pendientes.

## 5. Rechazo sin efectos · A4.3-FAIL-01

Preparación rechaza definición inválida, incrementos incompletos/duplicados,
tipos incompatibles, presupuesto inválido/excedido e incompatibilidad contextual
cuando se solicite comprobación estructural. Esa comparación conserva el alcance
de A4.2.1; no aprueba un parámetro nuevo para una API de preparación aún sin fijar.
Fallo no produce efectos ni muta entradas, no completa bases/presupuesto/puntos
automáticamente. No conversiones, defaults o reparaciones silenciosas.

Confirmación futura comprobará vigencia, elegibilidad, referencias y estado conforme
a su frontera transaccional. No inventar concurrencia, replay o actualización para
A4.3.1 ni trasladarle automáticamente políticas de operaciones persistentes.

## 6. Compatibilidad y responsabilidades

Conservar ATK Ataque, DEF Defensa, VEL Velocidad, INT Inteligencia, LOG Lógica y
CUACK Especial / Especialización. Bases/incrementos/presupuesto enteros Python
exactos no negativos según NUM-01; bool y conversiones rechazados, efectivas =
bases+incrementos, puntos pendientes y presupuesto independiente. Sin SPE objetivo,
valores, límites o presupuestos oficiales nuevos; 45 no es presupuesto oficial.

V1 mantiene log_stat = Logística y spe = Especial / Especialización, sin
transformar estadísticas/eventos históricos. S3 V1 sigue único escritor XP activo.
No activar A2, A4 objetivo o escritores nuevos.

| Responsable | Función / dependencia |
| --- | --- |
| E5 / Parte A | Validación y preparación pura, futura resolución y servicios propietarios de stats/opciones. |
| Óscar | Bases oficiales, presupuesto numérico y reglas funcionales adicionales que correspondan; no definidos por este contrato. |
| Core / Equipo 0 | Identidad, permisos, contexto confiable, conservación y dependencias A3.5. |
| Henry | Relación opción jugable/Ducky físico, apariencia e inventario. |
| Otros equipos | Contratos pendientes de consulta de estadísticas efectivas desde Ecomotor. |

Ninguna dependencia se considera ratificada por esta separación. Permanecen
abiertos fuentes confiables/publicación/vigencia, valores autorizados, contratos
de consumo, persistencia/conservación/migración y activación coordinada.

## 7. Próximo incremento A4.3.1 y pruebas futuras

**A4.3.1 — Preparador puro de configuraciones objetivo**, para 01B: recibir
una definición válida/inmutable, incrementos/presupuesto, invocar A4.1 y devolver
propuesta completa canónica/inmutable conservando identidad/versiones. Sin Django,
BD, I/O, otros servicios o certificación de autorización.
Firma Python, errores y estructura definitiva del resultado deberán revisarse en
01B antes de implementar; no APIs compartidas definitivas de juegos/frontend.

Tests futuros: preparación válida, gasto total/parcial/cero, efectivas correctas,
identidad/versiones/bases preservadas, exceso e incrementos inválidos,
definición/contexto incompatibles, fallo sin efectos, entradas intactas, inmutabilidad,
determinismo/independencia, reutilización A4.1/A4.2.1, aislamiento Django/I/O y
regresión V1. No se implementan ni ejecutan nuevos tests Django en esta PR documental.
Pruebas de permisos/fuentes oficiales/publicación/vigencia/transacciones/idempotencia
y configuración persistente pertenecen a incrementos posteriores.
