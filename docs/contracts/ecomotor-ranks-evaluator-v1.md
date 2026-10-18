# S13-A / S13-A1 · Contrato del evaluador de rangos V1

## 1. Estado, autoridad y fuentes

**Arquitectura aprobada internamente; contrato técnico candidato, no implementado.**
DOC-S13-A1 parte de develop `5d36778449e7c796e2770ddfdb97f25e8f8b280f`,
con S11-A (#44) y DOC-S12-A (#45) integrados. Jaime/Parte A aprueba S13-A-01…07
y las precisiones S13-A1 en «02B · Arquitectura y repositorio · Continuación».
No es aprobación de Óscar/Core ni cierre de P5/P7.

DAR3 es la fuente principal de requisitos funcionales. Se conserva la
[precedencia documental](../architecture.md#1-estado-y-fuentes) y el contraste con
DuckyEcomotor: el [ERD](../erd/ecomotor.md) ya registra Junior, Middle, Senior y
Maestro como rangos funcionales, sin esquema físico ni baremos aprobados.
Los PDFs originales siguen sin versionarse; este documento utiliza su trazabilidad
existente, sin afirmar una nueva lectura directa ni atribuir a DAR3 las convenciones
técnicas internas siguientes.

## 2. Decisiones internas S13-A

| ID | Decisión aprobada internamente |
| --- | --- |
| S13-A-01 | Rangos independientes por especialización: sin rango → Junior → Middle → Senior → Maestro. |
| S13-A-02 | Ascensos secuenciales, con requisitos configurables; no saltar rangos. |
| S13-A-03 | XP histórica y nivel general independientes de los rangos. |
| S13-A-04 | Evaluación pura separada de la confirmación persistente del ascenso. |
| S13-A-05 | Requisitos de XP de dominio, cursos y retos mediante evidencias verificadas. |
| S13-A-06 | Ascensos confirmados trazables e idempotentes, conservados al cambiar de especialización. |
| S13-A-07 | Políticas versionadas, sin recalcular ni retirar silenciosamente rangos históricos. |

Se registra además la conservación del progreso de las **cinco especializaciones**
al alternar entre ellas como decisión interna. No define códigos canónicos ni
autoriza un servicio de cambio: S11-A sigue limitado a la primera selección y
rechaza una selección distinta. No se borrará ni reiniciará progreso por inferencia.

También se registra la **opción B de importes independientes de XP general
(histórica) y XP de dominio**. No hay igualdad, proporción, conversión o doble
concesión automática. No se fijan cantidades oficiales, fuentes ni autorización;
no debe confundirse esta opción B con las alternativas A/B/C de S12-A.

## 3. Alcance puro y precisiones S13-A1

- XP mínima de dominio para Junior estrictamente positiva; umbrales estrictamente
  crecientes hasta Maestro. No se proporcionan valores de producción.
- Todos los requisitos configurados se combinan con **AND**.
- Cursos y retos son opcionales si la política no los exige. Su ausencia en la
  política no equivale a afirmar que el usuario los haya completado.
- Evidencia requerida no disponible no equivale a cumplimiento.
- Solo se evalúa el siguiente rango. Un exceso de XP no permite saltos ni encadenar
  confirmaciones en una llamada.
- Una evaluación nunca confirma un ascenso, incluso cuando devuelve ELIGIBLE.

El evaluador recibe datos explícitos. No consulta ORM, red, disco, sesión, reloj
del sistema o configuración global; no autentica emisores, no concede XP ni premios,
no actualiza progreso y no genera eventos. No exige que S12-A esté implementado
para evaluar datos sintéticos; tampoco legitima una concesión real de dominio.

## 4. Interfaz y estructuras candidatas

```text
evaluate_rank_eligibility(progress, evidence, policy) -> RankAssessment
```

Interfaz candidata, no API Python disponible. Se proponen valores inmutables con
copia defensiva de colecciones; no son modelos ORM ni campos Django aprobados.
Los identificadores de especialización son referencias opacas exactas, sin asumir
la representación de la PK de User ni inventar un catálogo oficial.

| Estructura | Información y semántica candidata |
| --- | --- |
| RankProgress | Referencia de especialización, rango confirmado actual (ausente para «sin rango») y XP de dominio acumulada no negativa. El rango se aporta como hecho confirmado, nunca se deduce de XP. |
| RankRequirement | Rango destino, XP mínima de dominio y colecciones explícitas de referencias de cursos y retos requeridos; colecciones vacías significan que no se exigen. |
| RankPolicy | Identidad/versionado de política, ámbito de especialización y requisitos ordenados para Junior, Middle, Senior y Maestro. No hay política por defecto. |
| RankEvidence | Evidencias verificadas aplicables al mismo ámbito y sujeto del progreso; permite distinguir requisito cumplido, no cumplido y evidencia no disponible. Ausencia de una referencia requerida no prueba cumplimiento ni incumplimiento verificado. |
| RankAssessment | Versión de política evaluada, referencia de especialización, rango actual, siguiente rango (o ausente), estado y diagnósticos estructurados de requisitos. No contiene confirmación, premio aplicado, ID de evento ni replay persistente. |

El adaptador futuro debe garantizar la vinculación confiable de evidencia,
destinatario y especialización. Forma física, credenciales, tipos definitivos de
identidad y protocolo de autorización siguen pendientes. El evaluador solo valida
coherencia estructural de lo recibido; no convierte declaraciones del navegador
o un ValidatedRewardFact en evidencia autorizada.

## 5. Validaciones e invariantes

- Entradas presentes y estructuralmente válidas, sin conversiones silenciosas.
  XP y umbrales enteros exactos, excluyendo bool; XP acumulada no negativa.
  Sin nuevos máximos funcionales ni límites de campos ORM en el núcleo puro.
- Rango actual ausente o uno de los cuatro rangos reconocidos; orden único y
  completo de requisitos, sin destinos duplicados, omitidos o desconocidos.
- Junior exige XP positiva; los cuatro umbrales crecen estrictamente. Una política
  incompleta o inválida es error, no una evaluación favorable ni PENDING.
- Versión e identidades no vacías y coherentes entre entradas; referencias de
  cursos/retos inequívocas, sin alias o normalizaciones implícitas.
- Evidencias con estados explícitos válidos; contradicciones estructurales o
  pertenencia incompatible son errores, no cumplimiento.
- Evaluar exactamente el sucesor del rango confirmado y solo sus requisitos.
  El umbral se cumple con igualdad o exceso de XP; no se resta XP al evaluar.
- No exigir que un rango confirmado vuelva a satisfacer una política nueva.
  No degradar, recalcular ni retirar historia. La política evaluada queda
  identificada en el resultado, sin afirmar que confirmó rangos anteriores.

La representación concreta de estas estructuras y nombres de excepciones quedará
fijada en el encargo de implementación; no se fija aquí un esquema persistente.

## 6. Estados y resultado

| Estado | Semántica |
| --- | --- |
| ELIGIBLE | Todos los requisitos configurados del siguiente rango están cumplidos con datos/evidencias disponibles. Solo evaluación; no ascenso confirmado. |
| PENDING | Hay requisitos del siguiente rango conocidos como no cumplidos. No implica concesión ni cambio del rango actual. |
| EVIDENCE_UNAVAILABLE | Falta evidencia requerida para completar la evaluación; nunca se sustituye por cumplimiento. |
| MAX_RANK | El rango confirmado ya es Maestro; no hay siguiente rango ni ascenso propuesto. |

Para el contrato técnico candidato, tras validar las entradas, MAX_RANK no exige
evidencias de un rango inexistente. Para un sucesor, si falta evidencia requerida
se informa EVIDENCE_UNAVAILABLE, conservando en diagnósticos los incumplimientos
conocidos; con evidencia suficiente, un incumplimiento produce PENDING y todos
cumplidos ELIGIBLE. Esta precedencia explícita evita que el estado oculte que
faltan datos; no cambia la combinación AND ni autoriza un ascenso parcial.

Sin cursos/retos configurados, basta cumplir el requisito de XP del siguiente
rango. No se exige evidencia de requisitos ajenos a la política ni de rangos
posteriores. No se devuelve un estado APPLIED ni una confirmación implícita.

## 7. Errores previstos

Separar progreso inválido, política inválida y evidencia estructuralmente inválida
o incompatible. Evidencia requerida legítimamente no disponible es un estado de
evaluación, no un error de programación ni prueba de incumplimiento verificado.
No capturar indiscriminadamente excepciones ni convertir una entrada inválida
en ELIGIBLE/PENDING. Los diagnósticos no expondrán payloads privados o secretos.
Clases Python y detalles de serialización aún no se implementan ni se fijan aquí.

## 8. Compatibilidad, confirmación y límites

[S11-A](ecomotor-specialization-v1.md) conserva primera selección y repetición
basada en estado. Su rechazo de cambios sigue vigente hasta diseñar esa política.
[S12-A](ecomotor-domain-xp-v1.md) conserva sus seis decisiones, DomainXPEvent
solo conceptual y el bloqueo físico por Core. Las referencias anteriores a S13-A
como prioridad sin diseño corresponden al corte DOC-S12-A, superado en este
ámbito por la aprobación interna aquí registrada, sin reescribir sus decisiones.

V2-A25/A26 y el [ERD físico](../erd/ecomotor.md) permanecen intactos:
UserSpecializationProgress almacena domain_xp_total, sin campo de rango integrado.
No se crea entidad/evento de ascenso ni se decide FK, on_delete o conservación física.
Los ascensos futuros confirmados deberán ser trazables e idempotentes; mecanismo,
snapshots, claves, migraciones y contrato de confirmación siguen pendientes.

D-19 rige futuras escrituras locales: atomicidad, concurrencia y rollback bajo
SQLite IMMEDIATE. No exige transacciones de escritura o bloqueos para este núcleo
puro ni garantiza atomicidad entre sistemas. Una evaluación puede quedar obsoleta;
la coordinación y comprobaciones al confirmar deben diseñarse posteriormente.

[Rewards v0](rewards-v0.md) continúa candidato y F2-A bloqueado. Evaluar un rango
no concede premios. P5/P7 siguen abiertos: valores oficiales, códigos, autorización
de evidencias, cambios/reinicios de especialización, persistencia física y
recompensas tardías (atribución a especialización/política/momento) por resolver.
No se decide retrospectividad, reasignación o recálculo de esos casos.

## 9. Matriz de pruebas futuras, no ejecutadas ni implementadas

| Grupo | Casos requeridos |
| --- | --- |
| Secuencia | Sin rango evalúa Junior; Junior evalúa Middle; Middle evalúa Senior; Senior evalúa Maestro; Maestro devuelve MAX_RANK; nunca saltar rangos por exceso de XP. |
| Umbrales | Junior positivo; cero/negativos/bool/tipos inválidos rechazados; umbrales iguales o decrecientes rechazados; debajo/igual/encima del siguiente umbral. |
| AND | XP suficiente con curso o reto pendiente no es ELIGIBLE; todos cumplidos sí; cursos/retos no exigidos no bloquean. |
| Disponibilidad | Evidencia ausente distingue no disponible de cumplida/no cumplida; diagnóstico combinado con incumplimientos conocidos; no solicitar evidencia de rangos posteriores. |
| Validación | Política ausente/incompleta, versión vacía, destinos duplicados/desordenados, referencias incompatibles y progreso inválido; errores diferenciados sin éxito aparente. |
| Independencia | Misma XP histórica/nivel no implica mismo rango; dos especializaciones conservan progreso/rango independientes; no modificar ninguna de las cinco al evaluar otra. |
| Historia y versiones | Conservar rango confirmado bajo política distinta; identificar versión evaluada; sin degradación ni reconstrucción histórica. |
| Pureza | Determinismo con mismas entradas; inmutabilidad profunda/copia defensiva; entradas intactas; sin ORM, I/O, reloj, premios, eventos o confirmación. |
| Frontera | Evidencia estructural no acredita autorización externa; evaluación no equivale a ascenso; importes general/dominio independientes, sin conversión automática. |

Todas estas pruebas pertenecen a una implementación futura. Esta PR solo valida
documentos y enlaces; no crea tests Python ni afirma haber ejecutado la suite de
611 tests comunicada tras S11-A.
