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
| #77 / A4.3 | Corte conceptual integrado; arquitectura interna aprobada. |
| A4.3.1 · #78 | Preparador puro integrado. El corte previo para revisión partía de bf456d6f01133f615b11367ce323f7c88b94693b; se conserva como antecedente, no integración pendiente. |

La PR #77 no implementaba código. A4.3.1 concreta la API interna mínima en 01B
sin modificar las APIs integradas ni añadir persistencia, fuentes oficiales,
endpoints o activación del Ecomotor objetivo.

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
| Preparación pura | Combinar definición/incrementos/presupuesto, verificar estructura y aritmética. A4.3.1 integrada por #78; sin BD ni efectos. |
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
de A4.2.1 mediante expected_catalog, concretado internamente en 01B para A4.3.1.
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

## 7. A4.3.1 · API pura concretada en 01B

```python
prepare_target_stats_configuration(
    *, definition: TargetStatsDefinitionSnapshot, increments, budget: int,
    expected_catalog: TargetStatsCatalogContext | None = None,
) -> PreparedTargetStatsConfiguration
```

Todos los argumentos son keyword-only; presupuesto obligatorio. No se aceptan
definiciones crudas, mappings, objetos similares o subclases como sustitutos del
tipo exacto TargetStatsDefinitionSnapshot. Incrementos conservan la representación
A4.1 de listas/tuplas de pares, con detección de duplicados antes de colapsarlos.

PreparedTargetStatsConfiguration es una dataclass frozen/slots con únicamente
definition: TargetStatsDefinitionSnapshot y calculation: TargetStatsResult.
La composición conserva opción, catálogo, versiones independientes y bases en
definition, y bases/incrementos/efectivas/presupuesto/utilizados/restantes en
calculation. No duplica campos ni contiene expected_catalog, jugador, permiso,
selección, publicación o estado confirmado.

La función revalida la definición mediante validate_target_stats_definition,
pasándole sus valores originales y el contexto opcional. Después delega reparto
y cálculo en validate_target_stats. No replica sus reglas ni usa helpers privados.
Sin contexto no hay comparación; con contexto A4.2.1 valida su tipo exacto e
igualdad de catalog_id/catalog_version. definition_version puede ser diferente.
La coincidencia contextual no acredita autorización, vigencia ni procedencia.

La construcción directa también exige los tipos exactos de ambos componentes:
reconstruye la definición mediante la API pública A4.2.1 y el cálculo mediante el
constructor validado TargetStatsResult, incluyendo sus seis campos. Comprueba
definition.bases == calculation.bases después de revalidar. Almacena copias
independientes y validadas, con tuplas canónicas; no confía únicamente en frozen,
pues una entrada puede haber sido manipulada fuera de sus constructores.

Se propagan sin envolver las excepciones A4.1 InvalidTargetStatsStructureError,
InvalidTargetStatsNumericError y TargetStatsBudgetExceededError; y las A4.2.1
InvalidTargetStatsDefinitionIdentityError, InvalidTargetStatsDefinitionStructureError,
InvalidTargetStatsDefinitionNumericError y TargetStatsDefinitionCatalogMismatchError.
El único error nuevo es InvalidTargetStatsPreparationError(ValueError): tipos de
componentes incompatibles o bases contradictorias entre definición y cálculo.
Nunca se devuelve una propuesta parcial ni se mutan entradas ante un rechazo.

## 8. Pruebas y límites de implementación

31 tests sintéticos cubren preparación, gasto total/parcial/cero, identidades y
versiones, errores delegados, contextos incompatibles, entradas manipuladas incluso
tras construcción frozen, construcción directa, copias defensivas, inmutabilidad,
determinismo, independencia, enteros grandes, delegación pública e importación y
ejecución aisladas sin Django. Las ejecuciones reales y regresiones se registran
en la PR de implementación, sin atribuirlas al corte documental #77.

Pruebas de permisos/fuentes oficiales/publicación/vigencia/transacciones/idempotencia
y configuración persistente pertenecen a incrementos posteriores. No hay ORM,
I/O, reloj, servicios V1, autorización, confirmación ni activación en A4.3.1.

## 9. Resolución confiable A4.4

[Contrato A4.4](ecomotor-target-stats-resolution-v1.md) desarrolla la frontera
entre datos estructurales, obtención autorizada, preparación A4.3.1 integrada
por #78 y confirmación persistente futura. No cambia la API de §7. Contexto de
catálogo, versiones y propuesta pura no acreditan confianza. Primera configuración,
redistribución, cambio y lectura tienen necesidades distintas de vigencia/historia.
45 es parámetro provisional interno según #79, sin defaults ni autorización por
su uso. Resolutor y fuentes reales siguen pendientes; A4.4.1 solo candidato.
