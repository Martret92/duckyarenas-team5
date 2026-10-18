# S10-A · Historial web completo de XP y evoluciones V1

Incremento interno de implementación aprobado por Jaime/Parte A sobre develop
`a309e6324a54b25f84abd8bd66f2f26441ca7c4e`, que integra S9-A mediante PR #42.
Este contrato técnico local describe la adaptación HTTP implementada. No introduce
decisiones arquitectónicas, requisitos literales nuevos de DAR3 ni aprobación de Core.

## Dependencia y datos históricos

`xp_history_view(request)` utiliza exclusivamente
`list_progress_history(profile, limit=10, before_id=before_id)` de
[S4-A](ecomotor-progress-queries-v1.md), una vez por GET/HEAD válido. No necesita
get_progress_overview ni consulta evoluciones o catálogos mediante otro servicio.
S4-A conserva su implementación, alias del perfil, validaciones, agrupación causal,
resultados inmutables y paginación por PK descendente exclusiva.

La página presenta por concesión: ID de XPEvent, fecha, cantidad, xp_before y
xp_after persistidos. Sus evoluciones se muestran en el orden recibido, mediante
ID de EvolutionEvent, stage_id y xp_event_id causal. No muestra operation_key,
profile_id ni identidades de usuarios. stage_id es una referencia persistida,
no un snapshot del código, ordinal o nombre actual de EvolutionStage.
No reconstruye niveles, etapas, puntos, estadísticas, saldos o equipamiento.
El historial funciona sin configuración vigente ni catálogos actuales.

## Autenticación y ruta local

Ruta `xp-history/`, namespace `ecomotor`, nombre `ecomotor:xp-history`.
`login_required` precede a `require_safe`: solo GET/HEAD autenticados; el anónimo
usa LOGIN_URL y next de Django. El perfil se obtiene exclusivamente con
UserProfileEcomotor.objects.get(user=request.user). Parámetros profile_id,
user_id, username o recipient_id no seleccionan propietario.

No se monta en config/urls.py ni se modifica autenticación. La integración global
de rutas, login y navegación Core sigue pendiente de coordinación.

## Cursor y presentación

La web fija diez concesiones por página. `before_id` es opcional, exclusivo y
solo puede aparecer una vez, incluso si los valores duplicados son iguales.
Debe ser decimal ASCII positivo, sin signos ni espacios, y caber en el tipo
de PK de XPEvent según su backend. Se comprueban longitud y representación antes
de convertirlo; vacíos, cero, negativos, decimales, exponentes, Unicode no ASCII
y valores desmesurados se rechazan. No se cambia el contrato Python de S4-A.

`history.has_more` y `history.next_before_id` construyen el enlace «Ver concesiones
anteriores» mediante el nombre local de URL. Se ofrece «Volver al inicio del
historial» y «Mi progreso», sin offsets, números de página, JavaScript ni filtros.
El estado vacío indica que aún no hay concesiones registradas.

La plantilla xp_history.html extiende UI-A, reutiliza clases y autoescapado,
navegación activa con aria-current y disposición responsive. Mi progreso conserva
sus diez registros recientes y añade «Ver historial completo de XP».

## Respuestas y errores

| Situación | HTTP |
| --- | --- |
| GET válido | 200 |
| HEAD válido | 200 sin cuerpo |
| Anónimo | 302 hacia LOGIN_URL configurado, con next |
| Perfil ausente / InvalidQueryProfileError durante consulta | 404 |
| Cursor inválido / InvalidHistoryParametersError | 400 |
| InconsistentQueryStateError | 409 |
| ProgressQueryDatabaseError / DatabaseError | 503 |
| POST, PUT, PATCH, DELETE u OPTIONS autenticados | 405 |

Mensajes genéricos sin SQL, trazas, valores malformados ni identificadores privados.
No se capturan errores arbitrarios de programación como fallos esperados.
Las comprobaciones históricas y de causalidad pertenecen a S4-A, sin duplicación
en la vista ni reparación de datos.

## Garantías, comprobaciones y límites

Solo lecturas: sin inicialización, S3, asignación S7-A, Rewards, escrituras,
transacciones o bloqueos de escritura. No hay modelos, migraciones, dependencias,
endpoints REST ni configuración oficial nuevos. S3/S4-A/S9-A y sus contratos
permanecen intactos. Se mantiene la limitación concurrente S4-A: las consultas y
páginas pueden observar estados confirmados en distintos momentos; no hay
snapshot transaccional único ni historial congelado entre páginas.

Los tests HTTP usan fixtures ficticios y URLconf local del módulo de pruebas:
concesiones reales S3, aislamiento de usuarios, snapshots/evoluciones, cursor,
errores, autoescapado, navegación y SQL SELECT sin efectos de negocio. La página
se comprueba visualmente en escritorio y a unos 390 px, sin modificar bases locales.

Pendientes de Core: identidad/autenticación global, montaje y conservación/legacy.
S10-A no resuelve CRUD completo, Museo, economía, inventario, especializaciones o
XP de dominio. Rewards v0 continúa candidato y F2-A bloqueada para persistencia.
Cualquier cambio arquitectónico pendiente corresponde a 02B, fuera de S10-A.
