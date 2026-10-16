# S5-A · Vista web personal de progreso V1

Estado: decisión interna aprobada por Jaime/Parte A. No es un nuevo requisito
oficial de DAR3 ni aprobación de integración global por Óscar/Core.

## Contrato local

`progress_view(request)` ofrece una página personal de lectura con autenticación
estándar Django (`login_required`) y métodos GET/HEAD (`require_safe`). Solo
`request.user` determina el propietario mediante `UserProfileEcomotor.user`.
Los parámetros GET/POST y los IDs conocidos por el navegador nunca eligen perfil.
No crea perfiles, inicializa personajes ni concede XP.

`apps.ecomotor.urls` declara namespace `ecomotor` y ruta local `progress/`, nombre
`progress`, reversible como `ecomotor:progress`. No se monta en config/urls.py:
el include global, login definitivo y home corresponden a coordinación con Core.
Los tests montan el include bajo un prefijo temporal en una URLconf del propio
módulo de pruebas, mediante override_settings, sin rutas globales nuevas.

## HTTP y errores

| Situación | Respuesta |
| --- | --- |
| Usuario autenticado, perfil válido | 200, plantilla ecomotor/progress.html |
| Anónimo | Redirección estándar a LOGIN_URL con next; el destino puede no existir aún |
| Perfil ausente o desaparecido durante S4-A | 404 genérico |
| Estado parcial/inconsistente detectado por S4-A | 409, texto genérico |
| Fallo real de BD en búsqueda o S4-A | 503, texto genérico |
| Método no seguro de usuario autenticado | 405 con Allow: GET, HEAD |

409/503 son convenciones técnicas internas V1. No se exponen excepciones,
trazas ni identificadores ajenos; no se capturan errores arbitrarios de programación.
La autenticación precede al control de métodos: anónimos reciben primero login.

## Datos y presentación

Reutiliza exclusivamente `get_progress_overview(profile)` y
`list_progress_history(profile, limit=10)` de [S4-A](ecomotor-progress-queries-v1.md).
El resumen muestra XP histórica, nivel y código actual de etapa. Estadísticas base
ATK, DEF, LOG, SPE, VEL, INT y puntos disponibles, sin estadísticas efectivas.

Objetivos independientes: CALCULABLE muestra identidad, umbral y XP restante;
COMPLETED indica último elemento del catálogo actualmente configurado, sin
declarar un final definitivo; UNAVAILABLE muestra mensaje comprensible sin
diagnóstico interno ni cifras inventadas. La configuración ausente no oculta
datos básicos ni el siguiente nivel válido. No se recalcula progresión en la vista.

Historial: hasta diez concesiones, orden descendente por ID de XPEvent, con fecha,
amount y snapshots xp_before/xp_after. Las evoluciones conservan el orden de S4-A
y muestran únicamente stage_id y xp_event_id persistidos. No se reconstruyen
niveles, puntos, saldos ni nombres/códigos/ordinales históricos de etapas. Hay estado
vacío y aviso de límite, sin paginación web ni cursor expuesto en esta V1.

Plantilla autónoma, semántica y accesible, sin base global, JS, Bootstrap ni assets
ajenos. Autoescapado Django activo, sin safe ni HTML persistido sin escapar.

## Garantías y límites

Solo lecturas; no save/create/update/delete, S2-A, S3, reparaciones ni signals.
Se conserva la limitación S4-A: no snapshot transaccional único entre lecturas
concurrentes. Sin bloqueos de escritura añadidos. Tests HTTP reales verifican
identidad, códigos HTTP, renderizado, ausencia de escrituras SQL y conservación
de registros. Fixtures ficticios no son configuración de producción.

Pendientes: aprovisionamiento y autenticación global Core, montaje/home/base
compartida, CRUD PR07, configuración oficial, conservación legacy, puntos y
especializaciones, Rewards, inventario/avatar, economía y Museo global.
