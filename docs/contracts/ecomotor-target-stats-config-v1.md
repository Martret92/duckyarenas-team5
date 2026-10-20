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

A4.1 está implementada e integrada por PR #74 como módulo puro. A4.2 es arquitectura
y **A4.2.1 no está implementado**. No existen por este contrato catálogos objetivo
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
para sustituir al propietario Ecomotor. El futuro validador puro A4.2.1 valida
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

Tests futuros A4.2.1: identidad válida/inválida, versiones explícitas/ausentes,
seis atributos canónicos completos, duplicados, bases negativas/tipos incompatibles,
conversiones rechazadas, independencia de opciones, inmutabilidad/determinismo,
entradas intactas, separación bases/presupuesto, identidades de catálogo incompatibles
cuando exista contexto explícito de comparación, no usar datos V1 ni consultas
Django/efectos secundarios. No se implementan ni ejecutan tests Django aquí.
Pruebas de autorización, integración, conservación, actualización de catálogo y
consumidores pertenecen a incrementos posteriores.
