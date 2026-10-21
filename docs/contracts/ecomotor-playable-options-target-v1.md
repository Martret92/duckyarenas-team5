# Ecomotor · Opciones jugables · Contrato objetivo v1 (02C)

## 1. Estado y autoridad

**Precisión funcional posterior:** [§8](#8-conciliación-funcional-posterior-con-óscar)
contrasta las aclaraciones confirmadas de Óscar con el diseño 02C conservado.
La precisión interna [ATR-OBJ-01](../decisions.md#atr-obj-01--nomenclatura-de-atributos-objetivo--20102026) resuelve la nomenclatura objetivo:
LOG = Lógica y CUACK = Especial / Especialización. [§10](#10-precisiones-posteriores--presupuesto-y-recursos)
registra 45 puntos provisionales por decisión interna posterior. Bases, presupuesto definitivo, fórmulas,
transición legacy y adaptación de apariencia siguen pendientes; no se activa el
sistema ni se cambian campos o datos V1.

**Arquitectura objetivo aprobada internamente por el Equipo 5 el 20/10/2026;
no implementada ni activada.** target-v1 es la versión del diseño, no una API
disponible, una migración aprobada o una sustitución ejecutada de contratos V1.
La implementación posterior se planificará en 01B.

Procedencia: acuerdos 02C comunicados por Jaime en este encargo. DAR3 conserva su
autoridad principal. La aclaración de Óscar del 19/10/2026 comunicada por Jaime
confirma las siete épocas históricas; no se le atribuyen modelos, servicios ni
las demás decisiones internas. Se usa la trazabilidad existente, sin afirmar
una nueva consulta directa de los PDFs.

[Decisiones](../decisions.md#02c--arquitectura-objetivo-del-ecomotor--20102026),
[arquitectura](../architecture.md#9-arquitectura-objetivo-02c--no-implementada),
[ERD conceptual](../erd/ecomotor.md#14-opciones-jugables--modelos-conceptuales-02c) y
[pendientes](../pending-decisions.md#13-pendientes-residuales-de-la-arquitectura-objetivo-02c).
Los IDs T-01…T-03 y E-01/E-02 de **02C** son de este ámbito; no ratifican baremos
homónimos de Training/Escape ni precios anteriores.

## 2. A1, A2 y A3 · Progresión, catálogos y XP objetivo

Contratos objetivo bajo ARQ-PROG-01 y A1-CT-01/A2-CT-01/A3-CT-01; no publican
firmas nuevas ni alteran hoy S1, validadores o S3.

| Nivel | Época histórica objetivo |
| --- | --- |
| 1 | Prehistórico |
| 2 | Griego |
| 3 | Romano |
| 4 | Medieval |
| 5 | Renacentista |
| 6 | Revolución Industrial |
| 7 | Siglo XX |

Los umbrales de cada época coinciden con los del nivel correspondiente. Nivel 8
desbloquea elección, **no es una octava época**; niveles posteriores continúan.
Siglo XX es la última época y puede seguir efectiva si se aplaza la elección.
Valores XP pendientes; no hay puntos adicionales de estadísticas por subir de nivel.

| Contrato objetivo | Entrada y precondiciones conceptuales | Resultado y límites |
| --- | --- | --- |
| A1 · Progresión y validación (A1-CT-01) | XP anterior/posterior no decreciente, catálogos versionados válidos y correspondencia objetivo. | Nivel/época anteriores y finales y todas las transiciones cruzadas; cálculo sin escritura ni concesión de puntos por nivel. |
| A2 · Adaptación de XP histórica (A2-CT-01) | Perfil persistido, XP positiva, identidad idempotente y configuración autorizada del sistema activo. Referencia actual: grant_historical_xp(profile, amount, operation_key). | Adaptación futura conserva XP, niveles, todas las evoluciones, atomicidad e idempotencia; deja de conceder puntos nuevos por nivel. Revisar explícitamente compatibilidad de stat_points_awarded y available_points_after heredados; no modificar S3 ahora. |
| A3 · Compatibilidad de catálogos y transición (A3-CT-01) | Niveles, siete épocas, umbrales y versión del sistema cuya activación se valida. | Comprobar orden y coincidencia de umbrales niveles 1–7; elección en nivel 8 separada de evolución. Compatibilidad V1, inventario y clasificación legacy antes de migración y activación coordinada, sin renombrar historia para simular migración. |

Errores: XP/entradas inválidas, configuración/catálogos incompatibles, perfil
incoherente, conflicto idempotente o BD; sin reparación automática. A1/A3 no
conceden efectos; A2 confirma/revierte perfil e historiales conjuntamente bajo
D-19, con retry explícito en nueva transacción. No reconstruir resultados antiguos
con nueva configuración ni tratar un cálculo como concesión confirmada.

## 3. Opciones y estadísticas

T-01/T-02/T-03 e I-01 de 02C: desde nivel 8 se elige entre siete históricos
desbloqueados y **Developer, Ciber, Sistemas, Data IA y Gamer**; códigos canónicos
pendientes. Históricos son opciones jugables reales, no vestimentas. Solo una
opción explícita activa; antes de elegir rige la época histórica alcanzada.
Primera elección confirma opción/configuración juntas. Abandonar sin confirmar
no guarda selección parcial. Alternar histórico/tecnológico conserva estadísticas,
XP histórica, nivel, etapa, otras configuraciones y progreso tecnológico/rangos
confirmados independientes. S13-A2 no persiste todavía esos rangos.

E-01/E-02 se precisan mediante [ATR-OBJ-01](../decisions.md#atr-obj-01--nomenclatura-de-atributos-objetivo--20102026), aprobada internamente
tras la confirmación de Jaime: LOG cambia de Logística a Lógica y SPE se denomina
CUACK, conservando Especial / Especialización. La nomenclatura vigente del
**diseño objetivo, no implementado**, es:

| Código objetivo | Significado |
| --- | --- |
| ATK | Ataque |
| DEF | Defensa |
| VEL | Velocidad |
| INT | Inteligencia |
| LOG | Lógica |
| CUACK | Especial / Especialización |

CUACK es un atributo numérico, no la identidad de una especialización tecnológica;
no añade un séptimo atributo ni implica efectos especiales nuevos.
Los antecedentes de E-01/E-02 y la conciliación de §8 se conservan como historia.
V1 mantiene log_stat = Logística y spe = Especial / Especialización: no convertir
valores históricos SPE a CUACK ni reinterpretar log_stat como Lógica.
Cada Ducky conserva al
configurarse un snapshot de sus seis bases y seis incrementos independientes.
Efectivas = bases conservadas + incrementos. Se permite dejar puntos pendientes.
El presupuesto inicial fijo autorizado del jugador se utiliza independientemente
en cada Ducky: no es saldo global consumido al configurar otro. A4-PRESUPUESTO-PROV-01
adopta 45 provisionalmente por opción (§10); presupuesto definitivo y bases siguen
pendientes. No hay puntos adicionales por subir de nivel.

**Training no modifica los seis atributos ni concede puntos adicionales para ellos
en esta primera versión objetivo.** Mejoras futuras requieren confirmación
funcional de Óscar y coordinación con Training; no son requisito operativo actual.

[A4.1 · Validación pura de estadísticas](ecomotor-target-stats-validation-v1.md)
precisa claves exactas, bases explícitas, reparto por configuración y cálculo
bases + incrementos. A4.1 integrada como módulo puro por PR #74; no fija
bases/presupuesto oficiales ni implementa selección/redistribución ni modifica V1.
[A4.2 · Definiciones de estadísticas](ecomotor-target-stats-config-v1.md) separa
bases por opción del presupuesto fijo autorizado del jugador, con identidades y
versiones conceptuales. La fuente confiable y autorización funcional corresponden
a un componente servidor futuro. Conservar bases/referencia/procedencia al confirmar
configuraciones futuras; catálogo nuevo no reinterpreta las ya confirmadas.
No se aprueban tablas o servicios persistentes por esta precisión.

## 4. SVC-OP-01 a 04 · Contratos objetivo

Entradas/resultados conceptuales, **sin firmas Python ni APIs implementadas**.
Requieren consumidor autorizado, perfil persistido coherente, propiedad verificada,
configuración válida para sistema activado y clasificación explícita de legacy.
Validación estructural no autentica.

### SVC-OP-01 · Primera configuración de una opción

- Entrada: jugador/perfil, opción nunca configurada, reparto de seis incrementos,
  identidad de operación y precondiciones de estado/revisión.
- Validar nivel 8, elegibilidad, propiedad, identidad y presupuesto autorizado.
- En primera elección del jugador, crear UserPlayableState solo al confirmar;
  para otra opción nunca configurada, reutilizar su estado/presupuesto, sin duplicarlo.
- Crear snapshot de bases y confirmar configuración, activa y evento de primera
  configuración atómicamente. Tecnología sin progreso crea dominio en cero;
  progreso existente nunca se reinicia.
- Resultado: selección/configuración confirmadas, evento y revisiones; ninguna
  escritura parcial o cambio ajeno. Una opción ya configurada usa SVC-OP-02.

### SVC-OP-02 · Cambio de Ducky

- Entrada: jugador, configuración destino existente y revisión esperada del estado.
- Comprobar propiedad, configuración válida y revisión esperada antes de resolver
  repetición. Si es obsoleta, rechazar incluso cuando el objetivo ya esté activo.
- Con revisión coincidente y destino ya activo, devolver el estado existente sin
  escrituras. Para un cambio efectivo, activar la configuración destino.
- Resultado: opción/configuración activas y estado relevante; no altera stats
  guardadas, XP histórica, nivel, etapa, dominio o rangos.
- No configurar destinos nunca usados ni generar evento de redistribución.
  La semántica de revisión/repetición está aprobada; solo queda concretar su
  implementación técnica. No prometer replay histórico completo tras A → B → A.

### SVC-OP-03 · Estadísticas efectivas

- Entrada: jugador/perfil y contexto de consulta autorizado.
- Resolver coherentemente Ducky efectivo y seis atributos. Antes de elegir,
  usar época alcanzada; después, activa y snapshot/reparto conservados.
- Resultado de solo lectura: identidad efectiva, seis valores y procedencia/revisión
  necesaria para consumo. Sin escrituras, puntos ni selección implícita.
- No crear estado al consultar ni clasificar ausencia legacy como perfil nuevo.
  Incoherencias/configuración ausente son errores, no bases inventadas. Mecanismo
  de lectura coherente pendiente, sin prometer snapshot entre consultas separadas.

### SVC-OP-04 · Redistribución (OP-RED-01)

- Entrada: jugador, configuración, reparto completo de seis incrementos,
  clave de operación y revisión esperada.
- Validar propiedad, presupuesto, configuración y revisión; conservar bases.
- Actualizar configuración y evento de redistribución atómicamente, con reparto
  anterior/posterior y revisiones; devolver resultado confirmado trazable.
- Gratuita, ilimitada e independiente por Ducky. Sin monedas/objetos, cambios de
  bases, XP histórica, nivel, etapa, dominio, rangos u otras configuraciones.
- Puede dejar puntos pendientes. Caso de reparto idéntico aún pendiente.

## 5. Errores, idempotencia y concurrencia

Distinguir entrada/reparto/presupuesto, autorización/propiedad, elegibilidad,
opción no configurada, configuración/catálogo, revisión obsoleta, conflicto de
identidad, estado/historia incoherentes y BD. Sin clases, firmas o códigos HTTP
definitivos. Un fallo no es confirmación parcial.

SVC-OP-01/04 protegen duplicados mediante identidad conceptual
UNIQUE(playable_state, operation_key) e historia. Una identidad no aplica dos veces
ni sobrescribe otra distribución incompatible; conservar evidencia histórica.
**Orden entre reintento compatible y revisión obsoleta pendiente**: no trasladar
S14-A-09 automáticamente a estos contratos distintos. Representación de contenido,
replay y caso sin cambios por concretar antes del código.

Escrituras bajo frontera atómica y alias común; D-19 conserva BEGIN IMMEDIATE,
timeout 5 s, comprobaciones bajo transacción antes de modificar estado mutable,
unicidad persistente, rollback y revisión para evitar pérdida de cambios.
Alcance/incremento de revisiones por especificar. Sin I/O externo en transacción,
retry automático, bloqueo efectivo select_for_update en SQLite ni atomicidad entre
BD independientes. SVC-OP-03 es lectura; no se le atribuye identidad de concesión.

## 6. Compatibilidad y activación coordinada

A3-CT-01, junto con COMP-01/ORD-OP-01/PLAN-OP-01, regula compatibilidad,
migración legacy y activación coordinada. Distinguen:

1. Nueve épocas de DAR3 original.
2. Siete etapas V1 terminadas en Actual, stats globales, puntos por nivel y
   selección/cambio tecnológicos S11-A/S14-A en Actual.
3. Siete épocas objetivo terminadas en Siglo XX, elección nivel 8 y estadísticas
   independientes sin puntos nuevos por nivel.

No renombrar EvolutionStage para reinterpretar EvolutionEvent ni recalcular
XP/niveles. No reasignar CharacterStats a una opción ni borrar/reasignar
StatAllocationEvent, XPEvent, EvolutionEvent o UserSpecializationProgress.
No permitir autoridades de escritura contradictorias entre active_specialization_code
y nueva selección explícita; activar coordinadamente servicios/consumidores.

Antes de migración: inventario de datos, clasificación explícita nuevos/heredados
y política aprobada de transición. Ausencia de UserPlayableState no significa
perfil nuevo. Core/P5 conserva relaciones definitivas, retención, anonimización/
eliminación y on_delete pendientes. Nueve entidades físicas no aumentan por este
contrato. DomainXPEvent y RewardEvent conservan sus propios bloqueos.

Los contratos [XP V1](ecomotor-xp-v1.md),
[asignación V1](ecomotor-stat-allocation-v1.md),
[selección V1](ecomotor-specialization-v1.md) y
[cambio V1](ecomotor-specialization-switch-v1.md) se conservan intactos.
S14-A integrado por #50 y S13-A1 por #47; sus notas anteriores de revisión son
antecedentes, no ausencia actual de implementación.

## 7. Pendientes y límites

Internos: códigos de épocas/tecnológicas, XP numérica, bases, presupuesto,
firmas, replay/revisión, reparto idéntico y detalles físicos de eventos/constraints.
Parámetros provisionales internos pueden versionarse/coordinarse sin ser oficiales.
Coordinación: inventario/migración legacy, conservación/Core/P5, consumo de stats
por juegos, dominio autorizado, S13-A2, activación conjunta y apariencia/vestimenta/
inventario con Henry. LOG = Lógica y CUACK = Especial / Especialización están
resueltos internamente por ATR-OBJ-01; bases, presupuesto, fórmulas y migración
legacy siguen abiertos. Elegir históricos, nivel 8 y redistribución gratuita/ilimitada
conservan aprobación interna. La nomenclatura previa SPE/LOG Logística es antecedente,
no la nomenclatura objetivo vigente ni una modificación de V1.
Rewards F2-A sigue bloqueado según sus dependencias. ARQ-OP-02 sí aprueba el diseño provisional de campos y restricciones de
PlayableOption, UserPlayableState y UserPlayableStats; no migraciones, relaciones
físicas definitivas ni on_delete. No se aprueban baremos de juegos.

## 8. Conciliación funcional posterior con Óscar

Consulta de CORE-03/CORE-07/PROF-04 y Training el 20/10/2026, con confirmación
directa de Jaime en 02C de las aclaraciones del profesor. [Procedencia](../decisions.md#conciliación-de-aclaraciones-de-óscar--20102026).
DAR3 y DOC-5/02C se conservan como antecedentes; la aclaración funcional posterior
no es aprobación de la solución Django ni del contrato técnico compartido.

Óscar confirmó **Ataque, Defensa, Velocidad, Inteligencia, Lógica y Cuak**,
específicos por época y distribución de puntos al alcanzar especialización.
En el corte de conciliación de la PR #61 se registró una discrepancia con
LOG (Logística) y SPE (Especial / Especialización) del diseño interno inicial:
códigos, significados, bases y presupuesto estaban pendientes de concreción.
ATR-OBJ-01 resuelve posteriormente solo la nomenclatura objetivo según §3;
no es una reinterpretación de snapshots ni una sustitución de campos V1.
Bases, presupuesto, fórmulas y transición legacy continúan pendientes.
En el corte histórico de conciliación, 45 puntos era ilustrativo. La decisión
interna posterior de §10 lo adopta provisionalmente, sin convertirlo en cifra
oficial de Óscar. Se conserva el resto de 02C
sin convertir este contraste en nuevas reglas de reparto o mejoras de Training.

Vestimenta visual: una imagen completa por época; en progresión histórica solo
la vigente, y tras elegir especialización se pueden reutilizar anteriores
desbloqueadas. DOC-5 proponía reutilización intermedia más amplia; no es conducta
confirmada. Identidad jugable histórica sigue distinta de apariencia: no inferir
que elegir un histórico en 02C equivale a la condición «elegir especialización».
Coordinar esa relación con Henry, sin decidir adquisición/autoequipamiento,
objetos, tablas o relaciones Duckies.

Se mantienen siete épocas históricas hasta Siglo XX y elección desde nivel 8.
No renombrar V1, reabrir la secuencia, activar A2 o cambiar contratos S3/Rewards.
[Pendientes residuales](../pending-decisions.md#17-aclaraciones-confirmadas-de-óscar--pendientes-residuales).

## 9. A4.3 · Preparación previa a configuración futura

[Contrato canónico A4.3](ecomotor-target-stats-preparation-v1.md) separa propuesta
pura, resolución autorizada y confirmación persistente. A4.1 (#74) y A4.2.1 (#76)
están integradas; la previsión inicial de preparador A4.3.1 se concretó e integró
por #78: conserva identidad/versiones/bases y reutiliza A4.1 con incrementos/
presupuesto explícitos. El antecedente conceptual no implementaba código.
No selecciona, redistribuye, autoriza o persiste por producir una propuesta válida.
Se mantienen precondiciones y límites SVC-OP-01…04, snapshot 02C, OP-RED-01 y
A3-CAT-01; no nuevas políticas de replay/concurrencia, campos o valores oficiales.

## 10. Precisiones posteriores · Presupuesto y recursos

[Registro del 21/10/2026](../decisions.md#doc-aclaraciones-2010--presupuesto-vestimentas-y-membresías--21102026)
tras aclaraciones funcionales del 20/10: A4-PRESUPUESTO-PROV-01 es una decisión
interna posterior, no de Óscar/DAR3. Adopta 45 puntos iniciales por opción, mismos
e independientes, con reparto completo/parcial/cero y sin saldo global consumido.
Valor revisable; bases y reglas adicionales pendientes. No defaults ni cambios de
APIs puras ni autorización por utilizar 45. Configuraciones persistentes futuras
requieren política expresa de versionado/cambio; no recálculo silencioso de confirmadas.

Una imagen completa por época está confirmada, pero las imágenes definitivas aún
no se han entregado al Equipo 5 según 02C. Recepción gráfica pendiente de Óscar;
Henry conserva avatar/apariencia. No se acredita integración visual completada ni
se bloquea implementación pura de evolución/estadísticas. Se mantiene vestimenta
vigente durante progresión histórica y anteriores desbloqueadas tras elegir
especialización; no nuevas reglas de adquisición, equipamiento o esquema Duckies.
[Coordinación](integracion-equipo5-v0.md#03-precisiones-posteriores--presupuesto-recursos-y-membresías)
y [pendientes](../pending-decisions.md#28-precisiones-2010--presupuesto-recursos-y-membresías).

## 11. A4.4 · Resolución antes de confirmación futura

[Contrato A4.4](ecomotor-target-stats-resolution-v1.md) separa estructura válida,
fuentes autorizadas, preparación pura integrada y confirmación persistente futura.
Servidor obtiene/verifica identidad, permisos, definición/bases/presupuesto y
versiones aplicables; opción/incrementos son entradas propuestas, sin que el cliente
imponga bases, presupuesto, catálogo o autoridad mediante flags. Sin API externa definitiva.
Primera configuración usa bases autorizadas aplicables; redistribución conserva
snapshot confirmado; cambio utiliza configuración propia confirmada; lectura usa
estado efectivo/configuración persistida con coherencia. No vigencia uniforme
impuesta ni recálculo silencioso. Definiciones retiradas/sustituidas/antiguas,
fuentes reales y acuerdos Core/Henry/consumidores siguen pendientes. 45 provisional
interno no autoriza configuración ni activa el objetivo. SVC-OP-01…04 no implementados.
