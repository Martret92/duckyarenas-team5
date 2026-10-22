# A3-TARGET-PERSIST-DEMO-01 · Paso 2: XP y evoluciones sintéticas guardadas

Decisión **interna de Equipo 5 / 02C-2 del 22/10/2026**, implementada para revisión
en PR. DAR3 mantiene autoridad funcional. Esto no es el escritor A2 productivo,
una aprobación de valores de Óscar ni una integración de usuarios Core.

## Entorno y separación

La app `apps.ecomotor_target_demo` solo se instala mediante
`apps.ecomotor.target_persistent_demo_settings`. URLconf independiente, sin admin,
Core o V1, y SQLite exclusiva `instance/target_persistent_demo.sqlite3`.
La [demo #94](ecomotor-target-demo-v1.md) conserva código, datos y configuración.

Backend local derivado del SQLite de Django 5.2: IMMEDIATE, timeout=5, sin BEGIN
manual. Comprueba alias/NAME/OPTIONS, componentes lexicales de la ruta antes de
resolverlos, ausencia de symlinks/junctions y enlaces duros (`st_nlink`/`samefile`)
frente a db.sqlite3, la demo #94 y la base normal configurada. Comprueba la conexión
efectiva con `PRAGMA database_list` y conserva identidad física de archivo durante
la vida de la conexión para rechazar sustituciones detectables.

Las aperturas normales usan URI `mode=rw`: seed, servicios, vistas y sesiones no
recrean archivos ausentes, tampoco si desaparecen justo antes del open nativo.
La orden local `migrate`, registrada solo al instalar esta app, es la única que
habilita temporalmente la creación (`mode=rwc`) después de comprobar aislamiento.
Su frontera incluye los checks de BD que Django ejecuta antes de `handle()`.
No cambia los comandos/settings normales. No crea automáticamente `instance/`.

Esto protege operaciones ordinarias de esta demo, no un administrador que modifica
el esquema, código, clave de desarrollo o archivos concurrentemente. No es un
servicio público: ligar explícitamente a `127.0.0.1`, conservar los datos ficticios
y no utilizarlo con usuarios o bases reales.

## Catálogo y dos fases de preparación

Identidad `synthetic-persistent-target-demo`, versión `persist-demo-2026-10-22-v1`.
Códigos `persist-demo-epoch-1` … `persist-demo-epoch-7`; nombres Prehistórico,
Griego, Romano, Medieval, Renacentista, Revolución Industrial y Siglo XX.
Nueve niveles con XP **ficticia**: 0, 100, 200, 300, 400, 500, 600, 700, 900.
Nada de ello acredita configuración oficial.

`seed_persistent_target_demo`:

1. Bajo atomic IMMEDIATE instala o comprueba exactamente las filas sintéticas;
   rechaza diferencias y versiones adicionales, sin reparación. Valida el catálogo
   completo con `validate_target_catalog_version` / A1.1 y confirma la preparación.
2. Fuera de esa transacción llama a `freeze_target_catalog_version`, que exige su
   propia transacción exterior. Finalmente comprueba contenido y fecha congelada.

**No hay atomicidad entre esas fases.** Si falla FREEZE-01 después de confirmar la
instalación, queda un catálogo preparatorio válido: la creación de partidas y las
nuevas concesiones están bloqueadas. Corregir el fallo y repetir el mismo seed.
Si ya está congelado y es exacto, revalida sin duplicar filas ni cambiar fecha.
Los nueve triggers y la protección pertenecen a ecomotor.0007 y no se modifican.
Congelado no significa publicado, autorizado funcionalmente ni aprobado por Óscar.

## Diseño físico de la demo

Migración **ecomotor_target_demo.0001_initial**, dependiente de
**ecomotor.0007_target_catalog_freeze** (que depende de 0006). Solo tablas y
constraints; sin RunPython, datos precargados, usuarios ni cambios V1.

| Modelo | Datos y restricciones locales |
| --- | --- |
| DemoTargetProgress | BigAutoField; hash de secreto de sesión (CharField 64); FK a TargetCatalogVersion y época actual; XP PositiveBigIntegerField 0…2⁶³−1; nivel PositiveIntegerField 1…2³¹−1; fecha de creación. |
| DemoTargetXPEvent | BigAutoField; FKs a progreso, catálogo exacto y épocas antes/después; operation_key CharField 32; importe positivo, XP antes/después y niveles; cruces completos en JSON; fecha. Unicidad (progress, operation_key), clave no vacía, checks de rango, suma exacta e incremento/no retroceso de nivel. |
| DemoTargetEvolutionEvent | BigAutoField; FKs a progreso, XPEvent causante, época exacta y catálogo; ordinal histórico 1…7; fecha. Unicidades (progress, epoch) y (progress, ordinal). |

Todas las FKs usan `PROTECT` como decisión **local de demo**, preservando historial
al iniciar otra partida. El ORM aplica PROTECT y SQLite sus FKs; la igualdad entre
progreso/causa/época/catálogo se comprueba en el servicio, no mediante un check SQL
entre tablas. Índices implícitos de FK y de unicidades, sin esquema productivo Core.
No se guarda stat_points_awarded, usuario, elección, atributos, inventario o saldo.

Los JSON conservan los cruces originales para replay; el servicio no actualiza ni
borra eventos. No se atribuye a estas tablas protección histórica contra SQL de
un administrador: solo el catálogo congelado tiene triggers de FREEZE-01.

## API y transacciones

`create_demo_progress(session_token=...)` crea XP 0/nivel 1/primera época usando
catálogo exacto, congelado y validado. La sesión aporta un secreto aleatorio creado
por el servidor; la partida guarda su SHA256, sin FK a User ni a una sesión Core.

`issue_demo_operation(progress, session_token=...)` firma identidad de partida,
hash de sesión y clave aleatoria. No tiene vencimiento propio para permitir replay
tras reinicio; siguen siendo necesarios una sesión válida y el mismo secreto del
servidor. No es un permiso productivo ni una identidad de XPEvent V1.

`grant_demo_target_xp(progress, *, amount, operation_token, session_token)`:

- Tipos exactos, importe positivo y límites SQLite comprobados antes de escribir;
  booleans/conversiones rechazados. Recarga la partida; no confía en sus caches.
- Atomic exterior IMMEDIATE antes de leer progreso/historial mutable; rechaza
  atomic/autocommit exteriores incompatibles. No select_for_update ni reintentos.
- Tras comprobar sesión/partida, busca primero `(progress, operation_key)`.
  Mismo importe recupera los hechos originales sin escrituras ni recalcular A1/A2
  o validar elegibilidad nueva del catálogo; distinto importe es conflicto.
- Para una operación nueva comprueba catálogo sintético exacto, congelado y A1.1,
  estado actual y cadena de hechos sintéticos; usa `plan_target_xp_grant` / A1.2.
- XPEvent, todos los cruces causales y actualización de progreso se confirman o
  revierten juntos. Cualquier error revierte todo, sin reparación automática.
- Resultado frozen `DemoGrantResult`: identidad de evento/partida, importe,
  TargetProgressionResult y flag replay. En replay describe el estado histórico,
  no necesariamente el actual. Historial insuficiente/contradictorio se rechaza.

Errores diferenciados: entrada, acceso de sesión, conflicto, integridad, frontera
transaccional, BD y bloqueo/timeout (`DemoBusyError`); se conserva causa técnica.
Un error no es una concesión favorable. Los fallos de seed son `CommandError`.

Caso central: 0→700 produce nivel 1→8, Prehistórico→Siglo XX, un XPEvent y seis
evoluciones (ordinales 2–7), todas con esa causa y catálogo. 700→900 produce nivel
9 y ninguna evolución nueva. Nivel 8 desbloquea doce opciones solo como dato;
no existe octava época ni concesión de puntos estadísticos.

## HTTP y sesiones locales

Solo GET y POST, CSRF real, números ASCII positivos estrictos (máximo 19 dígitos
de transporte y rango SQLite), rechazo de campos extra/duplicados, escape HTML.
No IDs de partida por GET/POST como autoridad; la sesión DB local decide la partida.
Antes de leerla o conceder, el servidor verifica dueño y referencias. Se rechazan
referencias causales ajenas sin mostrar historial ajeno.

Cookies de sesión y CSRF tienen nombres exclusivos y path
`/demo/objetivo-persistente/`; no interfieren con la demo #94. El router de sesiones
usa la misma SQLite protegida. No login ni permisos globales.

Cada formulario conserva una operación firmada estable antes de completarse;
después de éxito, POST/Redirect/GET emite una nueva. Reenviar el formulario anterior
o el botón «Repetir última operación (replay)» recupera aquella concesión. No se
convierte una repetición en premio nuevo. Un importe diferente con la misma clave
se rechaza. Iniciar otra partida no borra eventos anteriores; el navegador pasa a
la nueva, y formularios de la anterior dejan de ser utilizables en ese contexto.

## Ejecución reproducible PowerShell

Desde la raíz con dependencias del repositorio instaladas:

```powershell
New-Item -ItemType Directory -Force instance | Out-Null
py manage.py migrate --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py seed_persistent_target_demo --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py runserver 127.0.0.1:8002 --settings=apps.ecomotor.target_persistent_demo_settings
```

1. Abrir http://127.0.0.1:8002/demo/objetivo-persistente/.
2. «Iniciar personaje ficticio»: XP 0, nivel 1.
3. Conceder 700 XP sintéticas y consultar el historial: un evento XP y seis causas
   de evolución; doce opciones desbloqueadas sin ninguna selección persistente.
4. Detener Django con Ctrl+C y volver a ejecutar el mismo runserver. Conservar
   navegador/cookies y SECRET_KEY. Recargar: siguen XP 700, nivel 8 y seis eventos.
5. «Repetir última operación (replay)»: permanecen 700 XP, un XPEvent y seis
   evoluciones. Para ganancia nueva utilizar el formulario superior con otra identidad.
6. «Iniciar otra partida ficticia»: nueva partida inicial, sin borrar el historial.

Para limpiar **solo esta SQLite sintética**, detener el servidor, confirmar que
no es un enlace y, desde la raíz, ejecutar:

```powershell
Remove-Item -LiteralPath .\instance\target_persistent_demo.sqlite3
```

Repetir migrate/seed y descartar cookies de esta demo. No tocar db.sqlite3,
instance/target_demo.sqlite3 ni aplicar migraciones con settings habituales.

## Tests y límites

Nueva suite explícita (nombre `demo_tests.py` evita importar modelos no instalados
durante el descubrimiento normal):

```powershell
py manage.py test apps.ecomotor_target_demo.demo_tests --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py test
py manage.py test apps.ecomotor apps.users apps.duckies apps.ecomotor_target_demo.demo_tests --settings=apps.ecomotor.target_persistent_demo_settings
```

El runner exclusivo ejecuta dos fases y comunica cifras separadas: registro de
apps normal, SQLite estándar en memoria, URLs y cookies normales **para las pruebas
heredadas que las presuponen**; después instala el registro persistente para la
suite nueva. Las fixtures históricas que paran en 0005/0007 no contienen las
tablas nuevas, por lo que no deben adquirir sus referencias ORM inversas PROTECT.
No cambia sus tests ni expone esas rutas en el servidor real. Los tests nuevos configuran sus URLs reales y el
backend protegido sobre archivos temporales, migran explícitamente y usan
conexiones independientes para carreras, replay y timeout real de cinco segundos.
La excepción de migrate para ese arnés solo admite BD de test en memoria, nunca
un archivo arbitrario. Producción local conserva settings/cookies/rutas exclusivas.

Checks y revisión de migraciones se ejecutan aparte en ambos entornos. Resultados
exactos, omisiones, evidencia visual/reinicio y hashes protegidos se entregan en PR.

Sin escritor productivo, Core/User, Rewards, Bank/Shop, selección persistente,
estadísticas persistentes, migración legacy, USE-01B o TRACE-01B productivos.
Faltan acuerdos externos, valores oficiales y activación coordinada; esta demo
no los resuelve. [Contrato A3](ecomotor-transition-target-v1.md) permanece vigente.
