# A3.4 · Frontera de clasificación con Core/P5 · Propuesta de consulta v1

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
