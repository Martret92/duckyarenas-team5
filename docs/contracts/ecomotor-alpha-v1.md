# ALFA-A-DOC-01 · Primera alfa navegable de Ecomotor V1

## 1. Estado, autoridad y objetivo

ALFA-A-ARQ-01 está **aprobada internamente por Equipo 5 en 02C-2**: preparar
para Óscar una primera alfa básica, funcional y navegable de Ecomotor V1.
DAR3 conserva autoridad funcional. Esta aprobación no es ratificación de Óscar
ni de Core sobre el montaje, login o navegación global.

Esta PR, ALFA-A-DOC-01, solo registra arquitectura y contrato. La implementación
está **pendiente de ALFA-A-01**, tras revisión y fusión documental. Tampoco existe
todavía `apps/ecomotor/alpha_urls.py`. El README útil y actualizado se preparará
en ALFA-A-01; no se modifica en este incremento.

## 2. Baseline inspeccionada y reutilización

Referencia comprobada: develop `e7277aba6ca552344dccbac6480d1dc92119367c`.
En [views.py](../../apps/ecomotor/views.py) existen progress_view,
xp_history_view y allocation_history_view, protegidas por login_required y
require_safe. Reutilizan get_progress_overview y list_progress_history de
[S4-A](ecomotor-progress-queries-v1.md), y list_stat_allocation_history de
[S9-A](ecomotor-stat-allocation-history-web-v1.md).

El [URLconf V1 completo](../../apps/ecomotor/urls.py) contiene esas tres rutas y
allocate_points_view (GET/POST). [config/urls.py](../../config/urls.py) solo monta
administración: Ecomotor no está integrado globalmente. Las plantillas base.html,
progress.html y allocation_history.html enlazan a ecomotor:allocate-points,
incluido el estado vacío de asignaciones. No basta con retirar una ruta para
obtener una alfa navegable: quedarían reversos sin destino.

La alfa reutilizará las vistas y servicios de lectura existentes. No sustituye
S1, S2-A, S3, S4-A, S7-A, S8-A, S9-A o S10-A ni reescribe sus contratos.

## 3. Tres páginas y rutas internas propuestas

El URLconf autónomo aprobado es `apps.ecomotor.alpha_urls`, con **exactamente
tres páginas**. No incluye asignación, login propio, administración, demos o
endpoints de concesión. No se añade una cuarta página de inicio/redirección.

La siguiente concreción técnica conserva los nombres locales V1 para revisión
en ALFA-A-01; no fija el prefijo externo ni un acuerdo de namespace global Core:

| Página | Ruta relativa propuesta | Vista reutilizada | Nombre reversible propuesto |
| --- | --- | --- | --- |
| Progreso | `progress/` | progress_view | `ecomotor:progress` |
| XP y evolución | `xp-history/` | xp_history_view | `ecomotor:xp-history` |
| Asignaciones históricas | `allocation-history/` | allocation_history_view | `ecomotor:allocation-history` |

Se propone app_name/namespace local ecomotor, como en V1. El prefijo anterior a
estas rutas lo decide Core; no se confirma aquí `/ecomotor/` ni otra URL pública.
La entrada de menú debe resolver progreso por nombre, sin depender de una raíz
adicional. Si Core necesita montar simultáneamente alfa y V1 completa, deberá
coordinar namespaces de instancia inequívocos y sus reversos; no montar dos
instancias ambiguas bajo el mismo namespace ni elegir una por orden accidental.

## 4. Identidad, lectura y datos mostrados

Solo request.user autenticado determina el perfil mediante
UserProfileEcomotor.objects.get(user=request.user). IDs, username o destinatarios
en URL/GET/POST no conceden acceso ni cambian de propietario. No hay selección
de perfiles ajenos, login alternativo, usuarios sintéticos o permisos inventados.
login_required usa LOGIN_URL y next de Django; Core debe proporcionar un destino
real compatible, pues una redirección por sí sola no demuestra login operativo.

- Progreso: XP histórica, nivel, etapa y estadísticas base V1 persistidas, saldo
  disponible y próximos objetivos; mantiene CALCULABLE, COMPLETED y UNAVAILABLE
  según [S5-A](ecomotor-progress-web-v1.md), con diez concesiones recientes.
- XP/evolución: snapshots XP y referencias causales persistidas, diez entradas
  por página, sin reconstruir niveles o nombres históricos desde catálogos
  actuales; mantiene [S10-A](ecomotor-xp-history-web-v1.md).
- Asignaciones: consulta de StatAllocationEvent existente, snapshots de gasto,
  atributo/saldo antes y después y código histórico de etapa; no permite gastar.

Los dos historiales conservan before_id opcional, único, decimal ASCII positivo
y representable, y paginación por PK descendente. Los límites son técnicos, no
valores funcionales oficiales. Otros parámetros no se convierten en autoridad;
no se promete un nuevo rechazo general de parámetros que V1 actualmente ignora.

Se conservan las etiquetas y semántica V1, incluido SPE y log_stat. La alfa no
los reinterpreta como CUACK ni implanta el modelo objetivo. Los estados vacíos
no generan eventos ficticios. UNAVAILABLE no se sustituye por umbrales inventados.

No se invocan inicialización, concesión XP, asignación, reparación o Rewards.
No se crean perfiles ni se cambian estadísticas o eventos mediante estas páginas.
La infraestructura de sesión/autenticación sigue bajo Core; «solo lectura» se
refiere a las operaciones de negocio Ecomotor, sin prometer ausencia de toda
escritura que pueda realizar el middleware global. Tampoco se añade IMMEDIATE,
bloqueo o snapshot transaccional conjunto: las lecturas/páginas V1 pueden observar
estados confirmados en momentos distintos bajo concurrencia.

## 5. Navegación alfa y conservación de V1 completa

ALFA-A-01 deberá adaptar todos los enlaces de navegación, cabecera y estados
vacíos que dependen de asignación, antes de renderizar con el URLconf reducido.
La selección del modo/variante será exclusivamente del servidor, no un flag
GET/POST del navegador. El mecanismo exacto (contexto o variante de plantilla)
se concretará en esa PR sin duplicar reglas de consulta.

En modo alfa no se evalúa el reverso ecomotor:allocate-points ni se muestran
botones/formularios de asignación, enlaces muertos o accesos a demos. Permanecen
las tres páginas y sus cursores, navegación activa, escape HTML y presentación
accesible. No basta ocultar enlaces con CSS o capturar NoReverseMatch.

La V1 completa conserva su URLconf de cuatro páginas, formulario GET/POST,
CSRF, navegación y servicio S7-A. Excluir asignación de la alfa no elimina la
funcionalidad V1 ni demuestra revocación global si Core montase otro escritor.
La alfa no monta allocate-points y los POST a sus tres páginas no asignan puntos.

## 6. Métodos y errores conservados

| Situación | Comportamiento de las vistas de lectura |
| --- | --- |
| GET autenticado válido | 200 y página propia |
| HEAD autenticado válido | 200 sin cuerpo |
| Anónimo | Redirección Django al LOGIN_URL configurado, con next |
| Perfil ausente o desaparecido | 404 genérico, sin inicialización |
| Cursor inválido en historial | 400, sin conversiones permisivas |
| Estado parcial o incoherencia histórica detectada | 409 genérico, sin reparación |
| Fallo real de BD/consulta | 503 genérico, sin éxito ficticio |
| Método distinto de GET/HEAD, tras autenticación y middleware | 405, Allow: GET, HEAD |
| Ruta de asignación bajo el montaje alfa | Sin patrón; 404 en un montaje sin otra coincidencia global |

La autenticación precede al decorador de métodos; un anónimo puede recibir login
antes que 405. El middleware global, por ejemplo CSRF, puede rechazar antes una
petición no segura. No se debilitan esas protecciones para imponer un código.
No se exponen SQL, trazas, claves idempotentes, datos ajenos o detalles internos;
los errores de programación no se disfrazan de resultados válidos.

## 7. Montaje y ejecución orientativos para Core

Esto es un procedimiento propuesto, **no una modificación de config/urls.py ni
un contrato externo ratificado**. URLconf autónomo no significa entorno con
autenticación o servidor independiente ya disponible.

1. Tras integrar ALFA-A-01, Core verifica dependencias existentes: apps V1,
   sesiones/autenticación Django, middleware, templates y assets Ecomotor.
2. Core acuerda prefijo definitivo, namespace de instancia, LOGIN_URL real con
   retorno next y entrada de menú global. Incluye apps.ecomotor.alpha_urls en
   su URLconf propietario; Equipo 5 no modifica Core/User/auth para hacerlo.
3. Se utiliza un usuario autenticado y un perfil V1/CharacterStats ya preparados
   por el proceso autorizado. La alfa no los aprovisiona ni instala configuración
   ficticia. Faltas de configuración admitidas por S4-A se muestran como tales.
4. En el entorno acordado se comprueba Django check, arranque normal del proyecto,
   acceso al reverso de progreso, navegación e historiales del usuario propio.
   El comando runserver existente puede utilizarse ligado a 127.0.0.1 para revisión
   local; la URL exacta depende del montaje acordado, no se anuncia una ruta nueva
   funcional bajo los settings actuales.
5. La preparación de datos/migraciones requiere el procedimiento de respaldo y
   autorización del entorno correspondiente; esta documentación no ejecuta seeds,
   migrate ni cambios sobre SQLite personales. ALFA-A-01 actualizará el README
   con instrucciones verificadas y distinguirá montaje de prueba y montaje Core.

## 8. Plan de validación para ALFA-A-01

Estos son tests **pendientes**, no ejecuciones de esta PR documental:

- URLconf con exactamente tres patrones; resolve/reverse bajo prefijo de prueba;
  ausencia de asignación y de montaje nuevo en config.urls.
- GET/HEAD de las tres páginas, login configurable con next, perfil inexistente,
  datos parciales, corrupción causal y errores BD con códigos/mensajes seguros.
- Aislamiento entre dos usuarios incluso con IDs ajenos, cursor válido/inválido/
  duplicado, páginas vacías y múltiples páginas sin reconstruir snapshots.
- Navegación alfa completa sin NoReverseMatch, enlaces/formularios de asignación
  ausentes en los tres templates y sus estados vacíos; escape HTML y accesibilidad.
- POST y demás métodos rechazados sin efectos; consultas repetidas sin escrituras
  de negocio ni llamadas a S2/S3/S7, XP/estadísticas/historiales conservados.
- Regresión del montaje V1 completo: sus cuatro rutas, navegación y asignación
  GET/POST con CSRF siguen funcionando. No adaptar tests antiguos para ocultar
  roturas causadas por el modo alfa.
- Reutilizar test_progress_views.py, test_xp_history_views.py,
  test_stat_allocation_history_views.py, test_progress_queries.py,
  test_stat_allocation_queries.py y regresiones S3/S7/S8. Completar checks,
  migraciones sin cambios, suite habitual y regresión de las demos independientes
  según el alcance funcional final. Solo bases de tests aisladas.

## 9. Límites y dependencias abiertas

S3 V1 permanece como único escritor XP activo; esta alfa no es otro escritor.
No activa catálogos/progresión objetivo, A2/A4, selección de Duckies, Bank o Shop.
No fija bases, presupuestos, umbrales ni otras cifras oficiales.

[A3.5](ecomotor-classification-core-boundary-v1.md), USE-01B y TRACE-01B mantienen
sus acuerdos de identidad/permisos, ciclo de vida, conservación, autorización y
procedencia productiva pendientes; leer V1 no los cierra ni migra perfiles.
[Rewards F2-A](rewards-v0.md) productivo sigue fuera de alcance.
La [demo persistente Rewards–Bank](ecomotor-target-demo-rewards-bank-v1.md), su
app auxiliar, settings, sesiones y SQLite aislada permanecen separados: sus datos
sintéticos o éxito técnico no autorizan operaciones reales ni alimentan esta alfa.

Quedan por acordar con Core prefijo/namespace, login/retorno, menú global y montaje
efectivo, además del aprovisionamiento autorizado del perfil V1. No existe aún
evidencia de navegación global funcional con Core ni aceptación externa de Óscar.
