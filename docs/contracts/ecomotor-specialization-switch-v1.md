# S14-A · Arquitectura del cambio de especialización V1

## 1. Estado, autoridad y fuentes

**Arquitectura aprobada internamente; servicio implementado en PR para revisión,
todavía sin integrar.** API y resultados implementados en §12. Los cortes
DOC-S14-A y S14-A-08/09 siguientes conservan la trazabilidad de su aprobación.
DOC-S14-A parte de develop `e401c33045b4f1b4c8621c54c21757483769b56b`, con
S13-A1 integrado por PR #47. Jaime/Parte A comunica la aprobación en
«02B · Arquitectura y repositorio · Continuación». No es aprobación de Óscar/Core.
El registro documental original no implementaba el servicio; el estado actual en
PR se precisa en §12, sin ampliar las decisiones aprobadas.

**Precisiones S14-A-08/09:** registradas sobre develop
`f4c9ce4167f37dcf302b3b3093333a688068e801` (DOC-S14-A, PR #48).
Aprobadas internamente por Jaime/Parte A en 02B; completan las reglas de
compatibilidad y repetición. En ese corte eran documentales; la implementación
para revisión parte de develop `00d39570619ee47a054c8605068284f2a24da225`.

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
| S14-A-08 | S11-A admitirá varios progresos coherentes de especializaciones distintas y validará su integridad. Repetir el código activo recuperará su progreso sin escrituras ni reevaluación de configuración de etapas, manteniendo validación estructural; otra selección seguirá siendo conflicto y la primera selección conservará su comportamiento. |
| S14-A-09 | S14-A comprobará expected_active_code antes de resolver una repetición. Si no coincide con la activa persistida, rechazará la solicitud aunque el objetivo ya esté activo. Si coincide y el objetivo está activo, devolverá el estado coherente sin escrituras ni reevaluación de configuración de etapas. Un cambio efectivo requiere Actual y transacción D-19. |

El cambio se realizará en **Actual**, sin retroceder de etapa ni consumir XP
histórica. No se fijan baremos, códigos oficiales, costes ni premios nuevos.
«Sin rango» expresa estado funcional; no afirma que exista un campo físico de rango.

## 3. Interfaz local y confianza

```text
switch_active_specialization(profile, target_code, expected_active_code) -> SpecializationSwitchResult
```

Interfaz Python interna implementada en specialization_switch_service.py,
pendiente de revisión/merge. No contrato HTTP ni autorización global.

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
reparan silenciosamente. La compatibilidad S11-A aprobada se precisa en §5.

| Situación coherente | Resultado conceptual |
| --- | --- |
| Objetivo distinto, nunca utilizado y estado esperado correcto | Crear su progreso en cero y cambiar solo el código activo; ambos efectos atómicos. Estado funcional sin rango, sin crear un campo de rango. |
| Objetivo distinto con progreso anterior y estado esperado correcto | Reutilizar la fila original y sus valores; cambiar solo el código activo. No transferir ni reinicializar XP o rangos. |
| Estado esperado distinto de la activa persistida, incluso si el objetivo ya está activo | Rechazar como solicitud obsoleta; no convertirla en repetición ni escribir. |
| Estado esperado correcto y objetivo ya activo, con estado coherente | Recuperar el estado existente sin escrituras, duplicados, reevaluación de configuración de etapas ni nueva comprobación de elegibilidad en Actual; mantener validación estructural. |

SpecializationSwitchResult distingue primera activación, reutilización y
repetición e identifica perfil, especialización activa y progreso (§12).
No incluye concesiones,
rangos confirmados por esta llamada, evento de cambio inexistente ni un indicador
que sugiera replay histórico completo.

## 5. Compatibilidad S11-A y orden aprobado · S14-A-08/09

El antecedente S11-A integrado por PR #44 exigía exactamente un progreso en
`_existing_selection()`. La adaptación S14-A-08 en esta PR valida todas las filas
y admite varias coherentes, recuperando la activa. El
[contrato S11-A actualizado](ecomotor-specialization-v1.md) y
[sus pruebas](../../apps/ecomotor/test_specialization_service.py) distinguen ahora
varios progresos válidos de referencias incompatibles o activa sin progreso.
S11-A sigue rechazando seleccionar otro código y mantiene la primera elección.

El [modelo integrado](../../apps/ecomotor/models.py) UserSpecializationProgress
ya permite varias filas por perfil con unicidad `(profile, specialization)`;
el [perfil](../../apps/users/models.py) conserva un único código activo. El esquema
no exige una tabla nueva para acumular progreso de varias especializaciones.
La adaptación S11-A en esta PR aplica **S14-A-08**:

1. Validar estructuralmente perfil, CharacterStats y todos los progresos: identidades
   y propietarios correctos, especializaciones existentes y distintas, unicidad por
   pareja y XP de dominio válida. Varias filas coherentes no serán una inconsistencia
   por su cantidad; referencias incompatibles o progreso activo ausente seguirán
   rechazándose sin reparación.
2. Repetir el código activo recuperará su fila de progreso, conservando XP de
   dominio y sin escrituras ni reevaluación de configuración/catálogos de etapas
   o elegibilidad actual. Se mantiene la validación estructural del estado persistido.
3. Solicitar otro código mediante S11-A seguirá siendo conflicto; S11-A no se
   convertirá en servicio de cambio. Su primera selección mantiene el comportamiento
   integrado, incluidas precondiciones y rechazo de estados parciales.

S14-A aplica **S14-A-09** dentro de la transacción D-19:

1. Recargar y validar el estado persistido, manteniendo las comprobaciones estructurales.
2. Comprobar `expected_active_code` antes de tratar una solicitud como repetición.
   Si no coincide con la activa persistida, rechazarla aunque `target_code` coincida.
3. Si el valor esperado coincide y el objetivo ya está activo, devolver su estado
   coherente sin escrituras, sin reevaluar configuración/catálogos de etapas ni
   exigir de nuevo Actual. No reinicializar progreso.
4. Solo para un cambio efectivo a otra rama, comprobar las precondiciones de
   Actual, configuración y catálogo de etapas y crear/reutilizar el progreso,
   actualizando la activa conjuntamente conforme a D-19.

Estas precisiones resuelven las preguntas del corte DOC-S14-A; no autorizan
reparaciones, cambios físicos, nuevos baremos ni replay histórico completo.

## 6. Errores previstos

Separar perfil inválido/inexistente, código inválido o inexistente, configuración
o catálogo inválido, etapa no elegible, estado persistido incoherente, solicitud
obsoleta por estado esperado incorrecto y fallo real de BD. Las clases Python
implementadas figuran en §12; no se definen códigos HTTP. No presentar un error de BD como éxito/repetición;
preservar su causa y no capturar errores arbitrarios de programación.

## 7. Atomicidad y concurrencia D-19

El servicio abre `transaction.atomic(using=alias)` antes de leer el
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
siempre que el estado esperado coincida, según S14-A-09 (§5). V1 no crea evento de cambio ni
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

## 11. Matriz de aceptación · plan original y verificación S14-A

Usar exclusivamente códigos y configuración sintéticos, sin seeds oficiales.
Developer/Gamer son etiquetas ilustrativas del escenario, no fixtures de producción.

| Grupo | Comprobaciones necesarias |
| --- | --- |
| Primera activación | Developer → Gamer con nuevo progreso Gamer, XP cero y estado funcional sin rango; selección/progreso atómicos. |
| Reutilización | Gamer → Developer conserva fila y XP originales; alternar las cinco conserva progresos independientes y rangos confirmados cuando exista su persistencia. |
| Repetición | Esperado correcto y objetivo activo: sin escrituras ni reevaluación de configuración/etapas, conservando validación estructural; esperado incorrecto: rechazo incluso con objetivo activo. |
| Validación | Código inexistente; perfil/stats/progreso/catálogo incoherentes; referencias/propietarios inválidos; etapa anterior o incoherente; estado activo esperado incorrecto. |
| Concurrencia | Dos conexiones SQLite file-backed, objetivos distintos, BEGIN IMMEDIATE antes de lectura, estado esperado serializado; sin sobrescrituras, huérfanos o duplicados; timeout y retry. |
| Rollback | Fallo al crear progreso o actualizar perfil revierte ambos cambios; errores de BD con causa preservada. |
| Regresión S11-A | Múltiples progresos coherentes admitidos con integridad validada; repetición de activa sin escrituras/configuración, XP conservada; otro código en conflicto y primera selección intacta; estados inconsistentes rechazados. |
| Historia limitada | A → B → A evidencia el límite de detección de solicitudes antiguas; no simular replay histórico completo. |
| Sin efectos ajenos | XP histórica, nivel, etapa, seis stats, puntos y recompensas intactos; sin transferencias, XP de dominio concedida, rangos nuevos ni efectos Rewards. |

La matriz fue registrada como plan documental. Los casos del servicio y concurrencia
se verifican ahora mediante los módulos S14-A; la conservación física de rangos
continúa fuera de alcance porque S13-A2 sigue pendiente.

## 12. API implementada en PR, pendiente de integración

`switch_active_specialization(profile, target_code, expected_active_code)` en
[specialization_switch_service.py](../../apps/ecomotor/specialization_switch_service.py).
Reutiliza validaciones internas de S11-A; no llama a select_initial_specialization
para cambiar ni inicializa perfiles. No consulta LevelThreshold o User ni valida
los seis valores iniciales S2-A para evaluar Actual; solo configuración de etapas.

Resultado frozen `SpecializationSwitchResult`: `profile_id`, `specialization_id`,
`specialization_code`, `progress_id` y `kind`, enum `SpecializationSwitchKind`:

- `FIRST_ACTIVATION`: progreso nuevo en cero y código activo actualizado.
- `REACTIVATION`: fila destino anterior reutilizada, conservando XP e identidad.
- `UNCHANGED`: mismo objetivo activo y esperado correcto, sin escrituras.

No existe evento ni campo de rango, `replayed` o garantía histórica completa.
Con transacción exterior del consumidor, su rollback también puede revertir el
resultado del bloque interno; no se afirma un commit independiente.

Errores reutilizados y exportados desde el módulo S14-A:

| Excepción | Semántica |
| --- | --- |
| InvalidSpecializationProfileError | Entrada no persistida/inválida o perfil desaparecido. |
| InvalidSpecializationCodeError | Código objetivo/esperado estructuralmente inválido o destino inexistente. |
| InvalidSpecializationConfigurationError | Configuración/catálogo de etapas ausente o inválido para cambio efectivo. |
| IneligibleSpecializationStageError | Cambio efectivo antes de Actual. |
| InconsistentSpecializationStateError | Sin selección previa, perfil/stats/progresos inválidos o etapa incompatible con XP en cambio efectivo. |
| StaleSpecializationStateError | Nueva excepción: esperado distinto de la activa persistida, incluso con objetivo ya activo. |
| SpecializationDatabaseError | Error real de BD, causa preservada y rollback; sin retry automático. |

Se validan todos los progresos antes de comprobar el esperado y de resolver
repetición. El cambio crea/reutiliza destino y actualiza solo active_specialization_code
dentro de atomic usando el alias del perfil. Idempotencia por estado, sin recompensas,
transferencias, XP nueva o llamada al evaluador de rangos. S12-A-02 y F2-A intactos.

## 13. Verificación ejecutada en la rama de implementación

- Ejecución conjunta test_specialization_service, test_specialization_concurrency,
  test_specialization_switch_service y test_specialization_switch_concurrency:
  **83 tests correctos**, cero fallos/errores (40 + 4 + 35 + 4).
- Suite Django completa: **697 tests correctos**, cero fallos y cero errores.
- Cuatro tests S14-A con SQLite temporal file-backed y conexiones independientes:
  objetivos iguales/distintos con estado esperado inicial común, BEGIN IMMEDIATE
  antes de lecturas, invisibilidad sin commit y rollback, timeout real de 5 s y
  retry explícito en nueva transacción. La repetición posterior usa el esperado
  actualizado; no se convierte una solicitud obsoleta en éxito.
- Fallos de creación y actualización, incluidos fallos tras escritura, revierten
  progreso nuevo y código activo; errores preservan causa original.
- check sin incidencias; makemigrations --check --dry-run sin cambios;
  git diff --check correcto. Sin modificaciones de modelos, migraciones, SQLite
  locales o archivos de demo. Configuración y códigos exclusivamente sintéticos.
