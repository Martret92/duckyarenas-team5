# A3.4 · Frontera de clasificación con Core/P5 · Propuesta de consulta v1

**Actualización A3.5 · 21/10/2026:** [§6](#6-a35--respuestas-preferidas-del-equipo-5--21102026)
registra propuestas aprobadas internamente por Equipo 5, pendientes de compatibilidad/
confirmación Core. Las cinco preguntas originales de §2 se conservan sin cambios;
no se han recibido por esta actualización respuestas externas ni autorización física.

## 1. Estado y autoridad

**Propuesta para consulta, no contrato ratificado.** Documento del Equipo 5
preparado el 20/10/2026 sobre develop `8b6b0f7`, bajo
[A3.4-ARQ-01](../decisions.md#a34--dirección-de-persistencia-de-clasificación--20102026).
No contiene respuestas atribuidas a Core/P5, Óscar o Henry ni autorizaciones
externas aprobadas. DAR3 sigue principal; decisiones técnicas internas no son
requisitos literales nuevos del profesor. No se contacta automáticamente con Core.

[Persistencia candidata](ecomotor-classification-persistence-v1.md),
[protocolo A3.3](ecomotor-profile-classification-v1.md) y
[pendientes](../pending-decisions.md#19-a34--puertas-de-persistencia-y-servicio).
La propiedad de clasificación es Equipo 5/apps.ecomotor; identidad, autenticación
y autorización global siguen bajo Core/P5. No redefinir User o sus relaciones.

## 2. Preguntas de coordinación pendientes

| Identificador | Propuesta de consulta / decisión requerida |
| --- | --- |
| CORE-A3.3-IDENTITY | ¿Qué identidad canónica representa al operador, usuario y proceso interno? ¿Cómo se conserva su atribución histórica? Acordar representación y participación canónica del operador en comparación de solicitudes originales; no equiparar autorización con identidad ni decidir FK. |
| CORE-A3.3-AUTH | ¿Quién puede clasificar inicialmente, transicionar, bloquear, recuperar y reproducir operaciones? Acordar contexto confiable, alcance por perfil/alias y permisos de procesos internos. Replay también requiere autorización; no basta conocer operation_key. |
| CORE-A3.3-LIFECYCLE | ¿Qué ocurre al eliminar User o UserProfileEcomotor y con sus políticas/eventos? Acordar relaciones y on_delete sin copiar políticas existentes o impedir decisiones de Core por inferencia. |
| CORE-A3.3-RETENTION | ¿Qué políticas de conservación se aplican a políticas, eventos, operation_key y referencias de incidencias? ¿Durante qué alcance temporal permanece la evidencia suficiente para replay e integridad? No fijar plazos ficticios. |
| CORE-A3.3-PRIVACY | ¿Cómo anonimizar y controlar acceso al historial preservando o delimitando idempotencia, atribución y comparación? Acordar tratamiento de identificadores, claves y referencias potencialmente sensibles sin normalización/pérdida silenciosa del contenido original. |

La API pura actual no incorpora operador, permisos, tiempo o política de retención.
No añadirlos a su comparación por esta propuesta. Tampoco asumir que una identidad
de proceso equivale a un User o autorizar perfiles ajenos. Logs y respuestas no
deben usarse para exponer solicitudes o referencias históricas innecesariamente.

## 3. Alternativas de conservación y eliminación

Alternativas a evaluar por relación y ciclo de vida, **sin elegir ninguna**:

| Alternativa | Consecuencias que requieren acuerdo |
| --- | --- |
| CASCADE | Puede eliminar políticas/eventos al eliminar su referencia, perdiendo trazabilidad, prueba de contenido y deduplicación. No asumir que mantener el resto del historial permite replay íntegro. Requiere política explícita antes de adoptarla. |
| PROTECT | Puede preservar referencias bloqueando eliminaciones; condiciona el ciclo de vida de User/perfil y necesidades de privacidad. No imponerla unilateralmente a Core. |
| Conservación/anonimización con identidad histórica separada | Puede desacoplar atribución histórica de identidad operativa, pero requiere diseñar vínculos, permisos, minimización y consistencia con perfil/idempotencia. No aprueba modelo adicional, FK, pseudónimo o transformación de datos. |

Anonimizar, retirar referencias o perder eventos puede impedir comparación exacta
y replay. No declarar compatibilidad si falta evidencia. Acordar consecuencias y
frontera de garantías sin fabricar datos o reconstruir desde el estado actual.
No confundir una retención decidida con consentimiento para registrar datos
personales innecesarios. Esas decisiones son externas y permanecen pendientes.

## 4. Puertas de modelos y servicio

| Decisión pendiente | Bloquea modelos/migraciones definitivos | Bloquea servicio posterior |
| --- | --- | --- |
| Ciclo de vida, retención, privacidad y on_delete (LIFECYCLE/RETENTION/PRIVACY) | Sí: condicionan relaciones, datos conservados y representación histórica. | Sí: definen qué historia se puede confirmar/recuperar y cómo acceder a ella. |
| Identidad física del operador y su atribución (IDENTITY) | Sí en cuanto condiciona campo/relación y evidencia persistente; no elegir FK provisional. | Sí para atribución confiable y comparación acorde al contrato. |
| Permisos y contexto confiable (AUTH) | No por sí solos si no exigen campos/relaciones; si lo hacen, revisar el esquema antes de aprobarlo. | Sí: sin autorización acordada no habilitar clasificación, bloqueo, recuperación o replay reales. |
| Participación canónica del operador en contenido (IDENTITY/AUTH) | Resolver antes de cerrar datos/evidencia que deba conservar el modelo. | Sí para comparación definitiva de solicitudes y replay autorizado. |
| Cobertura y protocolo de evidencia por transición | No elige por sí solo tipos/on_delete; cualquier necesidad nueva de datos debe revisarse antes del esquema definitivo. | Sí: la dirección de lector interno no establece suficiencia de evidencia. |
| Tipos, límites, colaciones, nulidad y constraints candidatos (Parte A con acuerdos pertinentes) | Sí: resolver representabilidad e integridad antes de migrar. UNIQUE(profile, after_revision) sigue propuesto. | Sí: reconstrucción exacta y errores seguros sin truncamiento o reparaciones. |

Esta separación permite avanzar en diseño, pero **no autoriza hoy modelos o
migraciones**: las puertas necesarias siguen abiertas. Las reglas puras #66 están
integradas y no sustituyen acuerdos externos. Los contratos con Henry/Duckies y
consumidores siguen necesarios para catálogo, causalidad, transición e integración.

## 5. Siguiente paso y límites

Recoger decisiones explícitas de Core/P5 sin inventar respuestas. Después revisar
su efecto en el esquema candidato y contrato de comparación; concretar cobertura
de evidencia, preparar modelos/migraciones sin backfill solo tras acuerdos,
y servicio/tests en incrementos separados. Integración, ensayos y activación global
requerirán autorización posterior; la secuencia no es calendario aprobado.

No se modifica Core/User, autenticación, A3.1/A3.2, reglas puras A3.3, S3 V1,
Duckies, Bank/Shop o Rewards. No clasificar perfiles, reparar historia o activar
XP objetivo por esta consulta. No se ejecutan tests Django en esta PR documental.

## 6. A3.5 · Respuestas preferidas del Equipo 5 · 21/10/2026

**Cada propuesta siguiente está aprobada internamente por Equipo 5 en 02C,
pendiente de compatibilidad/confirmación Core.** Registro comunicado por Jaime,
sobre develop `3f140da0f53596fff429553641ac81b5f82ce6de`. DAR3 conserva autoridad
funcional; estas direcciones técnicas no son requisitos literales de DAR3 ni
respuestas confirmadas por Óscar/Core. No se afirma nueva consulta externa.
[Registro interno](../decisions.md#a35--propuestas-internas-para-core--21102026)
y [bloqueos residuales](../pending-decisions.md#30-a35--preferencias-internas-y-acuerdos-externos-pendientes).

| Pregunta original (§2) | Respuesta preferida, aprobada internamente por Equipo 5 | Pendiente de compatibilidad/confirmación Core |
| --- | --- | --- |
| CORE-A3.3-IDENTITY | Diferenciar perfil afectado y operador ejecutor. Obtener operador de contexto confiable del servidor y preservar atribución histórica original. | Representación canónica, identidad de procesos internos y participación exacta del operador en comparación histórica. No elegir campos o FK ni modificar la API pura. |
| CORE-A3.3-AUTH | Clasificaciones iniciales, transiciones, bloqueos, recuperaciones y replays solo para administradores o procesos internos expresamente autorizados según cada operación. Conocer operation_key no autoriza replay; ser administrador tampoco sustituye la autorización exigible a esa operación. | Permisos concretos, alcance por perfil/alias e integración con autenticación Core. No habilitar operaciones reales sin acuerdos. |
| CORE-A3.3-LIFECYCLE | Evitar destrucción silenciosa de evidencia histórica necesaria por bajas/eliminaciones. Diseñar conjuntamente con Core conservación, anonimización o supresión que proceda. | Ciclo de vida y tratamiento definitivo de relaciones/evidencia. Sin aprobar CASCADE, PROTECT, SET_NULL u otro on_delete. |
| CORE-A3.3-RETENTION | No implementar limpieza automática de eventos de clasificación en primera versión; mantener evidencia suficiente mientras sea legítimamente necesaria. | Plazos y tratamiento definitivo con Core; sin plazos ficticios, conservación perpetua o impedimento a políticas de eliminación. La dirección interna no elige una retención física definitiva. |
| CORE-A3.3-PRIVACY | Acceso mínimo según identidad/autorización; no exponer claves/referencias sensibles innecesarias; proteger atribución histórica. Reconocer explícitamente si anonimización/supresión impide reconstrucción o replay exactos. | Integración con mecanismos Core, privacidad y representación histórica; sin inferir igualdad del contenido cuando falte evidencia ni fabricar historia. |

### Alcance y garantías conservadas

Las cinco preguntas de §2 siguen abiertas a Core; ahora existe una solución
preferida interna para contrastarlas, no un acuerdo compartido cerrado. §3 mantiene
alternativas sin elección y §4 conserva las puertas de modelos/migraciones y servicio.
Operador canónico, permisos, eliminación, conservación, privacidad, on_delete y
representación física requieren acuerdos antes de implementar lo condicionado.

A3.3, A3.4 y A3.6 mantienen sus garantías: identidad por perfil/operation_key,
comparación del contenido original, evento histórico primero, replay autorizado
sin mutar estado actual ni revalidar elegibilidad nueva, y confirmación conjunta
bajo D-19 para operaciones nuevas con evidencia vigente/suficiente. No se cambia
la participación del operador en comparación por inferencia. Si una supresión
hace imposible reconstruir/comparar, reconocer el límite; no prometer replay exacto.

No se aprueban modelos, migraciones, campos, FKs, backfill, clasificación real o
activación objetivo. S3 V1 sigue único escritor XP activo. Sin código, nuevos tests
Django ejecutados o cambios de Core, Henry u otros equipos. Próximo paso: contrastar
las preferencias con Core mediante coordinación autorizada; no contacto automático.

## 7. INT-A-00 · Respuestas concretas requeridas de Core · 26/10/2026

El [plan INT-A-00](ecomotor-transition-target-v1.md#13-int-a-00--plan-de-integración-progresiva--26102026),
aprobado internamente en 02C-2 el 26/10/2026, precisa qué respuesta necesitamos
recibir para cada pregunta A3.5 existente. §2 conserva las preguntas originales
y §6 las preferencias internas; **ninguna fila siguiente es una respuesta
recibida o ratificada por Core**. No se eligen unilateralmente campos, FKs,
permisos, retención ni mecanismos de autenticación.

| Pregunta existente | Respuesta concreta requerida para revisar la integración |
| --- | --- |
| CORE-A3.3-IDENTITY | Identificar la representación canónica de perfil destinatario, usuario, operador y proceso interno; especificar de qué contexto confiable se obtienen, cómo se resuelven y cómo se conserva su atribución histórica tras cambios o bajas. Confirmar qué identidad del operador forma parte de la comparación de solicitudes/replay y cómo se vincula al perfil, sin asumir que toda identidad sea un User. |
| CORE-A3.3-AUTH | Aportar la matriz de permisos para clasificación inicial, transición, bloqueo, recuperación, replay y nuevas concesiones objetivo; precisar quién autoriza cada operación, alcance por perfil/alias y cómo entrega Core el contexto verificable a Parte A. Definir qué sucede cuando el permiso se revoca, incluido replay, y qué rechazos deben devolver los consumidores. Conocer la clave no equivale a permiso. |
| CORE-A3.3-LIFECYCLE | Confirmar el comportamiento ante baja, desactivación, eliminación y eventual recreación de User/perfil: efectos sobre políticas, eventos y causas; política acordada por relación/on_delete y responsable/orden de ejecución. Indicar cómo impedir referencias rotas o reutilización de identidad que permita duplicar operaciones, sin inventar historia ni reparar automáticamente. |
| CORE-A3.3-RETENTION | Especificar qué evidencia, claves, políticas, eventos y referencias debe conservarse, durante qué plazos o condiciones legítimas y quién ejecuta su retirada. Acordar desde qué momento deja de garantizarse reconstrucción/comparación/replay exactos y cómo debe responder el servicio al faltar evidencia, sin reconstruir desde estado actual ni prometer conservación indefinida. |
| CORE-A3.3-PRIVACY | Definir quién puede consultar cada dato histórico, con qué alcance y minimización; tratamiento de identificadores, operation_key y referencias en consultas, logs y exportaciones. Precisar el procedimiento de anonimización/supresión y qué atribución o comparación se preserva legítimamente, así como los límites explícitos de replay cuando no pueda conservarse. |

La respuesta deberá poder contrastarse con §3–§4 y evidencia A3.6 antes de cerrar
el esquema y servicio condicionados. Se registrarán fuente, alcance y confirmación
de los acuerdos recibidos, sin interpretar silencio o pruebas sintéticas como
ratificación. Las puertas USE-01B/TRACE-01B y contratos de Bank, Duckies y emisores
reales siguen siendo requisitos separados; estas preguntas no los dan por cerrados.
La coordinación externa requiere autorización específica: esta PR no envía consultas.
