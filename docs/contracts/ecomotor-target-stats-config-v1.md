# A4.2 · Configuración de estadísticas objetivo · Contrato conceptual v1

## 1. Autoridad y estado

A4.2-SPLIT-01, ID-01, TRUST-01, SNAPSHOT-01 y CONSUME-01, aprobadas internamente
por Equipo 5 en 02C el 21/10/2026, sobre develop
`13f0c5a2dff0c94b1e81939bfe50d0ed4b73a8e2`. DAR3 sigue principal; aclaraciones
funcionales confirmadas de Óscar conservan su alcance, sin convertir estas decisiones
técnicas en reglas oficiales, esquemas Django o contratos externos ratificados.
No se inventan bases, presupuestos, límites, catálogos publicados o reglas de juego.

[Decisiones](../decisions.md#a42--configuración-autorizada-de-estadísticas-objetivo--21102026),
[opciones 02C](ecomotor-playable-options-target-v1.md),
[validador A4.1](ecomotor-target-stats-validation-v1.md),
[transición A3/CAT-01](ecomotor-transition-target-v1.md#3-catálogos-e-integridad-histórica--a3-cat-01)
y [pendientes](../pending-decisions.md#26-a42--configuración-confianza-y-consumidores-pendientes).
Se utiliza trazabilidad existente, sin afirmar nueva consulta directa de PDFs.

A4.1 está implementada e integrada por PR #74 como módulo puro. A4.2 es arquitectura;
**A4.2.1 está integrada como componente puro mediante PR #76**, sobre develop
`e612ed5cba8dfcd1e661649ff9f8459b9f4fb7fa`. El corte de implementación para revisión
partía de `f5acadfd1fed8234106fa6152e1e4aef8638ea05` (PR #75 integrada); se conserva
como antecedente, no integración pendiente.
[§9](#9-a421--api-pura-concretada-en-01b) registra su API técnica aprobada en 01B,
sin nuevas decisiones funcionales DAR3 o autorización externa. No existen por ello catálogos objetivo
publicados, fuentes de configuración autorizadas, snapshots persistentes o servicios
de resolución. No modelos, migraciones, endpoints o activación objetivo.

## 2. Bases por opción y presupuesto del jugador · A4.2-SPLIT-01

| Concepto | Contenido y límite |
| --- | --- |
| Definición de estadísticas por opción | Identidad de opción jugable, referencia y versión del catálogo objetivo aplicable, versión de definición y exactamente seis bases ATK/DEF/VEL/INT/LOG/CUACK. |
| Presupuesto autorizado del jugador | Cantidad inicial fija autorizada, sin valor numérico oficial. Se utiliza independientemente al configurar cada opción; no se agota por configurar otro Ducky ni pertenece necesariamente a cada definición de bases. |

La configuración individual usa ambos conceptos sin fusionarlos. A4.1 recibe
budget explícito para calcular un reparto; esa entrada no implica que el presupuesto
pertenezca al catálogo de bases de cada opción. Se permiten puntos sin gastar,
reparto cero y configuraciones independientes. No presupuestos por época, fórmulas
de bonificación o nuevos puntos por subir de nivel aprobados aquí.

Atributos ATR-OBJ-01: ATK Ataque, DEF Defensa, VEL Velocidad, INT Inteligencia,
LOG Lógica y CUACK Especial / Especialización. CUACK es numérico, no identidad
tecnológica; sin SPE adicional objetivo. Bases según A4.1-NUM-01: enteros Python
exactos no negativos, sin cantidades funcionales oficiales deducidas del tipo.

## 3. Identidad y versiones · A4.2-ID-01

Una definición necesita distinguir conceptualmente **opción objetivo**, **catálogo
objetivo**, **versión del catálogo** y **versión de definición de estadísticas**.
No asumir igualdad entre ambas versiones. No se define una clave física compuesta,
tabla, FK, índice, restricción SQL o formato definitivo por enumerar estas dimensiones.

Mantener siete épocas históricas objetivo: Prehistórico, Griego, Romano, Medieval,
Renacentista, Revolución Industrial y Siglo XX; y cinco tecnológicas Developer,
Ciber, Sistemas, Data IA y Gamer, conforme a 02C. Códigos canónicos definitivos
pendientes: nombres visibles no son identificadores técnicos obligatorios.

Identidad histórica objetivo distinta de EvolutionStage V1. A3-CAT-01 exige
catálogo objetivo separado, versionado e inmutable una vez utilizado; no reutilizar
referencias V1 o renombrar filas para aparentar migración. El diseño físico de
relaciones con opciones y catálogos, así como publicación/sustitución/vigencia,
sigue pendiente con A3 y propietarios.

## 4. Estructura frente a autorización · A4.2-TRUST-01

| Frontera | Responsabilidad |
| --- | --- |
| Validación estructural | Datos completos, tipos correctos e identidades/versiones estructuralmente válidas; números conforme a A4.1. No certifica procedencia, publicación, vigencia o permiso. |
| Autorización funcional | Componente servidor posterior obtiene definición realmente permitida/aplicable desde fuente confiable, coordinado con catálogos, Core y servicios E5. Todavía no implementado ni fuente ratificada. |

Texto de identidad/versión aportado por cliente o booleano declarativo no acredita
autorización. Tampoco lo hacen TargetStatsResult o TargetCatalogSnapshot A1.1.
No permitir que consumidor elija arbitrariamente bases, incrementos o versiones
para sustituir al propietario Ecomotor. El validador puro A4.2.1 valida
estructura, no membresías, permisos, publicación, vigencia funcional o fuente.

## 5. Conservación de configuración confirmada · A4.2-SNAPSHOT-01

Al implementar primera configuración real: obtener bases de definición autorizada,
conservar las seis bases usadas y conceptualmente la referencia/procedencia de la
definición aplicable; conservar incrementos y presupuesto autorizado según 02C.
Evitar reinterpretar configuraciones ya confirmadas cuando cambie una definición.
Una actualización de catálogo no recalcula silenciosamente estadísticas anteriores.

UserPlayableState, UserPlayableStats y eventos de configuración siguen siendo
arquitectura futura, no tablas existentes. Representación física, reglas de
actualización/conservación, formato histórico y eliminación pendientes de diseño
y Core; no crear campos, eventos o modelos por este contrato. No reasignar
CharacterStats o historiales V1 a opciones ni transformar log_stat/spe.

## 6. Consumo propietario y responsabilidades · A4.2-CONSUME-01

Futuros juegos/consumidores obtendrán estadísticas desde el servicio propietario
Ecomotor. Consulta conceptual coherente y solo lectura que permita distinguir:

- Opción jugable efectiva.
- Seis estadísticas efectivas.
- Configuración y versión aplicables.
- Información de revisión/coherencia necesaria para consumidor autorizado.

Sin selección implícita, puntos o cambios de progreso. No fijar endpoint HTTP,
JSON, firma Python, token o interfaz gráfica. Autorización del consumidor y
contexto de usuario requieren Core. Un juego no sustituye autoridad de Ecomotor
con datos arbitrarios de bases/reparto/versiones.

| Propietario | Responsabilidad / frontera |
| --- | --- |
| E5 / Parte A | Catálogo conceptual jugable, definiciones/validación de stats, reglas de configuración/cálculo, futuros servicios de selección/redistribución/consulta. |
| Henry / Duckies | Avatar físico, apariencia/vestimenta, inventario/equipamiento. [Ducky actual](../../apps/duckies/models.py) tiene OneToOne a User; múltiples opciones Ecomotor no implican múltiples registros físicos Ducky. No se modifica su esquema. |
| Core / Equipo 0 | Identidad/autenticación, contexto autorizado, relaciones con User, ciclo de vida y políticas compartidas. |
| Otros equipos | Consumo autorizado de estadísticas mediante contratos de integración aún pendientes. |

## 7. A4.1 integrada y futuro A4.2.1

**Corte histórico DOC-A4.2:** la previsión de implementación siguiente se conserva;
A4.2.1 ya está integrada por #76 según §9, sin persistencia o resolución
confiable de configuración. A4.1 mantiene su firma y comportamiento.

API existente en [target_stats_validation.py](../../apps/ecomotor/target_stats_validation.py):

`validate_target_stats(bases, increments, *, budget) -> TargetStatsResult`

Conservar firma y comportamiento: enteros Python exactos no negativos, rechazo de
bool/float/Decimal y conversiones; seis atributos, duplicados rechazados en
secuencias de pares; efectivas=bases+incrementos, presupuesto/restantes y resultado
inmutable/canónico. Su estructura no incluye certificado de autorización.
A4.2 aportará conceptualmente bases candidatas para validación, no cifras oficiales.
45 puntos sigue siendo ejemplo no oficial.

**A4.2.1 previsto en 01B:** validador puro de definiciones por opción. Comprobar
identidad conceptual estructural, versiones explícitas, seis bases completas,
tipos A4.1-NUM-01, duplicados/entradas incompatibles; resultado inmutable y
determinista. Separar contenido de bases y presupuesto del jugador.
Firma, errores y representación concreta se definirán antes de implementar en
01B respetando esta arquitectura, sin alterar contratos compartidos.

Sin BD, permisos/membresías, publicación/vigencia/procedencia autorizada, selección,
consultas persistentes, nuevos modelos/migraciones o efectos. No implementarlo en
esta PR. S3 V1 continúa único escritor XP, sin activar A2 o sistema objetivo.

## 8. Pendientes y pruebas futuras

Abiertos: bases oficiales, presupuesto oficial, límites funcionales adicionales,
códigos de opciones, fuente real autorizada, publicación/versionado/sustitución/
vigencia, relación física con catálogos A3-CAT-01, actualización/conservación de
configuraciones, autorización y contratos Core/Henry/consumidores, persistencia de
estado/configuraciones/eventos, activación y compatibilidad legacy. Validación
estructural no cierra ninguno por inferencia.

Pruebas previstas en DOC-A4.2, ahora incluidas en el incremento puro A4.2.1:
identidad válida/inválida, versiones explícitas/ausentes,
seis atributos canónicos completos, duplicados, bases negativas/tipos incompatibles,
conversiones rechazadas, independencia de opciones, inmutabilidad/determinismo,
entradas intactas, separación bases/presupuesto, identidades de catálogo incompatibles
cuando exista contexto explícito de comparación, no usar datos V1 ni consultas
Django/efectos secundarios. [Tests sintéticos A4.2.1](../../apps/ecomotor/test_target_stats_config_validation.py)
añadidos; los resultados reales de ejecución y regresión se informan en la PR de
implementación, sin atribuir esas ejecuciones al corte documental DOC-A4.2.
Pruebas de autorización, integración, conservación, actualización de catálogo y
consumidores siguen perteneciendo a incrementos posteriores.

## 9. A4.2.1 · API pura concretada en 01B

Concreciones técnicas de API aprobadas en 01B, no nuevos requisitos de DAR3 ni
autorización de Core. Implementación en
[target_stats_config_validation.py](../../apps/ecomotor/target_stats_config_validation.py),
con datos exclusivamente sintéticos en los tests. Sin catálogos oficiales o valores
funcionales nuevos. No modifica A4.1, A1/A2/A3, modelos o servicios V1.

```python
validate_target_stats_definition(
    *, option_code: str, catalog_id: str, catalog_version: str,
    definition_version: str, bases,
    expected_catalog: TargetStatsCatalogContext | None = None,
) -> TargetStatsDefinitionSnapshot
```

Todos los argumentos son keyword-only. Sin presupuesto, jugador, selección,
publicación o flags de autorización.

| Tipo público frozen=True, slots=True | Campos exactos y garantías |
| --- | --- |
| TargetStatsCatalogContext | catalog_id, catalog_version. Construcción directa valida ambos textos; contexto proporcionado por llamador, no certificado de catálogo. |
| TargetStatsDefinitionSnapshot | option_code, catalog_id, catalog_version, definition_version, bases. Construcción directa valida identidades/versiones y bases, copia defensivamente y conserva tuplas de pares inmutables/canónicos. |

Las cuatro identidades/versiones son str exacto, no vacío o solo espacios;
rechazar None, números/bool, subclases y otros objetos. Usar strip solo para
comprobar contenido, nunca para alterar el valor conservado: espacios exteriores,
capitalización y texto opaco no se normalizan. Sin códigos oficiales ni restricciones
de formato/longitud inventadas. Versión de catálogo y de definición independientes.

bases acepta exclusivamente listas/tuplas explícitas de pares, cada par lista/tupla
de dos elementos. Exactamente ATK/DEF/VEL/INT/LOG/CUACK, con código str exacto,
una vez cada uno; salida en ese orden canónico. Rechazar faltantes, extras, SPE,
capitalización/espacios alternativos, pares mal formados, mappings/sets/generadores/
iteradores u otros contenedores. Duplicados detectados antes de colapsar claves;
no recupera duplicados descartados por componentes anteriores.

Cada base es int Python exacto >=0: admite cero/enteros grandes, sin máximo
funcional o Django inventado. Rechaza bool, negativos, float, Decimal, Fraction,
cadenas, None, subclases int y objetos convertibles; sin convertir/truncar/redondear
ni defaults. Entradas nunca mutadas, tampoco ante error. Snapshot sin referencias
a listas originales, incluso al construirlo directamente.

expected_catalog=None omite comparación contextual. En otro caso requiere tipo
exacto TargetStatsCatalogContext válido (también revalida sus campos al recibirlo).
Compara catalog_id y catalog_version exactos; incompatibilidad produce error
específico. No compara definition_version con catalog_version ni infiere pertenencia
de opción o confianza. No acepta TargetCatalogSnapshot A1.1 como ese contexto;
validar/comparar datos del llamador no prueba publicación, vigencia o autorización.

Jerarquía pública mínima derivada de ValueError:

- InvalidTargetStatsDefinitionError: base.
- InvalidTargetStatsDefinitionIdentityError: opción/catálogo/versiones inválidos.
- InvalidTargetStatsDefinitionStructureError: pares/códigos/cobertura/duplicados o
  representación contextual incompatible.
- InvalidTargetStatsDefinitionNumericError: bases numéricamente inválidas.
- TargetStatsDefinitionCatalogMismatchError: catálogo o versión distintos del contexto.

Mensajes sin valores opacos innecesarios; no errores HTTP, ORM o autorización.
Resultado determinista y canónico, sin estado global compartido ni presupuesto,
incrementos, efectivas, saldo o datos de jugador/operador. Sus bases son directamente
compatibles con validate_target_stats(snapshot.bases, increments, budget=...):
A4.1 calcula reparto/efectivas con presupuesto separado explícito, sin autorizar
cifras. No llamadas a helpers privados A4.1, BD, ORM, red, reloj, archivos, S3,
Core, Duckies o Rewards. Importación/ejecución posible sin configuración Django.

Pendientes funcionales y externos de §8 intactos: códigos/bases/presupuesto oficiales,
fuente confiable, publicación/versionado/vigencia reales, Core/Henry/consumidores,
persistencia/conservación/migración y activación coordinada. S3 V1 sigue único
escritor XP; no se activa el objetivo ni se crea un servicio persistente.

## 10. Relación con A4.3 · Propuesta pura de configuración

[A4.3](ecomotor-target-stats-preparation-v1.md) define la futura preparación de
una propuesta completa: definición A4.2.1 válida e inmutable, incrementos y
presupuesto separado, reutilizando A4.1 para reparto/efectivas. Conserva identidad,
versiones y bases usadas sin demostrar fuente confiable, elegibilidad o autorización.
A4.3.1 no implementada; resolución autorizada y confirmación persistente son capas
posteriores. API/reglas de A4.1 y A4.2.1 integradas no cambian por esta referencia.
