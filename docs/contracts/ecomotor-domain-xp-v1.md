# S12-A · Arquitectura conceptual de XP de dominio V1

**Contrato conceptual V1 — no implementado, sin autorización de migración ni de premios reales.**

## 1. Estado y autoridad

Jaime/Parte A aprueba internamente la **alternativa C** en «02B · Arquitectura y
repositorio · Continuación»: servicio propietario local de concesión positiva de
XP de dominio, preparado para integración posterior mediante Rewards.
Este registro DOC-S12-A parte de develop
`84f809df43c7db9b438a6541a298214ce8d97b50`, con S11-A integrado por PR #44.
No atribuye aprobación a Óscar/Core ni cierra P5/P7 o los contratos globales.

Las tres alternativas se plantearon explícitamente en la deliberación de 02B.
A/B no estaban incorporadas a los documentos del repositorio ni al contexto
documental recibido por Codex; esa ausencia documental no implica que faltaran en 02B:

- **A, estudiada:** servicio local de actualización de XP de dominio, con identidad
  e idempotencia suficientes y sin depender de F2-A.
- **B, estudiada:** concesión de XP de dominio exclusivamente coordinada por Rewards
  global, una vez aprobados sus contratos.
- **C, aprobada internamente:** separar el desarrollo en un núcleo local seguro y
  una integración posterior con Rewards, evitando mecanismos de concesión inseguros
  o incompatibles.

A/B fueron alternativas estudiadas, no decisiones aprobadas. No se añaden ventajas,
riesgos ni razones de descarte que no consten en la aclaración de 02B.

## 2. Fuentes funcionales y precedencia

Se conserva la [precedencia y trazabilidad de fuentes](../architecture.md#1-estado-y-fuentes):
DAR3 §§9–10 es la referencia principal de Ecomotor y coordinación de recompensas;
DuckyEcomotor y documentación complementaria precisan donde actualizan
explícitamente lo anterior. Las aclaraciones confirmadas y las contradicciones
registradas no se sustituyen por inferencias o ejemplos numéricos.

Los PDFs no están versionados en este repositorio; esta PR revisa su trazabilidad
documental existente, no acredita una nueva consulta directa de los originales.
[V2-A25/V2-A26](../decisions.md), el [ERD](../erd/ecomotor.md),
[S11-A](ecomotor-specialization-v1.md) y [Rewards v0](rewards-v0.md) son referencias
de estado y límites. Las seis decisiones siguientes proceden de la aprobación
interna de 02B, no de nuevos requisitos literales atribuidos a DAR3.

## 3. XP histórica y XP de dominio

XP histórica y XP de dominio son magnitudes independientes. S3 y XPEvent
permanecen dedicados a XP histórica; no se reutilizan como historial de dominio.
UserSpecializationProgress ya existe y persiste domain_xp_total por
perfil/especialización. S11-A crea el progreso inicial en cero y conserva un total
positivo válido al repetir; **no concede XP de dominio positiva**.

S12-A plantea concesiones positivas sobre ese acumulado, sin cambiar XP histórica,
nivel, etapa, estadísticas o puntos. La presencia del campo y su default cero
no significa que exista un servicio de concesión ni fuentes oficiales autorizadas.

## 4. Propiedad y coordinación · S12-A-01

Ecomotor es propietario del efecto de XP de dominio. Rewards conserva la
coordinación global de recompensas. El futuro servicio local no sustituye Rewards,
no legitima por sí mismo emisores ni evita la necesidad de contratos de confianza.
Esta separación no autoriza integración física ni transaccional con Rewards.

## 5. Elegibilidad de concesiones nuevas · S12-A-02

Una concesión nueva exige perfil Ecomotor válido e inicializado, especialización
activa coherente, progreso válido y elegibilidad coherente en Actual.
No se aprueban baremos, códigos oficiales ni requisitos funcionales adicionales.
La concreción técnica de estas comprobaciones y parámetros pertenece al contrato
de implementación futuro; no se extrapolan automáticamente políticas de S3 o S11-A.
Estados parciales o incompatibles no justifican inicialización, reparación o
cambio automático de especialización.

## 6. Identidad y causalidad · S12-A-04

Se aprueba el principio de identidad única de **origen, hecho y perfil**.
Debe vincularse causalmente el efecto a su destinatario y especialización, sin
deducir identidad o autorización de texto enviado por un cliente.
No se equipara automáticamente perfil con el User canónico o con recipient_id de
Rewards. Identificadores, representación, huellas, restricciones e interfaces
definitivas requieren concreción técnica y acuerdos de confianza.
No se fija constraint, longitud, algoritmo de huella ni esquema físico de claves.

## 7. Repetición histórica y conflictos

Una repetición coherente recupera el resultado histórico sin conceder XP adicional
ni reconstruirlo mediante catálogos actuales. Conflictos de identidad, importe o
especialización deben rechazarse, nunca tratarse como otra concesión.
No se reescribe historia ni se asume que el acumulado actual coincide con el
resultado de una operación anterior. Formato y suficiencia de los snapshots,
información del resultado recuperable y validaciones exactas quedan por concretar.
No hay implementación de deduplicación ni replay de dominio en esta PR.

## 8. Persistencia conceptual · S12-A-03

**DomainXPEvent es únicamente el modelo conceptual de trazabilidad aceptado.**
Debe permitir documentar la causa y recuperar una concesión original; no existe
como tabla, clase Django ni migración. No se aprueban campos/tipos concretos,
índices, FKs, cardinalidades físicas o políticas on_delete.
El inventario ORM sigue teniendo nueve entidades de Parte A; este concepto no
se añade a él. No se copia el CASCADE provisional de otros historiales locales.
Su persistencia física está bloqueada por conservación, anonimización y eliminación
con Core, incluidas las relaciones con perfil y progreso de especialización.

## 9. Atomicidad y concurrencia · S12-A-05

Evento y acumulado de dominio deben confirmarse o revertirse conjuntamente.
D-19 exige operaciones transaccionales, concurrencia segura, SQLite IMMEDIATE
en el entorno actual, rechazo de duplicados/estados parciales, errores operativos
diferenciados y rollback ante fallos. No se promete atomicidad entre BD o sistemas
independientes. Frontera transaccional concreta y composición con Rewards siguen
pendientes; este registro no implementa bloqueos, retries ni escrituras.

## 10. Frontera de confianza y autorización · S12-A-06

Premios reales requieren origen autorizado, asociación confiable del hecho con
el destinatario y reglas de concesión validadas. **ValidatedRewardFact por sí solo
no autoriza premios**: F1-A comprueba estructura semántica y presupone confianza
del consumidor interno, sin autenticar el emisor. authorized_context sigue siendo
un concepto pendiente de estructura y verificación, no una credencial disponible.

La aprobación conceptual no autoriza aún el modelo ORM DomainXPEvent ni ninguna
migración: Core debe acordar conservación, anonimización/eliminación y on_delete.
**S12-A no desbloquea Rewards F2-A**, cuyo bloqueo DOC-6 permanece íntegro.

## 11. Contrato candidato de entrada y salida

Propuesta pendiente de concreción, **no API disponible ni firma Python definitiva**:

```text
grant_domain_xp(profile, validated_fact, amount, authorized_context) -> DomainXPGrantResult
```

Los nombres expresan perfil objetivo, hecho, importe positivo y contexto confiable.
No se fijan tipos concretos, transporte, estructura de authorized_context o modo
de verificar al emisor. DomainXPGrantResult es un nombre conceptual para distinguir
concesión y repetición y conservar su resultado causal; sus campos y tipos no están
definidos. No se atribuye a RewardDecision puro una aplicación transaccional.

Conceptualmente aprobados: propiedad local, separación de XP, elegibilidad,
identidad causal, prevención de duplicados, repetición/conflictos y atomicidad.
No aprobados: firma/tipos definitivos, huellas y constraints, esquema físico y
borrado, integración transaccional Rewards, fuentes/cantidades/límites oficiales
o umbrales de rangos. Ningún identificador de ejemplo se activa como producción.

## 12. Errores previstos, sin clases definitivas

El diseño futuro debe distinguir entradas/perfil inválidos, especialización no
seleccionada, progreso inconsistente, falta de elegibilidad/configuración,
origen/destinatario no autorizados, conflictos históricos y fallos operativos.
No se fijan nombres de excepciones, códigos HTTP, tipos de resultado o políticas
de retry. Un fallo no debe convertirse en concesión, reparación o replay aparente.

## 13. Pruebas futuras pendientes de implementación

- Primera concesión positiva y acumulación por hechos distintos.
- Repetición coherente sin duplicación; conflictos de identidad, cantidad y
  especialización; snapshots originales y replay sin reinterpretar catálogos.
- Perfil ausente/inválido, especialización no seleccionada, progreso inconsistente,
  elegibilidad en Actual e integridad de propietarios/destinatarios.
- Fallos y rollback de evento/acumulado, concurrencia real SQLite file-backed,
  timeout y reintento en nueva transacción, alias alternativos.
- Ausencia de modificación de XP histórica y regresiones S3, S11-A y demás
  servicios afectados; frontera de autorización según el contrato que se acuerde.

Estas pruebas no se crean ni ejecutan aquí. Los 611 tests de S11-A corresponden
a la última suite comunicada, no a una ejecución de este PR documental.

## 14. Dependencias y puertas de avance

| Antes de avanzar | Pendiente |
| --- | --- |
| Modelo físico y migración | Acuerdo Core sobre conservación, anonimización/eliminación y on_delete de DomainXPEvent y sus relaciones; P5 abierto. |
| Servicio implementable | Concretar firma/tipos, identidad y huellas, snapshots/resultado histórico, errores y frontera transaccional, sin cerrar contratos por inferencia. |
| Premios reales | Origen autorizado, vínculo confiable hecho–destinatario y reglas de concesión validadas. Fuentes, cantidades y límites no están aprobados. |
| Integración Rewards/juegos | Contratos compartidos y autorización correspondientes; F2-A mantiene su bloqueo independiente. |
| Progresión por rangos | P7 abierto; S13-A solo prioridad funcional provisional futura para estudiar Junior → Middle → Senior → Maestro, sin arquitectura ni umbrales aprobados. |

## 15. Exclusiones

No implementación S12-A, DomainXPEvent ORM, migraciones, seeds, premios reales,
cambios a User/Core, S3/S11-A o Rewards. Sin rangos, XP histórica adicional,
cambio/reinicio de especialización, estadísticas/puntos, inventario, economía,
endpoints, formularios, REST/WebSockets ni modificación de bases locales.
Este documento no cierra P5/P7, DOC-6 ni contratos globales de Rewards v0 candidato.
