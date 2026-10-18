# S14-A · Arquitectura del cambio de especialización V1

## 1. Estado, autoridad y fuentes

**Arquitectura aprobada internamente; contrato técnico candidato, no implementado.**
DOC-S14-A parte de develop `e401c33045b4f1b4c8621c54c21757483769b56b`, con
S13-A1 integrado por PR #47. Jaime/Parte A comunica la aprobación en
«02B · Arquitectura y repositorio · Continuación». No es aprobación de Óscar/Core
ni autorización para implementar el servicio mediante esta PR documental.

DAR3 sigue siendo la fuente principal. La [trazabilidad de fuentes](../architecture.md#1-estado-y-fuentes)
registra sus requisitos generales de Ecomotor, progresión y recompensas y el apoyo
de DuckyEcomotor para especializaciones en Actual. Las reglas técnicas siguientes
son decisiones internas, no requisitos literales nuevos atribuidos a los PDFs.
Los originales no están versionados en el repositorio; se consulta su trazabilidad
documental existente, sin afirmar una nueva lectura directa. Las contradicciones
y aprobaciones externas pendientes se conservan en [pendientes](../pending-decisions.md).

## 2. Decisiones internas aprobadas

| ID | Decisión y límite |
| --- | --- |
| S14-A-01 | Cada perfil tiene una sola especialización activa y puede conservar progreso independiente en las cinco especializaciones. |
| S14-A-02 | Primera activación de una especialización nunca utilizada: progreso con domain_xp_total = 0 y estado funcional «sin rango». |
| S14-A-03 | Retorno a una especialización anterior: reutilizar su progreso, sin reiniciar XP de dominio ni rangos confirmados. |
| S14-A-04 | No modificar XP histórica general, nivel, etapa, estadísticas ni recompensas; no transferir XP entre ramas. |
| S14-A-05 | Servicio local transaccional separado de la primera selección, con comprobación del estado activo esperado y concurrencia segura conforme a D-19. |
| S14-A-06 | V1 sin evento físico de cambio. Idempotencia por estado, sin promesa de idempotencia histórica completa. |
| S14-A-07 | Atribución de recompensas tardías pendiente con S12-A, Rewards y Core. |

El cambio se realizará en **Actual**, sin retroceder de etapa ni consumir XP
histórica. No se fijan baremos, códigos oficiales, costes ni premios nuevos.
«Sin rango» expresa estado funcional; no afirma que exista un campo físico de rango.

## 3. Interfaz candidata y confianza

```text
switch_active_specialization(profile, target_code, expected_active_code) -> SpecializationSwitchResult
```

Propuesta de interfaz, no API disponible ni contrato HTTP.

- `profile`: perfil persistido e inicializado del ámbito autorizado del consumidor.
  Recargar desde su alias de BD, sin confiar en atributos cacheados ni presumir la
  representación de la PK del User canónico. No crear User, perfil ni estadísticas.
- `target_code`: código exacto de una especialización existente en el catálogo
  Specialization. Validar estructura y límites existentes; sin normalizar,
  convertir, crear catálogo o deducir códigos oficiales.
- `expected_active_code`: estado activo que el solicitante espera encontrar.
  Es una precondición de concurrencia, no una autorización, clave histórica o
  prueba de propiedad. Comparar con el estado persistido dentro de la transacción;
  una lectura antigua del consumidor no permite sobrescribir un cambio ajeno.

El futuro adaptador debe resolver identidad y autorización confiables; un código
enviado por un navegador no acredita ninguna de ellas. No se define transporte,
autenticación nueva o integración global con Core.

## 4. Precondiciones, estados y resultado

Perfil existente con CharacterStats estructuralmente válido, especialización
activa coherente y su progreso perteneciente al mismo perfil. El cambio nuevo
requiere Actual coherente con XP histórica, configuración confiable de etapas y
catálogo pertinente válido. No basta comparar con un literal inventado de etapa.
No recalcular nivel, reparar datos legacy ni modificar estadísticas para habilitarlo.

Validar las referencias de especialización y los progresos existentes: propietario,
unicidad por pareja, XP de dominio no negativa representable y coherencia con la
selección activa. Varias filas coherentes son el estado que S14-A debe admitir;
referencias ausentes, selección activa sin progreso o datos incompatibles no se
reparan silenciosamente. La política exacta de compatibilidad S11-A queda en §5.

| Situación coherente | Resultado conceptual |
| --- | --- |
| Objetivo distinto, nunca utilizado y estado esperado correcto | Crear su progreso en cero y cambiar solo el código activo; ambos efectos atómicos. Estado funcional sin rango, sin crear un campo de rango. |
| Objetivo distinto con progreso anterior y estado esperado correcto | Reutilizar la fila original y sus valores; cambiar solo el código activo. No transferir ni reinicializar XP o rangos. |
| Objetivo ya activo, repetición coherente | Recuperar el estado existente sin crear duplicados ni escribir progreso. La relación exacta con la precondición esperada debe concretarse antes de implementar (§5). |

SpecializationSwitchResult deberá distinguir primera activación, reutilización y
repetición, e identificar el perfil, especialización activa y progreso resultante.
Nombres/tipos definitivos de campos quedan candidatos. No incluir concesiones,
rangos confirmados por esta llamada, evento de cambio inexistente ni un indicador
que sugiera replay histórico completo.

## 5. Compatibilidad S11-A y precisiones previas a implementación

El [servicio S11-A integrado](../../apps/ecomotor/specialization_service.py) y su
[contrato](ecomotor-specialization-v1.md) permiten primera selección y repetición
con exactamente un progreso. `_existing_selection()` rechaza `len(rows) != 1`;
el test `test_active_selection_with_incompatible_or_multiple_progress_rejected`
en [sus pruebas](../../apps/ecomotor/test_specialization_service.py) lo verifica.
S11-A también rechaza seleccionar otro código. Estas garantías actuales no se
reinterpretan ni se cambia código en DOC-S14-A.

El [modelo integrado](../../apps/ecomotor/models.py) UserSpecializationProgress
ya permite varias filas por perfil con unicidad `(profile, specialization)`;
el [perfil](../../apps/users/models.py) conserva un único código activo. El esquema
no exige una tabla nueva para acumular progreso de varias especializaciones.
La futura implementación deberá adaptar cuidadosamente la validación S11-A,
preservando primera selección, repetición sin reset y detección de inconsistencias.

**Cuestiones explícitas para 02B antes de implementar:**

1. Contrato de S11-A tras varios progresos coherentes: concretar cómo recuperará
   una selección activa al repetirse y cómo rechazará una selección diferente;
   no decidir aquí qué nuevas combinaciones de filas aceptará su validación.
2. Precedencia entre objetivo ya activo y `expected_active_code` obsoleto:
   concretar si esa solicitud se rechaza como obsoleta o se recupera como
   repetición. El control esperado es obligatorio; no se adopta una excepción
   por inferencia. También precisar si una repetición requiere volver a validar
   configuración y Actual o sigue otra política de recuperación.

No se copia automáticamente la política de replay histórico de S11-A/S12-A.
Estos puntos requieren precisión de implementación, no autorizan ampliar el
alcance, reparar estados ni modificar ahora las decisiones aprobadas.

## 6. Errores previstos

Separar perfil inválido/inexistente, código inválido o inexistente, configuración
o catálogo inválido, etapa no elegible, estado persistido incoherente, solicitud
obsoleta por estado esperado incorrecto y fallo real de BD. No se fijan todavía
clases Python ni códigos HTTP. No presentar un error de BD como éxito/repetición;
preservar su causa y no capturar errores arbitrarios de programación.

## 7. Atomicidad y concurrencia D-19

El futuro servicio abrirá `transaction.atomic(using=alias)` antes de leer el
estado mutable, recargará perfil/estadísticas/progresos y comprobará el estado
activo esperado dentro de la misma frontera que crea/reutiliza el progreso y
actualiza el código activo. SQLite actual utiliza BEGIN IMMEDIATE y timeout 5 s;
no depender de select_for_update como bloqueo de fila.

Creación de progreso y actualización del perfil confirman o revierten juntas.
La unicidad existente por pareja es defensa persistente, no autorización para
sobrescribir. Dos objetivos distintos concurrentes deben comprobar el estado
efectivo serializado; una solicitud que dejó de cumplir su precondición se rechaza,
sin pérdida de actualizaciones. Fallos, bloqueo o timeout hacen rollback; retry
explícito en nueva transacción, sin éxito aparente ni bucles automáticos.
Sin I/O remoto dentro de la transacción ni atomicidad prometida entre sistemas.

## 8. Idempotencia por estado y A → B → A

Repetir un objetivo coherente ya activo no debe duplicar progreso ni reiniciarlo,
con la precisión de precondición pendiente en §5. V1 no crea evento de cambio ni
almacena identidad histórica de cada solicitud.

Si el perfil pasa A → B → A, una solicitud antigua que esperaba A vuelve a
encontrar ese código, aunque hayan ocurrido cambios intermedios. Comparar solo
el estado no permite distinguirla de una solicitud nueva ni reconstruir la primera
respuesta. No prometer detección histórica de esos reintentos o exactamente una
ejecución histórica; la conservación del progreso sí sigue siendo obligatoria.
No añadir tokens persistentes, eventos o versiones físicas para resolverlo aquí.

## 9. Compatibilidad S12-A, rangos y Core

[S12-A](ecomotor-domain-xp-v1.md) mantiene la concesión nueva de XP de dominio
conceptualmente limitada a la especialización activa y Actual. S14-A no concede
XP de dominio ni introduce excepciones a S12-A-02.

[S13-A1](ecomotor-ranks-evaluator-v1.md) ya está implementado por PR #47 como
[evaluador puro](../../apps/ecomotor/rank_progression.py). El cambio no lo llama
para otorgar rangos automáticamente. S13-A2, confirmación y persistencia de rangos,
sigue pendiente. Conservar rangos confirmados es una decisión funcional, no un
campo existente ni una migración autorizada.

P5/Core mantiene conservación, anonimización/eliminación y on_delete pendientes.
No crear tablas, relaciones o políticas de borrado. DomainXPEvent sigue conceptual,
[Rewards v0](rewards-v0.md) candidato global y Rewards F2-A bloqueado. No premios reales.

## 10. Recompensa tardía: incompatibilidad pendiente

Ejemplo ilustrativo, sin aprobar códigos canónicos ni baremos:

1. Una actividad válida ocurre mientras Developer está activo.
2. El usuario cambia a Gamer.
3. La recompensa de aquella actividad llega después.

La propuesta funcional preferida atribuye XP de dominio a la especialización
vinculada a la actividad original. **No está aprobada como excepción operativa.**
Si Developer ya no está activo, esa atribución entra en conflicto con la
precondición de concesión nueva S12-A-02. Antes de implementarla, revisar esa regla
con S12-A, Rewards y Core y definir evidencias confiables de la especialización
activa al realizar la actividad, su vínculo con el hecho y destinatario.
No adoptar automáticamente Gamer por estar activo al procesar, ni atribuir a
Developer por una declaración no verificada. No reinterpretar silenciosamente
S12-A, política temporal, identidad causal o autorización de la recompensa.

## 11. Matriz de pruebas futuras, no implementadas ni ejecutadas

Usar exclusivamente códigos y configuración sintéticos, sin seeds oficiales.
Developer/Gamer son etiquetas ilustrativas del escenario, no fixtures de producción.

| Grupo | Comprobaciones necesarias |
| --- | --- |
| Primera activación | Developer → Gamer con nuevo progreso Gamer, XP cero y estado funcional sin rango; selección/progreso atómicos. |
| Reutilización | Gamer → Developer conserva fila y XP originales; alternar las cinco conserva progresos independientes y rangos confirmados cuando exista su persistencia. |
| Repetición | Mismo objetivo activo sin duplicados ni reset; precondición y configuración según precisión pendiente de §5. |
| Validación | Código inexistente; perfil/stats/progreso/catálogo incoherentes; referencias/propietarios inválidos; etapa anterior o incoherente; estado activo esperado incorrecto. |
| Concurrencia | Dos conexiones SQLite file-backed, objetivos distintos, BEGIN IMMEDIATE antes de lectura, estado esperado serializado; sin sobrescrituras, huérfanos o duplicados; timeout y retry. |
| Rollback | Fallo al crear progreso o actualizar perfil revierte ambos cambios; errores de BD con causa preservada. |
| Regresión S11-A | Primera selección, repetición, rechazo de inconsistencias y comportamiento expresamente acordado para múltiples progresos coherentes. |
| Historia limitada | A → B → A evidencia el límite de detección de solicitudes antiguas; no simular replay histórico completo. |
| Sin efectos ajenos | XP histórica, nivel, etapa, seis stats, puntos y recompensas intactos; sin transferencias, XP de dominio concedida, rangos nuevos ni efectos Rewards. |

Esta PR solo registra arquitectura y pendientes. No ejecuta tests Django, cambia
servicios, modelos/migraciones, endpoints, archivos de demo ni bases SQLite.
