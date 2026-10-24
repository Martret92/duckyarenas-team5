# REW-MULTI-02-DOC-01 · Rewards → Duckies en el laboratorio persistente

Las secciones 1–10 registran el corte documental original de #109. El servicio
2C y sus evidencias se describen en la sección 11; el corte HTTP 2D posterior,
en la sección 12. Cada corte conserva su contexto histórico.

## 1. Estado, autoridad y alcance

Baseline inspeccionada: develop `74ba7560e1373091163a15caa878ffd56c8bdc34`,
con ALFA-A-01 / PR #108 integrada. REW-MULTI-02-ARQ-01 está cerrada internamente
en 02C-2 para documentación y futura verificación técnica. **Esta PR solo documenta;
no implementa objetos ni ejecuta la fase 2A.**

Según el traspaso del Equipo 5, Henry dio conformidad el **23/10/2026** al uso de
grant_item y al alcance del Ducky mínimo. Es información transmitida por el equipo,
no una consulta directa, acta, cita o ratificación adicional aportada por esta PR.
No autoriza cambios en Duckies ni sus contratos físicos propietarios.

DAR3 mantiene autoridad funcional. El diseño es interno y demostrativo, sin
autorización Rewards F2-A productiva, USE-01B, TRACE-01B o integración global Core.
Se amplía únicamente `apps/ecomotor/ecomotor_target_demo/`, app auxiliar existente,
en `instance/target_persistent_demo.sqlite3`, conservando settings, backend,
sesiones y Pasos 1–4/Rewards–Bank. No otro entorno, app o inventario paralelo.

Cada recompensa admite **un único efecto**: XP, DuckyCoins u objeto; NO_REWARD
es evaluación válida sin efecto. No XP + monedas + objetos combinados, ni efectos
de cantidad cero. Fallos de entrada, sesión, catálogo, integridad o BD son errores,
nunca NO_REWARD. S3 V1 permanece como único escritor XP activo fuera del laboratorio.

Las exclusiones de objetos en los cortes anteriores de
[Rewards XP](ecomotor-target-demo-rewards-xp-v1.md) y
[Rewards–Bank](ecomotor-target-demo-rewards-bank-v1.md) conservan su historia.
Esta decisión amplía un laboratorio posterior; no modifica
[Rewards v0/F1-A/F2-A](rewards-v0.md) ni el alcance productivo de otros propietarios.

## 2. Hechos verificados en el código actual

La inspección es estática; **no demuestra aún atomicidad Rewards–Duckies**.

| Componente | Hecho observado |
| --- | --- |
| [services.py de Duckies](../../apps/duckies/services.py) | Firma pública grant_item indicada abajo; usa transaction.atomic() y ORM sin using explícito, por tanto default con la configuración inspeccionada. Devuelve ItemGrant nuevo o anterior en replay. |
| [Modelos Duckies](../../apps/duckies/models.py) | ItemGrant único por (ducky, operation_key); operation_key máx. 255, reference_type máx. 50, reference_id máx. 255. Ducky tiene User OneToOne, sex (male/female) y selected_outfit nullable. Item.HINT existe. |
| Entrega actual | Cantidad int exacta positiva; valida variante y excluye HISTORICAL/SPECIALIZATION. Busca replay antes de comprobar actividad/posesión para una entrega nueva. Conflicto por distinta terna artículo/variante/cantidad o referencias: ValueError. |
| ItemGrant | Conserva ducky, item, item_level nullable, quantity, operation_key, reference_type, reference_id y created_at. No tiene request_fingerprint propio ni referencia a InventoryItem. |
| [F1-A](../../apps/ecomotor/reward_types.py) y [evaluador](../../apps/ecomotor/reward_rules.py) | ProposedEffect contiene effect_type y quantity, no un ID de artículo. Evalúa estructura/reglas y propone efectos: no entrega, autentica ni persiste premios. |
| [Modelos de demo](../../apps/ecomotor/ecomotor_target_demo/models.py) | synthetic_user OneToOne nullable/PROTECT existe desde 0004. Rewards tiene causas XP/Bank opcionales y check exclusivo de XP, monedas o NO_REWARD; no existe vínculo ItemGrant. |
| [Coordinador actual](../../apps/ecomotor/ecomotor_target_demo/reward_demo_services.py) | Solo acepta XP/DUCKYCOINS; lectores V1/V2 y causalidad ya implementados. No admite ni concede objetos. [Reglas actuales](../../apps/ecomotor/ecomotor_target_demo/reward_demo_rules.py): challenge XP700, visit sin premio, coin_challenge monedas5. |
| [Aislamiento](../../apps/ecomotor/ecomotor_target_demo/isolation.py) y [backend](../../apps/ecomotor/ecomotor_target_demo/db_backend/base.py) | default exclusivo con IMMEDIATE/timeout 5 s, apertura normal mode=rw, controles físicos y de conexión efectiva; solo migrate explícito puede crear inicialmente el archivo. |

Firma pública exacta, sin parámetro source o alias añadido:

```python
grant_item(user, item, quantity, operation_key, *, item_level=None,
           reference_type="", reference_id="")
```

El replay Duckies compara item_id, item_level_id, quantity y ambas referencias.
No concede más inventario si coinciden. La unicidad es **por Ducky**, no global.
El servicio no exige UserProfileEcomotor; initialize_ducky sí lo exige y selecciona
vestimenta, por lo que **no se utilizará ese inicializador productivo**.
max_length no equivale a enforcement automático por SQLite: el coordinador futuro
debe validar representación, longitudes y rangos antes de escribir.

Los documentos históricos de [Duckies](../erd/duckies.md),
[Bank/Shop](../erd/bank-shop.md) e [integración del Equipo 5](integracion-equipo5-v0.md)
contienen propuestas de firmas o múltiples efectos. No se reescriben ni se adoptan
como APIs actuales o aprobación productiva. Este piloto usa la firma real anterior
y un objeto único, sin cambiar esos contratos propietarios.

## 3. Identidad, autorización local y clave causal

Se conserva RewardIdentity = **(origin_code, fact_id, recipient_id)** y la huella
semantic_fingerprint independiente. Origen cerrado del servidor y destinatario
derivado de la partida (`demo-progress:<PK>`), no User/Item elegidos por HTTP.
La sesión autoriza exclusivamente su partida; no sustituye autenticación Core.
Tokens firmados vincularán partida, secreto de sesión, actividad y occurred_at
original estable. No regenerar instante/identidad al reenviar un hecho.

Se aprueba namespace Duckies **ri1:**, separado de rx1: (XP) y rb1: (Bank).
Como **concreción técnica propuesta para revisión**, codificar la clave:

```text
ri1: + SHA-256 hexadecimal completo de UTF-8(JSON canónico de
["demo-reward-item-key-v1", origin_code, fact_id, recipient_id])
```

JSON compacto, sin espacios separadores, ensure_ascii=False, allow_nan=False,
orden de array conservado y sin normalización Unicode. Se comparan también los
componentes originales: el digest no prueba autorización. Son 68 caracteres,
compatibles con ItemGrant.operation_key(255). No derivar de fingerprint, saldo,
inventario, PK de RewardEvent o artículo actual. Un solo efecto por identidad
hace innecesaria aquí una clave por múltiples artículos; no generalizar a Rewards
productivo con varios objetos.

Metadatos **propuestos**, no requisitos DAR3: reference_type =
`demo_reward_item_v1` (19 caracteres, límite 50), reference_id = clave ri1 completa
(68, límite 255), operation_key = esa misma clave. No requiere RewardEvent parcial.

Misma identidad y solicitud semántica compatible: resultado histórico original.
Misma identidad con otra huella, artículo/variante/cantidad o referencia incompatible:
conflicto sin escritura. No cambiar de clave para eludirlo. Una causa ri1 previa
sin recompensa confirmada coherente es huérfana: no adoptarla aunque grant_item
pudiera devolverla. Antes de una entrega nueva se comprobará también una clave
derivada existente en Ducky ajeno; la unicidad local de Duckies no prueba pertenencia
Rewards ni debe convertirse aquí en una constraint global de la app propietaria.

## 4. Aprovisionamiento e identidad sintéticos

Solo para recompensa de objeto **nueva y válida**, después de descartar replay y
conflictos, dentro del exterior controlado:

1. Recargar partida y verificar propiedad de sesión y catálogo/progreso vigentes.
2. Reutilizar synthetic_user si existe, con las validaciones sintéticas existentes
   de Rewards–Bank. Si no existe, crear un User reservado aleatorio, inactivo, sin
   privilegios, datos personales ni contraseña utilizable, y vincularlo a la partida.
3. Para un User nuevo crear Wallet a cero por compatibilidad del lector Bank.
   Una Wallet válida ya existente conserva saldo/historial; no se reinicia ni se
   acredita nada por entregar un objeto. User vinculado sin Wallet o relaciones
   incompatibles: error, sin reparación automática.
4. Crear o verificar Ducky mínimo del **mismo User**: sexo válido según las choices
   actuales y selected_outfit=None. La elección concreta de sexo será dato cerrado
   del fixture/servidor futuro, sin significado estético u oficial. No copiar un
   Ducky real, crear perfil V1, seleccionar vestimenta, equipar o inicializar por
   initialize_ducky.

Una partida anterior puede no tener User ni Ducky. Ausencia inicial de Ducky, sin
historia previa de objetos, permite aprovisionarlo para su primer premio válido;
ausencia de una causa/identidad exigida por historia ya confirmada es corrupción,
no una invitación a recrearla. Ducky existente incompatible, User compartido,
causa de otra partida o identidad ausente se rechazan. No se cambian relaciones
productivas CASCADE de Duckies ni políticas de conservación de Core.

GET, emisión de tokens, consulta histórica, replay, XP y NO_REWARD no crean
User/Wallet/Ducky/artículos para esta ampliación. El flujo monetario existente
conserva su aprovisionamiento autorizado, sin Ducky automático.

## 5. Un artículo de laboratorio y propuesta F1-A

Un solo artículo sintético: **HINT, consumable=True, quantity=1, item_level=None**;
debe estar activo al conceder una operación nueva. Se excluyen HISTORICAL y
SPECIALIZATION; no vestimenta, apariencia, equipamiento o efecto de juego real.
La API recibe la cantidad y objetos ORM resueltos por servidor, no IDs del cliente.
Aunque grant_item admite variantes tácticas compatibles en otros usos, este piloto
rechazará cualquier ItemLevel no None antes de entregar.

Su identidad lógica y PK se resolverán mediante catálogo/mapeo de prueba versionado
del servidor, preparado explícitamente en fixture o seed aislado de una fase
posterior. No crear artículos al consultar o aplicar HTTP ni buscar un Item
arbitrario por texto recibido. Código/nombre/imagen definitivos no se fijan aquí.

**Propuesta técnica de 2C:** actividad cerrada item_challenge con
ProposedEffect("ITEM", 1), resuelta a ese único HINT por mapeo versionado. F1-A
ya admite un tipo textual, pero el coordinador actual lo rechaza: habrá que ampliar
solo el piloto y sus verificaciones, no reward_types/reward_rules productivos.
Nombres de actividad, regla, versión de hecho/mapeo y campos V3 exactos siguen para
revisión; no son nuevos códigos oficiales. El hecho de objeto debe anclar la versión
del mapeo/identidad lógica para preservar su huella y su interpretación histórica.
Los constructores/fact_version de challenge, visit y coin_challenge conservan su
semántica V1/V2; no reinterpretar tokens o contextos anteriores.

Se validará inventario existente antes de modificarlo y el incremento representable
en el tipo/backend de InventoryItem.quantity. Cantidades incoherentes u overflow
abortan, sin corregirlas ni convertirlas en NO_REWARD. Que Duckies valide una entrega
no implica que Rewards haya autorizado el hecho.

## 6. Una única transacción, todavía por demostrar para Duckies

El nuevo flujo de objetos exige **default protegido**, porque grant_item y su
atomic/ORM usan default implícitamente. No usar persistent_fixture, otro alias,
un router que oculte otra conexión o un mock como prueba de esta integración.
XP/NO_REWARD históricos sin vinculación conservan su alias/contrato existente;
no se endurecen globalmente sus entradas para acomodar objetos.

Frontera de diseño aprobada:

1. Validar entorno, sesión, token/actividad y su instante original. Abrir exterior
   IMMEDIATE antes de leer estado mutable, recargar la partida propietaria.
2. Verificar historial e identidad Rewards existente primero. Replay compatible
   devuelve resultado verificado, sin evaluar reglas actuales ni escritores.
3. Para operación nueva validar configuración, catálogo, propuesta exclusiva,
   artículo/mapeo activo y ausencia de causas ri1 huérfanas/incompatibles.
4. Verificar mismo alias, archivo y conexión nativa Rewards–Duckies, antes de
   escribir. Aprovisionar/reutilizar User/Wallet/Ducky según sección 4.
5. Invocar solo grant_item público. Su atomic debe ser interior, sin commit propio.
6. Tras retornar, verificar tipo ItemGrant, alias, existencia real, propietario,
   artículo/variante/cantidad, clave y referencias; no confiar solo en el objeto
   devuelto. Un ItemGrant previo para un hecho nuevo no se adopta.
7. Persistir DemoTargetRewardEvent, FK causal y snapshot; releer y verificar
   consistencia completa antes del único commit exterior.
8. Cualquier fallo revierte aprovisionamiento nuevo, inventario, ItemGrant,
   RewardEvent y referencias. No XPEvent, evolución ni Transaction por un objeto.

Se conserva timeout cinco segundos y la estrategia D-19. No BEGIN manual dentro
de atomic, reintentos automáticos, I/O externo o transacciones envolventes ajenas.
select_for_update no proporciona bloqueo de fila en SQLite. El contexto existente
_check_xp_transaction exige un único exterior en sus puntos de control: durante el
savepoint Duckies no se llama al núcleo XP ni se relaja esa defensa; comprobar
la frontera antes/después de la API. No crear un escritor XP alternativo.

**Pendiente de evidencia 2A:** conexión compartida real, BEGIN IMMEDIATE, savepoint,
un solo commit, rollback conjunto, concurrencia, bloqueo/timeout y limpieza.
La evidencia Bank de PR #103/#105 no demuestra automáticamente estas propiedades
en Duckies. Si el arnés no puede demostrarlas sin cambiar backend/propietarios,
detener y devolver diagnóstico a 02C-2, sin improvisar otro alias o modelo.

## 7. Futura migración demostrativa 0005

Solo después de 2A revisada/fusionada, 2B añadirá una relación
**DemoTargetRewardEvent → duckies.ItemGrant: OneToOneField nullable,
on_delete=PROTECT**, exclusiva del laboratorio. Nombre de campo propuesto:
item_grant (concreción técnica para revisión). Evita reutilizar una entrega como
causa de dos recompensas; no crea un ItemGrant productivo alternativo.

Sucesora de ecomotor_target_demo.0004_rewards_bank_schema. Se verificará el grafo
real Duckies antes de elegir dependencia: 0001_initial define ItemGrant y
0002_rename_selected_historical_item_ducky_selected_outfit_and_more deja la forma
actual del Ducky; no se alteran esas migraciones ni se impone su nombre a una
aprobación externa. El resto de relaciones, unicidades, rangos y checks existentes
se conserva, ampliando conceptualmente demo_reward_outcome_valid:

| Estado | XP / causa XP | Monedas / causa Bank | Causa objeto |
| --- | --- | --- | --- |
| APPLIED XP | Positiva / presente | 0 / NULL | NULL |
| APPLIED monedas | 0 / NULL | Positivas / presente | NULL |
| APPLIED objeto | 0 / NULL | 0 / NULL | ItemGrant presente |
| NO_REWARD | 0 / NULL | 0 / NULL | NULL |

El servicio exige un HINT y una unidad, aunque un check de presencia no pueda
probarlo. Causalidad entre tablas se valida en servicio, no se atribuye a CHECK.
FK nueva NULL en todas las filas anteriores; sin RunPython/backfill ficticio,
reescritura de 0001–0004, snapshots V1/V2 o creación de identidades. No fake,
borrado de tablas o actualización sobre SQLite personal.

2B probará instalación limpia y copia temporal poblada anterior a 0005: mismos
registros/JSON exactos, huellas, identidades, referencias, replays y tokens V1/V2,
sin aprovisionamiento automático. Si SQLite reconstruye la tabla, conservar
índices/FKs/checks ajenos y protección del catálogo 0007. Repetir migrate sin
operaciones pendientes y revisar el estado final, sin generar 0005 en esta PR.

## 8. Snapshot V3 e historial independiente de posesión

Futura versión **demo-reward-result-v3 para recompensas de objeto**. Los datos y
lectores V1/V2 permanecen exactos: ningún JSON antiguo recibe claves nuevas.
Como propuesta mínima de serialización para revisión en 2C, V3 conserva identidad,
actividad/occurred_at, huella/versiones, reglas/decisión/motivos, efecto concedido,
catálogo/ancla XP y observación estacionaria originales, con xp_amount=0,
xp_event_id=NULL, evolution_ids vacíos, coin_amount=0 y bank=NULL.

Añade una sección causal de objeto con PK positivas exactas User/Ducky/Item/
ItemGrant; item_level_id=NULL; quantity=1; código/identidad lógica histórica,
versión del mapeo, categoría/consumible al conceder; operation_key, reference_type,
reference_id y created_at del ItemGrant. Nombres exactos del JSON son propuesta,
no un esquema implementado. No requiere un InventoryItem persistente para replay.
El resultado será inmutable y replay irá fuera del snapshot original.

El lector comprobará versión, estructura/tipos y exclusividad; terna Rewards y
huella original; mapeo histórico versionado; FK y campos reales de ItemGrant;
ItemGrant.ducky.user == progress.synthetic_user; ausencia de causas cruzadas y
coherencia de la observación XP histórica. No reevalúa reglas actuales ni reemplaza
datos por una configuración posterior. Los descriptores mutables del artículo se
conservan como snapshot del momento; no se presentan como snapshots almacenados
por ItemGrant ni se reconstruyen desde el catálogo actual. El mapeo histórico y
su vínculo semántico deben concretarse antes del lector 2C.

**El replay no llama a grant_item ni consulta o exige posesión/inventario actual.**
Consumir después puede reducir/eliminar InventoryItem, sin invalidar ItemGrant.
Recuperar una concesión antigua tampoco exige que el artículo siga activo;
una concesión nueva sí lo exige. No se añade consumo/equipamiento al flujo
Rewards; el caso postconsumo se demostrará en tests
aislados con la API propietaria y sus precondiciones reales.
La futura UI distinguirá inventario actual de entrega histórica: mostrar posesión
actual será una consulta separada, nunca una condición para recuperar el premio.

ItemGrant inexistente, de otro Ducky/User, referencias/clave cruzadas, causa ri1
huérfana, JSON manipulado o mezcla XP/Bank/objeto son errores, nunca reparación o
premio nuevo. Validar también namespace ri1 del Ducky contra recompensas coherentes;
no tratar concesiones de otros namespaces como premios propios. La futura FK
PROTECT no congela ItemGrant ni el catálogo: no se promete defensa frente a un
administrador capaz de reescribir coordinadamente datos/esquema.

## 9. Secuencia posterior y plan de pruebas pendiente

Cada fase requiere **PR separada, revisión y fusión antes de la siguiente**.
Ninguna se ejecuta o se considera probada por esta PR documental.

| Fase | Archivos previstos y alcance | Casos pendientes de esa fase |
| --- | --- | --- |
| 2A · Viabilidad | reward_duckies_fixture.py y demo_tests.py bajo el laboratorio. Subproceso/default protegido temporal, sin nuevos modelos/migración. | Ducky mínimo y HINT reales de fixture, sin perfil V1/inicializador; API grant_item real, inventario +1, replay/conflicto; mismo alias/archivo/conexión nativa, exterior IMMEDIATE/savepoint/único commit, rollback tras entrega, concurrencia independiente, timeout y reintento explícito. |
| 2B · Esquema | models.py, migrations/0005_*.py y auxiliares/tests de compatibilidad de demo. | Nullable/OneToOne/PROTECT y cuatro ramas de resultado; causas incompatibles rechazadas, copia temporal 0004→0005, filas/JSON/huellas y replays V1/V2 exactos; instalación nueva, sin backfill, esquema/triggers ajenos intactos y migrate repetido. |
| 2C · Servicio | reward_demo_services.py, reward_demo_rules.py y fixtures/tests del piloto. | Aprovisionamiento User/Wallet/Ducky perezoso y reutilización válida, artículo/mapeo, HINT1 real, activo/categoría/ItemLevel/cantidad/rangos, inventario incoherente, exclusión de efectos, rollback en distintos puntos y causas huérfanas/cruzadas. V3 estricto/manipulado, replay sin entregar ni reevaluar, replay después de consumo, sesión ajena, consulta sin escrituras y convivencia XP/Bank/V1/V2. Concurrencia, timeout y recuperación segura del coordinador completo. |
| 2D · HTTP | forms.py, views.py, plantilla/CSS necesarios y tests HTTP exclusivamente locales. | Tokens/CSRF, campos/IDs manipulados, propietario, entrega/inventario/historial propio, replay sin duplicación, consultas sin aprovisionar, errores sin falso éxito y regresión de XP/Bank/opciones. Sin integración en la interfaz compartida de Henry. |

La prueba 2A reutilizará el patrón de subproceso previo a django.setup del
[arnés existente](../../apps/ecomotor/ecomotor_target_demo/demo_tests.py): directorio
temporal propio y su instance/target_persistent_demo.sqlite3, settings y backend
protegidos intactos, default configurado antes de conectar y migrate exclusivo
para crear ese archivo. Preparación del Item solo en el fixture aislado.

Sin recursar al runner de dos fases, cambiar default del padre, desactivar routers,
MIGRATING o checked_path, ni compartir artificialmente conexiones nativas entre
hilos. Observar SQL real/lectura independiente, cerrar conexiones/procesos antes
de limpiar y propagar errores al padre. Capturar/restaurar estado y hashes de los
siete archivos protegidos. Las pruebas y runners normal/persistente se ejecutarán
y comunicarán por fase sin ocultar omisiones ni sumar dos veces padre/hijos.

## 10. Exclusiones y puerta de revisión

Sin cambios en Duckies/Bank/Shop/users, Core/auth, V1/S3 o alfa, Ecomotor objetivo,
settings/backend, migraciones anteriores, contratos físicos propietarios o
interfaz compartida de Henry. No juegos reales, efectos combinados, F2-A productivo,
USE-01B/TRACE-01B o nuevos permisos. No SQLite personal como fixture ni migrate,
seed o apertura para escritura de datos personales.

Antes de 2C siguen por concretar/revisar nombres físicos/JSON, versiones de hecho,
regla/mapeo y detalle causal, sin ampliar el objeto aprobado. La puerta inmediata
es 2A: demostrar transacción compartida sin tocar servicios propietarios; si falla,
volver a 02C-2. La conformidad transmitida de Henry no certifica esas pruebas ni
autoriza cambios ajenos. Esta PR solo comprueba texto, referencias y diff: **no
se han ejecutado tests Django ni ensayos Rewards–Duckies**.

## 11. Corte 2C · Servicio y V3 ratificados en 02C-2

Las secciones 1–10 conservan el registro documental de #109, incluida su condición
de propuestas y pruebas entonces pendientes. Después se integraron #110 (2A,
viabilidad real) y #111 (2B, esquema 0005). Sobre develop
`da35461ed5b6fe66c583f406fb7a9a7326c94f52`, **2C implementa el servicio interno**
con las concreciones ratificadas por el Equipo 5 en 02C-2. Esta aprobación no
añade ratificación externa de Henry/Core ni autorización productiva de DAR3.
HTTP 2D sigue pendiente: no cambia formularios, vistas, templates o rutas.

### 11.1. Actividad, mapeo y causa exacta

`item_challenge` existe únicamente en las actividades internas. Su hecho
`demo-fact-v3` contiene contexto `demo=REW-MULTI-02`, `mapping_version` e
`item_code`, además de `fact_version`; resultado `completed=true`. La huella
continúa siendo `rewards-semantic-v1`, con instante original firmado y estable.
La selección por actividad usa `demo-rewards-rules-v3`, regla
`demo-item-challenge-hint-v3`, con un solo `ProposedEffect("ITEM", 1)`.
Challenge/visit/coin_challenge conservan constructores, contexto, tokens y
selección de reglas V2 anteriores; propuestas ITEM sobre esas actividades siguen
rechazadas. Ninguna nueva recompensa XP/Bank se convierte en V3.

El mapeo inmutable `demo-item-map-v1` declara `demo-reward-hint-v1`, categoría
HINT, consumible, cantidad 1 y variante nula. La selección para concesiones nuevas
se distingue de esa definición histórica. El servicio no crea Items: exige el
artículo preparado explícitamente, activo, del código/categoría correctos,
consumible y sin ItemLevel. El fixture temporal es quien lo prepara. Comprueba
inventario coherente y rango entero del backend antes del incremento real.

La clave es `ri1:` seguida de SHA-256 hexadecimal completo de la representación
UTF-8 de este array, conservando orden, sin normalización Unicode:

```json
["demo-reward-item-key-v1", "origin_code", "fact_id", "recipient_id"]
```

Los tres últimos valores se sustituyen por la identidad real. La serialización
es JSON compacto (`separators=(",", ":")`, `ensure_ascii=False`,
`allow_nan=False`). No reutiliza el serializador anterior con ensure_ascii=True.
Son 68 caracteres; `operation_key=reference_id=ri1:<digest>` y
`reference_type=demo_reward_item_v1`. Identidad y fingerprint siguen separados.

### 11.2. Transacción y aprovisionamiento

El servicio exige `default` protegido para ITEM antes de escribir y conserva
`_xp_transaction(progress, session_token=...)` como único propietario del exterior
IMMEDIATE/5 s. Valida sesión, progreso, catálogo e historial; resuelve replay o
conflicto antes de reglas actuales, aprovisionamiento o entrega. Rechaza claves
ri1 previas huérfanas, ajenas o duplicadas; no las adopta.

Para un premio nuevo válido reutiliza las invariantes User/Wallet de Bank. Si
faltaba User, crea cuenta sintética inactiva, sin privilegios/datos personales y
con contraseña inutilizable, Wallet a cero y vínculo exclusivo de partida. Un
User ya vinculado sin Wallet es corrupción, no ocasión de reparación. Reutiliza
Ducky compatible del mismo User o crea el mínimo, sexo válido y selected_outfit
nulo, solo si no falta una causa histórica exigible. No requiere perfil V1 ni
initialize_ducky. Emisión de tokens, lectura y replay no aprovisionan.

Invoca grant_item público en su savepoint; después comprueba de nuevo el contexto
exterior, ItemGrant persistido, causa exacta e inventario incrementado en uno.
Guarda RewardEvent APPLIED con solo item_grant, XP/monedas cero y causas XP/Bank
nulas; relee la causalidad completa antes del commit exterior. User/Wallet/Ducky,
inventario, entrega y RewardEvent revierten conjuntamente ante fallo. No créditos,
XP/evoluciones, selección, consumo o equipamiento dentro del flujo ITEM.

### 11.3. Snapshot y resultado histórico

Solo ITEM usa `demo-reward-result-v3`. Conserva los campos comunes V2, incluidos
catálogo exacto, ancla XP y progresión estacionaria original; añade exclusivamente
esta sección `item`:

```text
mapping_version, item_code, user_id, ducky_id, item_id, item_grant_id,
item_level_id, category, consumable, quantity, operation_key,
reference_type, reference_id, created_at
```

PK enteras exactas positivas, variante NULL, HINT/true/1, versiones y referencias
anteriores; created_at ISO 8601 con microsegundos de la entrega real. El lector
reconstruye el resultado esperado desde identidad/huella, definición histórica y
filas causales, y compara el JSON completo conservadoramente: claves omitidas,
extrañas, booleanos como IDs, floats y valores incompatibles se rechazan. El
resultado y su sección de objeto son dataclasses frozen/slots, sin modelos ORM;
`replay` permanece fuera del snapshot. El resultado anterior se amplía con
`item=None` por defecto, sin añadir esa clave a JSON V1/V2.

V3 verifica regla/efecto originales sin evaluar reglas actuales; ItemGrant,
User/Ducky/Item, cantidad, variante, clave, referencias y fecha; pertenencia al
synthetic_user; exclusividad y correspondencia del namespace ri1 con recompensas
confirmadas. Distingue definición histórica de selección futura. No confía solo
en JSON ni inventa una FK ItemGrant→InventoryItem.

Replay no llama a grant_item, no consulta InventoryItem, no exige posesión actual
ni actividad actual del Item. Categoría/consumible históricos proceden del mapeo
inmutable; código/PK del artículo y causa persistida siguen comprobándose. No
reinterpreta anclas XP tras recompensas posteriores. Historial incoherente falla
sin reparar, entregar o convertir el error en NO_REWARD. V1/V2 conservan sus
lectores y JSON; el modelo histórico anterior a 0005 no consulta la nueva relación.

### 11.4. Evidencias y límites de 2C

El arnés conserva los escenarios 2A y añade grupos separados de servicio:
funcionalidad/consumo, validación, integridad, atomicidad y concurrencia. Cada
subproceso configura default antes de django.setup, mantiene el backend/routers,
audita todas las aperturas y migra/siembra únicamente su SQLite nueva temporal.
El padre comprueba configuración, conexión, registro de apps, limpieza y siete
hashes protegidos sin cambiar su default. No se usa la partida personal.

El caso de consumo concede mediante el coordinador, equipa y consume con las APIs
reales Duckies (server_accepted y game_reference sintéticos). Verifica inventario
agotado e ItemGrant conservado y repite el hecho con grant_item/evaluador
prohibidos y consultas InventoryItem rechazadas. El resultado original vuelve
sin DML ni reaparición de inventario, incluso con metadata mutable del Item
modificada. La reapertura de conexión se ensaya por separado.

También se observan SQL real BEGIN IMMEDIATE, savepoint interior y único COMMIT,
invisibilidad de entrega no confirmada para lector independiente; rollback en
aprovisionamiento, entrega, guardado Rewards y verificación final. Conexiones
independientes ensayan hechos iguales, incompatibles, distintos, ITEM/Bank e
ITEM/XP, además de timeout real de cinco segundos y reintento explícito.
No hay reintentos automáticos ni cambios de servicios propietarios.

Resultados ejecutados en Windows/Python 3.12/Django 5.2.17 para este corte:

| Ejecución | Resultado real |
| --- | --- |
| Regresión focalizada 2A/2B/Rewards XP/Bank y nuevos padres | 104 tests aprobados, 0 fallos/omisiones, 403,319 s. |
| Runner existente, fase habitual con registro normal | 1320 tests: 1318 aprobados, 2 omitidos, 0 fallos; 177,377 s. Incluye alfa/V1, objetivo, demo original y apps propietarias. |
| Mismo runner, fase persistente completa | 125 tests aprobados, 0 fallos/omisiones, 500,523 s. |
| Nuevos escenarios 2C, incluidos en la fase persistente | 5 tests padre; separadamente 19 casos hijos (5 funcionales, 4 validación, 3 integridad, 2 atomicidad, 5 concurrencia), todos aprobados. No se suman de nuevo al total del runner. |

Las dos omisiones se reprodujeron individualmente: Windows no permite crear
symlinks reales en este entorno (WinError 1314). No se omiten casos nuevos ni se
alteran tests heredados. En el desarrollo se corrigieron dos datos de pruebas
nuevas que no respetaban las estructuras públicas F1-A/A4; las ejecuciones finales
anteriores no presentan fallos.

El SQL observado en el coordinador fue BEGIN IMMEDIATE → SAVEPOINT → RELEASE
SAVEPOINT → COMMIT, una vez para cada frontera exterior. El timeout ITEM real
fue 5,5 s, seguido de recuperación explícita sin duplicación. La regresión física
0004→0005 recuperó nueve llamadas históricas, conservando JSON V1/V2 exactos,
columnas comunes, índices/FKs/checks y triggers ajenos. Ambos registros de apps
superaron los checks Django; check y makemigrations --check --dry-run también se
ejecutaron dentro del default temporal protegido, sin cambios de modelos.
Enlaces locales y git diff --check correctos; siete hashes personales idénticos.

Estas pruebas son del laboratorio y no certifican defensa frente a modificación
coordinada por un administrador de BD. La entrega histórica tampoco certifica
inventario presente. Falta HTTP 2D, incluida presentación autorizada del inventario;
no se arranca esta fase sobre una SQLite personal ni se activa F2-A productivo,
USE-01B, TRACE-01B, juegos reales o integración Core.

## 12. Corte 2D · HTTP local e inventario presente

Sobre develop `467724c1ffe8ad7c0dc115037293d256a18644a1`, con #112 integrada,
se publica el servicio 2C en la interfaz local existente. **Arquitectura ratificada
internamente por Equipo 5 en 02C-2**, según el traspaso 2D; no es autorización
productiva de Henry, Core o DAR3. Las afirmaciones anteriores sobre HTTP pendiente
describen sus respectivos cortes históricos. No cambia el algoritmo de concesión,
las reglas, el mapeo, las claves ri1 o el snapshot V3 de 2C.

### 12.1. Formulario, sesión y resultado

Se conserva `/demo/objetivo-persistente/`, nombre `persistent-demo`, vista home
y GET/POST, sin rutas adicionales. RewardDemoForm publica cuatro opciones cerradas:
challenge XP700, coin_challenge monedas5, item_challenge HINT1 y visit NO_REWARD.
Solo admite action=reward, activity, fact_token y CSRF; campos extra, duplicados
o ausentes se rechazan. Identidad, destinatario, Item, cantidad, variantes, reglas
y referencias causales siguen resolviéndose en servidor.

La sesión propietaria y el token firmado emitido por issue_reward_fact mantienen
partida, actividad e instante original. La vista llama a apply_demo_reward real;
no invoca grant_item directamente. Después del commit correcto devuelve 302/PRG
y aviso específico «APPLIED: HINT sintético entregado y registrado». Replay
comunica recuperación histórica sin otra concesión; ITEM nunca se muestra como
NO_REWARD o +0 XP. El aviso se consume al visualizarse en GET y se descarta al
procesar otro POST; los errores no presentan confirmaciones nuevas.

Se conservan replay del último hecho y por fila con los tokens históricos de la
sesión. El botón no depende del inventario actual. Reiniciar partida limpia esos
tokens/avisos del nuevo contexto sin borrar historia almacenada. No se aceptan
PK de partida, User, Wallet, Ducky o Transaction desde GET/POST como autorización.
CSRF y cookies/sesiones globales permanecen intactos.

### 12.2. Consulta de inventario sin efectos

read_demo_inventory(progress, session_token=...) abre su propia frontera protegida
_xp_transaction y comprueba pertenencia e historia antes de consultar posesión.
Devuelve DemoInventoryOverview frozen/slots, con solo item_prepared,
user_provisioned, ducky_provisioned y quantity; no expone modelos ORM ni IDs.

| Observación | Presentación |
| --- | --- |
| User ausente | Identidad no aprovisionada; quantity=NULL. |
| User válido de Bank y Wallet, sin Ducky ni causa ITEM histórica | Ducky no aprovisionado; quantity=NULL, sin crearlo. |
| Código del mapeo sin Item preparado | Artículo no preparado; quantity=NULL, sin crear artículos. |
| User/Wallet/Ducky válidos e Item registrado, sin posesión | quantity=0. |
| Posesión actual válida | quantity entera exacta positiva, dentro del rango SQLite. |

Reutiliza _wallet y _ducky sin aprovisionamiento. get_item_ownership público se
llama solo con identidad e Item resueltos y exige entonces el mismo default
protegido que Duckies utiliza implícitamente. Las observaciones sin User siguen
siendo compatibles con el alias aislado de los fixtures históricos, sin llamar
a servicios Duckies sobre otra conexión. Resolver Item usa exclusivamente el
mapeo histórico cerrado del servidor.

item_prepared informa de la existencia del código para consulta, no de autorización
para entregar: un premio nuevo sigue requiriendo todas las comprobaciones 2C,
incluida actividad/categoría/configuración actual. Consultar una entrega histórica
no exige que el Item siga activo. Historia que exige User/Ducky/ItemGrant ausentes
o incoherentes produce error de integridad, nunca un inventario vacío ni reparación.

La cantidad presente procede de get_item_ownership, no de DemoRewardResult.item.
No INSERT/UPDATE/DELETE, aprovisionamiento ni reparaciones en esta consulta.
La emisión de tokens y el motor de sesiones HTTP pueden mantener django_session;
no se confunden esas escrituras con XP, Bank, entregas o inventario.

Cada consulta de progreso, Bank, Rewards o inventario es coherente por separado.
**No se promete un snapshot transaccional global de toda la página**.

### 12.3. Historial e interfaz

El historial presenta ITEM antes de monedas, XP y NO_REWARD. Muestra HINT,
cantidad histórica 1, ItemGrant, código/mapeo y referencias, regla y versión.
La sección «Inventario HINT sintético» presenta por separado preparación,
aprovisionamiento y cantidad actual, incluida cero después del consumo. Los
campos de Django se escapan; no se imprimen secretos de sesión o rutas SQLite.

Se reutilizan los paneles, tablas y grid responsive existentes, sin cambiar CSS.
No botones de equipar, consumir, comprar, transferir o gestionar variantes.
La pantalla aclara que usa modelos Django Duckies auténticos con datos sintéticos,
sin avatar/inventario productivo ni integración Henry/Core. XP, Bank, opciones,
Gamer/Romano y redistribuciones conservan su experiencia.

### 12.4. Errores y pruebas del corte

| Caso | HTTP |
| --- | --- |
| Premio nuevo confirmado o replay válido | 302 con PRG. |
| Formulario inválido, extras/duplicados/ausencias o GET con parámetros | 400. |
| Token/sesión/partida ajenos, firma o actividad incompatible; fallo CSRF | 403. |
| Conflicto semántico o historia/identidades causales incoherentes | 409. |
| Item ausente/inactivo/incompatible para conceder, SQL o timeout | 503. |
| Método no admitido | 405. |

Se preservan los manejadores específicos, sin except Exception ni detalles SQL,
tokens, rutas privadas o trazas. Los fallos no se traducen en NO_REWARD.

El arnés Duckies añade siete grupos 2D independientes (flujo, replay, consumo y
consulta, sesiones, CSRF/entradas, errores y compatibilidad). Client real con
enforce_csrf_checks=True, sesión Django, default file-backed temporal auditado,
coordinador 2C y APIs Duckies reales. No se sustituye el coordinador por mocks.
Una inyección SQL controlada prueba el saneamiento del error de lectura; el
timeout se provoca con otra conexión real, sin reintentos automáticos.

Los grupos preservan los casos 2A/2C. Única adaptación histórica autorizada
expresamente en 01B-2: la aserción que excluía item_challenge del formulario en
2C ahora comprueba su inclusión ratificada en 2D. No se relajan validaciones de
concesión, replay, causas, rollback, concurrencia o esquema. load_tests registra
los siete padres una sola vez, sin herencia ni duplicación de casos anteriores.

La prueba concede por HTTP, equipa/consume solo dentro del fixture con las APIs
reales y verifica GET con cantidad cero, ItemGrant histórico conservado y replay
sin segunda entrega. También prueba consultas sin DML, cinco estados del DTO,
dos sesiones, reinicio de partida, parámetros de autoridad, HTML escapado, códigos
controlados, bloqueo real y recuperación explícita. Compatibilidad V1/V2 y las
otras modalidades se contrastan además mediante sus regresiones existentes.

La SQLite personal permanece sin migrar ni sembrar. No se arranca runserver contra
ella ni se utiliza como fixture. La preparación del HINT sigue siendo explícita
y exclusiva de datos sintéticos aislados: GET y POST de la vista no crean Items.
Este corte no implementa F2-A productivo, USE-01B, TRACE-01B, integración Core,
interfaz compartida de Henry, consumo HTTP o efectos combinados.

### 12.5. Resultados ejecutados en 2D

Verificación del 24/10/2026 en Windows/Python 3.12/Django 5.2.17, sobre archivos
desechables. Estos recuentos son nuevas ejecuciones, no resultados reutilizados
del corte 2C:

| Ejecución | Resultado |
| --- | --- |
| Focalizada HTTP/consulta 2D | 7 padres aprobados, 0 fallos/omisiones, 47,403 s. |
| Casos hijos 2D, contabilizados separadamente | 14 aprobados: flujo 2, replay 1, consumo/consulta 2, sesiones 1, seguridad 3, errores 4 y compatibilidad 1. |
| Runner de dos fases, registro habitual | 1320 tests: 1318 aprobados, 2 omitidos, 0 fallos; 194,213 s. |
| Mismo runner, fase persistente completa | 132 padres aprobados, 0 fallos/omisiones; 556,782 s. Incluye los 7 nuevos, sin sumar de nuevo sus hijos. |

Las dos omisiones se reprodujeron por separado: Windows deniega crear symlinks
reales (WinError 1314). No se omiten casos nuevos ni se desactivan regresiones.
El timeout HTTP ITEM observado en la suite completa fue 5,484 s; 503 saneado,
cero efectos parciales y reintento/replay explícitos sin duplicación.

Se comprobaron consumo real desde el fixture, GET con cantidad cero e historial
con cantidad entregada 1, y los formularios original/último/por fila sin entrega
adicional. SQL inesperado, corrupción y entradas ajenas no producen confirmación.
Las regresiones preservan los JSON V1/V2 y nueve replays históricos tras la
migración temporal 0004→0005. Checks Django correctos en ambas fases; check y
makemigrations --check --dry-run también dentro del default temporal protegido,
sin cambios de modelos. Enlaces locales y git diff --check correctos, siete
hashes protegidos idénticos. No se ejecutó runserver ni revisión visual de móvil
o navegador contra una SQLite personal; la validación funcional fue HTTP real
con Django Client, no una simulación del coordinador.
