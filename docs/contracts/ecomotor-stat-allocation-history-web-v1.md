# S9-A · Historial web personal de asignaciones V1

Decisión interna de Parte A aprobada por Jaime; implementación sobre la baseline
`b1b25cd8d67f45ede8de6b6642cb2eae29b6c1e8`, posterior a S8-A (PR #40) y UI-A
(PR #41). No es un requisito literal nuevo de DAR3 ni una ratificación de Core.

## Consulta local

`list_stat_allocation_history(profile, *, limit=50, before_id=None)` recibe una
instancia persistida y existente de UserProfileEcomotor y utiliza su alias de BD.
Recarga perfil y CharacterStats y valida su estructura, sin exigir configuración,
elegibilidad Actual ni concordancia con los catálogos vigentes. Un perfil parcial
o estructuralmente inválido se rechaza, sin reparación ni inicialización.

Filtra exclusivamente por su propietario y ordena por PK descendente. `limit`
es un entero entre 1 y 100; `before_id`, un entero positivo representable como
BigAutoField, exclusivo (`pk < before_id`). Se excluyen booleanos. Consulta
`limit + 1` registros: `has_more` indica si quedan filas; `next_before_id` es el
ID de la última entrada entregada únicamente cuando hay más. No hay offset.
Los límites son técnicos, no cantidades funcionales de DAR3.

Devuelve las dataclasses frozen `StatAllocationHistoryPage` y
`StatAllocationHistoryEntry`, con entradas en tupla. Cada entrada conserva `id`,
`attribute`, `points_spent`, `increase_applied`, `available_points_before`,
`available_points_after`, `attribute_before`, `attribute_after`,
`stage_code_at_allocation` y `created_at`. `attribute_label` presenta uno de ATK,
DEF, LOG, SPE, VEL o INT. No devuelve `operation_key` ni identidad del propietario.

Valida tipos enteros estrictos, rangos de los campos Django/backend, cantidades
positivas, atributo permitido, propietario, fecha datetime y código histórico de
1–32 caracteres. Exige incremento = gasto, saldo anterior = saldo posterior +
gasto y atributo posterior = anterior + incremento. También valida la fila extra
de paginación antes de anunciar un cursor. No utiliza conversiones de `full_clean`.
No compara eventos sucesivos entre sí ni con el saldo o atributos actuales.
La coherencia aritmética no demuestra autorización histórica.

## Semántica histórica y seguridad

S7-A es el único productor de asignaciones: replay conserva una única entrada.
La consulta muestra snapshots persistidos, incluidos atributos con signo. No
reconstruye niveles, puntos o etapas a partir de catálogos actuales. El código
de etapa se identifica como histórico persistido, sin buscar su nombre actual.

`allocation_history_view` exige login Django y GET/HEAD. La ruta local
`allocation-history/`, nombre `ecomotor:allocation-history`, resuelve el perfil
exclusivamente con `request.user`; ignora identificadores ajenos del navegador.
No se modifica `config/urls.py`: el montaje global sigue pendiente de Core.

La web fija diez entradas por página. El único cursor admitido es una
representación decimal ASCII positiva, de longitud acotada y dentro del rango
BigAutoField. Valores vacíos, duplicados (incluso iguales), exponentes, signos,
fracciones y valores desmesurados se rechazan antes de convertirlos.

El template extiende UI-A, conserva autoescapado, navegación con `aria-current`,
estado vacío, enlace a asignación, cursor de página anterior y vuelta al inicio.
No muestra claves idempotentes ni propietarios. No hay búsquedas, filtros,
exportaciones ni historial global.

## Errores

Se reutilizan únicamente las excepciones públicas de S4-A con igual semántica:

| Excepción / situación | HTTP |
| --- | --- |
| Anónimo | 302 al LOGIN_URL configurado, con next |
| InvalidQueryProfileError / perfil ausente | 404 |
| InvalidHistoryParametersError | 400 |
| InconsistentQueryStateError | 409 |
| ProgressQueryDatabaseError / error operativo de BD | 503 |
| Método distinto de GET/HEAD | 405 |
| Consulta válida | 200; HEAD sin cuerpo |

Los errores HTTP tienen mensajes genéricos sin datos recibidos, SQL ni trazas.
El servicio preserva la causa de DatabaseError. Errores de programación no se
convierten silenciosamente en errores de negocio o páginas válidas.

## Garantías y límites

Solo SELECT: no escrituras, bloqueos, transacciones de escritura, reparaciones,
S2-A, S3 ni S7-A durante consultas. No se promete un snapshot transaccional único
entre las lecturas; escrituras concurrentes pueden confirmarse entre ellas. La
paginación por PK evita desplazar registros por nuevas inserciones superiores.
No se introduce esquema ni migraciones. S4-A, S7-A y S8-A mantienen sus contratos.

Tests con fixtures ficticios cubren snapshots S7-A/replay, páginas, aislamiento,
alias SQLite temporal, estados inválidos, SQL de lectura, HTTP, autoescapado y
ausencia de claves en HTML. Conservación CASCADE/legacy, User/auth y montaje
global siguen pendientes de Core; S9-A no resuelve el CRUD completo de PR07.
Rewards v0 continúa candidato global y F2-A bloqueada para persistencia.
