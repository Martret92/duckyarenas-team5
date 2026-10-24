# REW-MULTI-01 · Rewards y DuckyBank en el laboratorio persistente

## 1. Estado y autoridad

Decisión **aprobada internamente por Equipo 5 / 02C-2 el 23/10/2026**.
La Fase 1 documentó arquitectura y contrato para revisión de **01B-2**.
La Fase 2A demuestra únicamente el arnés de tests de default protegido (sección 11);
no implementa funcionalidad monetaria, modelos ni migración 0004.
La Fase 2B incorpora únicamente el esquema de la sección 6 mediante 0004 y
pruebas de compatibilidad histórica (sección 12); la concesión monetaria y V2
quedaron pendientes en ese corte. La Fase 2C implementa el servicio interno y
los snapshots V2 (sección 13), sin interfaz en ese corte. La Fase 2D expone la
interfaz HTTP y la consulta bancaria autorizada (sección 14). Las limitaciones
anteriores conservan el alcance histórico de 2A/2B/2C.
DAR3 mantiene su autoridad funcional. No es una obligación técnica literal de
DAR3 ni una ratificación de Fernando, Óscar o Core.

Se conserva el laboratorio `apps/ecomotor/ecomotor_target_demo/`, su label
`ecomotor_target_demo`, los Pasos 1–4 y la demo original #94. El único destino
es `instance/target_persistent_demo.sqlite3`, mediante
`apps.ecomotor.target_persistent_demo_settings`, en `127.0.0.1:8002` y
`/demo/objetivo-persistente/`. No se crea otro entorno económico ni otro saldo.

Fuentes: [decisión REW-MULTI-01](../decisions.md#rew-multi-01--rewards-y-duckybank-demostrativos--23102026),
[Paso 2 y aislamiento](ecomotor-target-persistent-demo-v1.md),
[Paso 3](ecomotor-target-playable-persistent-demo-v1.md),
[Paso 4 y snapshots V1](ecomotor-target-demo-rewards-xp-v1.md),
[Rewards F1-A](rewards-v0.md). Los cortes históricos conservan su alcance:
la prohibición de monedas del Paso 4 describe ese incremento; REW-MULTI-01
autoriza una ampliación posterior exclusivamente demostrativa. Su servicio
monetario interno se incorpora en 2C y su interfaz en 2D.

## 2. Alcance aprobado y concreciones propuestas

La ampliación permitirá una actividad ficticia de **5 DuckyCoins**, abonadas
realmente en una Wallet local y registradas en una Transaction de Bank, junto
con un DemoTargetRewardEvent coherente. Los importes y reglas son sintéticos.
Se reutiliza exclusivamente `apps.bank.services.credit_coins()` para acreditar.
User, Wallet y Transaction son los modelos existentes, en la SQLite aislada;
no se duplican modelos económicos ni se usan usuarios de otras bases.

Permanecen el desafío XP700 y la visita NO_REWARD, XP directa, evoluciones,
opciones, atributos y sus replays. Una actividad tiene **cero o un efecto**:
XP positiva, 5 monedas, o ausencia de efectos. No se admiten XP + monedas en la
misma recompensa, objetos, puntos directos ni efectos adicionales. Un error
de sesión, configuración, Bank, integridad o BD nunca equivale a NO_REWARD.

Las secciones siguientes concretan una **propuesta técnica local** para llevar
la aprobación a implementación: nombres de campos, nulabilidad, constraints,
metadatos, codificación de claves y esquema V2. No atribuyen esas elecciones
físicas a una aprobación externa. Deben revisarse en 01B-2 y, si alteran el alcance
aprobado, volver a 02C-2 antes del prompt de implementación.

## 3. Contrato real de Bank revisado

La firma pública actual, en [services.py](../../apps/bank/services.py), es:

```python
credit_coins(
    user,
    amount,
    *,
    source,
    operation_key,
    issuing_entity="Ecomotor",
    reference_type="",
    reference_id="",
    description="",
)
```

Devuelve `LedgerResult`, dataclass frozen con `transaction: Transaction` y
`created: bool`; `already_applied` es la propiedad `not created`. El objeto ORM
anidado no se vuelve inmutable por ese decorador. El resultado de demo deberá
copiar datos escalares verificados a una representación histórica inmutable.

Hechos del código existente, no garantías nuevas:

- Importe entero Python exacto positivo, sin bool. El saldo resultante no puede
  superar `MAX_BALANCE = 2**63 - 1`. No crea Wallet: falta de aprovisionamiento
  produce `WalletNotProvisioned`.
- Usa `transaction.atomic()` sin `using` y managers sin `.using()`: el contrato
  de esta integración queda restringido a **default**. No tiene parámetro de alias.
  El router actual de demo solo dirige sesiones; no debe añadirse otro que envíe
  Bank a una conexión diferente.
- `_record_movement` crea un REWARD de importe firmado positivo, actualiza
  `Wallet.available_balance` y devuelve la Transaction. Su `atomic()` será un
  savepoint dentro del exterior Rewards/default; no confirma por separado.
- Idempotencia persistente **(wallet, operation_key)**, no por usuario global,
  actividad, descripción o fingerprint aislado. `operation_key` admite hasta 255
  caracteres, source/issuing_entity hasta 100 y referencias/description sus
  límites de modelo. La demo aplicará tipos y longitudes estrictos antes de llamar.
- La huella Bank es SHA-256 del JSON canónico de versión 1, transaction_type,
  amount firmado, source, issuing_entity, reference_type y reference_id:
  `sort_keys=True`, separadores `(',', ':')`, `ensure_ascii=False`, UTF-8.
  **description no participa**. Misma clave con huella distinta produce
  `IdempotencyConflict`; misma clave y huella recupera el movimiento existente.
  Esto no comprueba por sí solo la causa Rewards ni la integridad de todo el ledger.
- El código usa `select_for_update()`, pero SQLite no aporta bloqueo por fila:
  la serialización de este laboratorio dependerá del exterior IMMEDIATE/D-19.

[Wallet y Transaction](../../apps/bank/models.py) mantienen sus modelos:
Wallet.user es OneToOne CASCADE; Transaction.wallet es FK CASCADE. El ledger
conserva tipo, amount, balance_after, operation_key, source_platform,
issuing_entity, reference_type/id, description, request_fingerprint y created_at.
Unicidad wallet/clave y checks de amount no cero, saldo no negativo y clave no
vacía no acreditan por sí solos identidad causal ni congelación frente a SQL directo.
No se modifican esas políticas propietarias ni se usa UserProfileBank como saldo.
Los [tests Bank actuales](../../apps/bank/tests.py) cubren idempotencia y conflictos
de referencia/origen, pero no prueban aún este coordinador Rewards/default.

## 4. Identidades, sesión y ciclo de vida

| Identidad | Fuente y función |
| --- | --- |
| Rewards | Terna original `(origin_code, fact_id, recipient_id)` de F1-A; mismo origen servidor `persist-demo-rewards`, destinatario `demo-progress:<PK>`. La huella compara contenido, no sustituye esta identidad. |
| Sesión propietaria | Secreto local cuyo hash es progress.session_owner; autoriza la partida, también antes de leer historia o hacer replay. No es un User autenticado Core. |
| Usuario sintético | Un User distinto por partida, persistente y privado del laboratorio, resuelto por FK servidor. No cambia recipient_id ni la identidad de hechos anteriores. |
| Banco | Wallet de ese User en default y `(wallet, operation_key)`; Transaction exacta enlazada por el RewardEvent. No es la identidad de XP ni un permiso. |

Propuesta: aprovisionamiento **perezoso en la primera recompensa nueva de monedas**,
después de validar sesión, hecho, ausencia de replay y configuración. Partidas
antiguas y nuevas pueden seguir sin User mientras solo usen XP/opciones/visita.
GET, lectura histórica, emisión de tokens y replay no aprovisionan nada.

En el mismo exterior IMMEDIATE, se crea un User con username aleatorio de namespace
reservado de demo (p. ej. `rew-demo-` + 32 hex), sin email, nombres ni datos personales,
`set_unusable_password()`, `is_active=False`, `is_staff=False`, `is_superuser=False`.
Se crea su Wallet a cero y se vincula a la partida; todo revierte si falla la operación.
No se llama a login ni se asigna `_auth_user_id` a la sesión. No se crean perfiles V1,
permisos o credenciales utilizables. Los campos descritos corresponden al User
actual de Django; un futuro AUTH_USER_MODEL incompatible exigiría revisión explícita.

Una vez vinculados, User y Wallet se conservan y no se reasignan ni comparten entre
partidas, aunque pertenezcan al mismo navegador. Reiniciar crea otra partida y
no borra historial, User o saldo anteriores. Perder la sesión no habilita recuperar
otra partida por ID. No hay endpoint de supresión; la limpieza futura se limita
a la SQLite ficticia completa según el procedimiento del Paso 2.

Una vinculación existente con User ausente/no sintético, Wallet ausente, usuario
compartido o causa cruzada es **inconsistencia**, no una orden de recrear Wallet,
reasignar usuario o reconstruir saldo. Una colisión de username no permite adoptar
un usuario existente. NULL histórico solo permite aprovisionar ante una nueva
concesión de monedas válida; jamás reinterpreta una recompensa antigua.

## 5. Hechos, reglas, clave causal y metadatos

Propuesta de actividad cerrada `coin_challenge` y efecto interno F1-A
`ProposedEffect("DUCKYCOINS", 5)`. Este literal es de demo, no código canónico
ratificado por Bank/Core. Una nueva versión `demo-rewards-rules-v2` incorporará
una regla sintética propia para esa actividad, manteniendo XP700 y visita.
Los efectos se comprueban antes de ejecutar servicios; combinaciones o tipos
no soportados rechazan toda la operación.

El servidor emite un token Rewards ligado a partida, propietario, actividad,
fact_id e instante UTC original, conservado en reenvíos. No se acepta del HTTP
User, Wallet, Transaction, cantidad, origen, destinatario, regla, catálogo o saldo.
Se mantienen CSRF, escape, rechazo de extras/duplicados y POST/Redirect/GET.
El propósito firmado sigue separado de XP directa y opciones jugables.

Los constructores de hechos/token de challenge y visit V1 deben mantenerse
exactamente para preservar huellas, contexto, occurred_at y tokens existentes.
Para la actividad nueva se propone `demo-fact-v2`, contexto
`{"demo":"REW-MULTI-01","fact_version":"demo-fact-v2"}` y resultado
`{"completed":true}`; la selección de versión es cerrada por servidor/actividad.
No se sustituye la versión original de un hecho al hacer replay ni se modifica
F1-A. Una versión de reglas nueva no cambia la huella de un hecho anterior.

Clave Bank propuesta: `rb1:` + SHA-256 hexadecimal **completo** del UTF-8 del JSON
`["demo-reward-bank-key-v1", origin_code, fact_id, recipient_id]`, con separadores
`(',', ':')`, `ensure_ascii=True`, sin espacios ni concatenaciones ambiguas.
Longitud 68, dentro de 255. No usa fingerprint semántico, importe, regla actual,
PK del RewardEvent, User ni saldo; es estable ante reintentos. Se conserva `rx1:`
de XP y las claves directas del Paso 2 sin alterarlas ni truncar la clave Bank a 32.

Metadatos propuestos y fijos de la llamada:

| Parámetro | Valor servidor |
| --- | --- |
| amount | 5 |
| source | `persist-demo-rewards` |
| issuing_entity | `EcomotorDemo` |
| reference_type | `demo_reward_fact_v1` |
| reference_id | La clave `rb1:…` completa |
| description | Texto sintético informativo; no identidad ni control de idempotencia |

La referencia no necesita un RewardEvent parcial: deriva de su identidad estable.
Antes de un crédito nuevo, si ya hay Transaction en esa Wallet con la clave derivada
sin RewardEvent confirmado coherente, se rechaza como historia huérfana. No se
adopta automáticamente un movimiento, aunque Bank devuelva `created=False`.
Para una identidad nueva, el resultado Bank esperado es `created=True`; una
colisión o causa incompatible aborta. La verificación contrasta terna completa,
metadatos y FK, sin asumir que el digest por sí solo certifica su origen.

## 6. Propuesta física mínima para la futura 0004

**Diseño de Fase 1; esquema implementado en Fase 2B (sección 12).** La lógica
monetaria se incorpora en 2C, sin ampliar el esquema. Se extienden únicamente dos modelos de la app de demo:

| Modelo/campo | Tipo y nulabilidad propuestos | Garantía local |
| --- | --- | --- |
| DemoTargetProgress.synthetic_user | OneToOne a settings.AUTH_USER_MODEL, null=True, blank=True, PROTECT | Usuario exclusivo por partida; NULL compatible con partidas históricas. |
| DemoTargetRewardEvent.coin_amount | PositiveBigIntegerField, no nulo, default=0 | Entero 0…2⁶³−1; cero significa ausencia de efecto monetario, no premio cero. |
| DemoTargetRewardEvent.bank_transaction | OneToOne a bank.Transaction, null=True, blank=True, PROTECT | Causa bancaria exacta, no reutilizable por dos recompensas. |

Se mantiene la FK progress, la unicidad `(progress, origin_code, fact_id)`,
la OneToOne xp_event, y todos los campos/versiones/snapshots originales.
Las OneToOne nullable permiten múltiples NULL en SQLite: no exigen aprovisionar
usuarios o causas para filas antiguas; sí impiden reutilizar una referencia no nula.
No se añade otro modelo Wallet, relación User en Rewards redundante, copia de
saldo actual ni vínculo a UserProfileEcomotor. Wallet se resuelve por el User
de la partida; su PK histórica se conserva en V2 para detectar sustituciones.

Se sustituirá solo el check `demo_reward_outcome_valid` por tres ramas excluyentes:

| Estado | XP | Monedas | Causas |
| --- | --- | --- | --- |
| APPLIED XP | xp_amount > 0 | coin_amount = 0 | xp_event presente; bank_transaction NULL |
| APPLIED monedas | xp_amount = 0 | coin_amount > 0 | xp_event NULL; bank_transaction presente |
| NO_REWARD | xp_amount = 0 | coin_amount = 0 | ambas causas NULL |

Checks de rango se mantienen para XP y se añaden para monedas; en servicio,
la actividad aprobada exige exactamente **5**, no cualquier importe positivo.
Los checks no pueden demostrar relaciones entre tablas: el servicio verificará
partida→User→Wallet→Transaction, destinatario, importe, tipo, referencias,
catálogo/ancla XP e identidad semántica. max_length no es protección automática
de SQLite. PROTECT es política local ORM/FK, no inmutabilidad física del ledger
ni aprobación de conservación productiva. Las cascadas propias de Bank no se cambian.

Dependencias propuestas: `ecomotor_target_demo.0003_synthetic_rewards`,
`bank.0001_initial` y `migrations.swappable_dependency(settings.AUTH_USER_MODEL)`.
Bank ya depende del User y no del laboratorio: este grafo no introduce un ciclo
en las dependencias revisadas. Los campos y checks son representables con los
tipos existentes de Django 5.2/SQLite. En Fase 1 su generación y prueba efectiva
quedaban reservadas a implementación; la evidencia de Fase 2B consta en sección 12.

0004 será estructural, sin RunPython, datos oficiales o backfill de usuarios,
Wallet, Transaction o causas. Las filas antiguas reciben únicamente ausencia
monetaria (`coin_amount=0`, FK NULL) y synthetic_user NULL; **no se toca el JSON V1**.
No se reescriben 0001–0003 ni migraciones Bank; sin fake ni eliminación de SQLite.
SQLite puede reconstruir tablas al alterar un check: deberá probarse conservación
de todas las filas/FKs/índices y triggers 0007 del catálogo, sin alterar esos triggers.

## 7. Snapshots V1 y V2

`demo-reward-result-v1` conserva exactamente el esquema del Paso 4: identidad,
actividad/instante, huella/versiones, status, rule_set_version, matched_rule_id,
eligible, effects, reason_codes, xp_amount, xp_event_id, evolution_ids, catálogo,
anchor_xp_event_id y progression. Su lector no insertará claves monetarias,
no cambiará serialización ni reinterpretará la decisión con reglas actuales.
En BD exige columnas monetarias a cero/NULL. No requiere User para recuperar V1,
incluso si la partida se aprovisionó después por un hecho nuevo.

Propuesta V2 para **todos los nuevos RewardEvent**: `schema = demo-reward-result-v2`,
los mismos campos históricos V1 y dos claves adicionales obligatorias:

- `coin_amount`: entero exacto no negativo.
- `bank`: NULL para XP/NO_REWARD, o un objeto causal completo para monedas:
  `user_id`, `wallet_id`, `transaction_id`, `operation_key`, `transaction_type`,
  `amount`, `balance_before`, `balance_after`, `source_platform`, `issuing_entity`,
  `reference_type`, `reference_id`, `request_fingerprint`, `created_at` original.
  Los identificadores son PK exactas positivas y los saldos enteros representables;
  amount=5 y balance_after=balance_before+5. Se contrasta contra Transaction;
  balance_before se deriva de su balance_after y amount, no del saldo actual.

Monedas no crean XPEvent ni evoluciones. Conservan observación XP estacionaria
anclada al último XPEvent anterior, o al inicio real si no existe, siguiendo la
semántica del Paso 4. No se fabrica una nueva época o un desbloqueo. Los resultados
de servicio se propondrán frozen/slots con datos anidados inmutables y un indicador
replay **fuera del snapshot original**; el lector despacha por versión explícita
y rechaza versión desconocida o estructura no canónica. Las claves de cada objeto
deben ser exactamente las de su versión, con tipos estrictos: bool no equivale a
int y no se normalizan identidades, importes, versiones ni contenidos originales.

El saldo histórico del crédito es `Transaction.balance_after`; puede ser distinto
de Wallet.available_balance después de nuevas actividades. La UI distinguirá
«saldo después de este hecho» de «saldo actual», consultado separadamente bajo
sesión. Replay no sustituye el saldo original por el actual ni exige su igualdad.

## 8. Exterior transaccional, replay y errores

Rewards es propietario de **una única transacción exterior** `atomic(using="default")`,
SQLite IMMEDIATE, timeout cinco segundos, iniciada antes de las lecturas mutables.
Exige entorno exclusivo, archivo/conexión efectiva protegidos y alias exactamente
default; otro alias se rechaza **antes de escribir o llamar a Bank**. Se mantienen
mode=rw no creador, controles symlink/junction/hardlink y de sustitución del archivo;
solo migrate explícito puede crear inicialmente la SQLite. Sin BEGIN manual,
transacción envolvente ajena, autocommit manual ni reintentos automáticos.

Flujo propuesto:

1. Validar firma/actividad/instante original y sesión; abrir exterior y recargar
   partida propietaria. Verificar historia y buscar primero la identidad Rewards.
2. Si existe y su huella coincide, verificar su lector V1/V2 y todas las causas;
   devolver resultado original sin evaluar reglas, aprovisionar, guardar ni llamar
   a credit_coins o al núcleo XP. Otra huella es conflicto sin efectos.
3. Si es nueva, validar catálogo/progreso y propuesta F1-A. Para monedas únicamente,
   aprovisionar User/Wallet si no estaban vinculados, verificar identidad bancaria
   y ausencia de causas huérfanas, y llamar a credit_coins con metadatos cerrados.
4. El atomic interno de Bank es un savepoint en **la misma conexión default**.
   Tras su retorno se verifica LedgerResult y Transaction. Para XP se conserva
   el núcleo privado del Paso 4, sin otra transacción exterior; NO_REWARD no llama
   a ningún escritor de efectos. No se combinan ramas XP/monedas.
5. Guardar RewardEvent/V2 y sus referencias; releer/contrastar causas reales y
   snapshot antes de salir del exterior. Solo entonces anunciar APPLIED/NO_REWARD.

Se confirma o revierte conjuntamente aprovisionamiento nuevo, saldo, Transaction,
RewardEvent y referencias. Un fallo de Bank, de guardado Rewards o de verificación
final no puede dejar saldo/causa huérfanos. No se actualizan elecciones/atributos,
XP o evoluciones por una concesión exclusivamente monetaria.

El contexto XP actual exige exactamente el bloque exterior vivo. Durante la llamada
Bank habrá un savepoint: no se invocará el núcleo XP dentro de él, ni se relajará
esa defensa. Después de volver de Bank el savepoint ha terminado. No es necesario
modificar Bank ni llamar a grant_demo_target_xp dentro del exterior.

Replay V2 contrasta FK Transaction, Wallet y User de esa partida, campos Bank,
huella bancaria de la solicitud original, clave derivada, cantidad, snapshot,
ancla XP y exclusividad de causa. V1 mantiene sus verificaciones originales.
No se importa un helper privado Bank como nueva API: la comprobación de la huella
se documenta con la codificación existente y necesitará tests de compatibilidad.
También se comprueban movimientos del namespace rb1 de la Wallet vinculada sin
RewardEvent coherente; no se reconstruyen ni adoptan como premio.

Causa ausente/ajena, Wallet sustituida, importes/JSON contradictorios o huella
incompatible son errores de integridad/conflicto, nunca reparación automática.
Errores Bank (InvalidAmount, WalletNotProvisioned, IdempotencyConflict), sesión,
catálogo, restricciones, SQL y bloqueo/timeout mantienen significado distinguible.
La adaptación HTTP puede controlarlos, pero no convertirlos en NO_REWARD o éxito.
Se puede reintentar explícitamente el mismo hecho tras resolver un bloqueo.
No se promete defensa frente a un administrador capaz de reescribir toda la BD.

## 9. Condición previa de tests: default protegido real

El fixture actual de [demo_tests.py](../../apps/ecomotor/ecomotor_target_demo/demo_tests.py)
crea `persistent_fixture`; no basta cambiar el alias de Rewards mientras Bank
permanece en default. Tampoco basta un mock de credit_coins o un router que oculte
una segunda conexión. **Esta condición debe probarse antes de implementar el flujo.**

Propuesta preferida: **fixture default protegido en subproceso de test**, invocado
explícitamente desde la fase exclusiva. Evita sustituir el default en memoria del
runner padre, cerrar su conexión y perder su esquema/estado, o mutar configuración
compartida. Es una concreción técnica de pruebas para revisión, no otro entorno
de demo instalado ni un cambio a la API Bank.

1. Una prueba explícita del módulo demo_tests.py crea TemporaryDirectory y su
   subdirectorio instance. Registra cleanup antes de lanzar el proceso. Captura
   configuración/default, wrapper y flags del padre; el subprocess no los modifica.
   No hereda el setUp que selecciona persistent_fixture ni un atomic de Django TestCase.
2. El hijo arranca con los settings persistentes oficiales y un bootstrap **solo de
   test**, anterior a django.setup()/cualquier conexión. Cambia únicamente BASE_DIR
   a la raíz temporal, NAME a su instance/target_persistent_demo.sqlite3 y
   TARGET_PERSISTENT_DEMO_ALIAS a default. Conserva ENGINE protegido, IMMEDIATE/5,
   router, flags y todas las comprobaciones de aislamiento. No modifica
   config.settings ni su referencia a la base habitual.
3. Migrate/seed se ejecutan exclusivamente sobre ese default temporal por los
   comandos protegidos. El hijo ejecuta casos seleccionados de unittest sin volver
   a invocar el runner de dos fases ni recursar al test lanzador. No instala la app
   en settings normales ni cambia tests históricos. Bank/auth/demo deben estar
   migrados en ese archivo; la creación inicial sigue limitada a migrate.
4. Antes de conceder se verifica PRAGMA database_list, identidad física, alias y
   conexión nativa de Rewards/default; el trazado real de la llamada credit_coins
   debe demostrar INSERT/UPDATE Bank en esa misma conexión. Los objetos User,
   Wallet, Transaction, progreso y RewardEvent pertenecen a default. Una prueba
   negativa con Rewards en persistent_fixture debe rechazar antes de escribir:
   compartir el nombre físico mediante dos aliases tampoco demuestra un solo atomic.
5. Capturar SQL de default: un BEGIN IMMEDIATE exterior y COMMIT final, con
   SAVEPOINT/RELEASE Bank permitidos y sin commit intermedio. Inyectar fallo tras
   el crédito real y comprobar todas las tablas/saldos desde otra conexión después
   del rollback. No mockear el crédito para demostrar esta garantía.
6. Dentro del hijo, carreras con conexiones[default] independientes por hilo al
   mismo archivo. Barreras/eventos, timeout real y cierre de cada wrapper en finally;
   no compartir conexiones nativas ni usar memoria para probar concurrencia.
7. El hijo libera bloqueos, une workers y cierra conexiones antes de finalizar,
   incluso tras fallo. El padre espera salida con timeout acotado y, ante cuelgue,
   termina y espera al hijo antes de limpiar **solo** TemporaryDirectory. Un fallo
   del hijo hace fallar el test padre; se publican casos y resultados del hijo,
   sin ocultar omisiones ni contar dos veces escenarios. No se permite continuar
   con un hijo vivo o borrar archivos todavía abiertos en Windows.
8. Tras éxito y errores deliberados se comprueba restauración: configuración,
   alias/wrapper, autocommit, flags y registry del padre idénticos; nada requiere
   reabrir una SQLite personal. Se comparan hashes protegidos. El aislamiento por
   proceso evita que las carreras alteren el default de otros tests.

Se conserva el runner de dos fases y descubrimiento explícito
`apps.ecomotor.ecomotor_target_demo.demo_tests`, junto con todos los fixtures
históricos. No se añaden bypasses de checked_path/MIGRATING ni se parchea Bank
para aceptar using. La Fase 2A demuestra la viabilidad del arnés según la sección
11; no implementa ni autoriza por sí sola el flujo monetario de las fases siguientes.

## 10. Plan de aceptación futuro y pendientes

Antes de dar por implementado REW-MULTI-01 se exigirán pruebas reales de:

- 5 monedas: Wallet +5, una Transaction REWARD y un RewardEvent APPLIED causal;
  XP/evoluciones/atributos intactos. XP700 y NO_REWARD existentes siguen funcionando.
- Aprovisionamiento por primera necesidad, dos partidas/sesiones con User/Wallet
  distintos, usuario inactivo sin credenciales, sesión ajena/tokens cruzados,
  campos HTTP de autoridad, CSRF y duplicados rechazados.
- Replay sin escrituras ni llamadas a credit_coins, incluso con reglas futuras,
  saldo posterior distinto y reapertura. Mismo hecho incompatible es conflicto.
  Bank idempotente por su propia identidad no sustituye este replay Rewards.
- Fallo real/inyección antes y después del crédito, en RewardEvent y verificación
  causal: rollback completo, incluido aprovisionamiento. Errores no son NO_REWARD.
- Dos intentos del mismo hecho, hechos diferentes, monedas frente a XP/opciones,
  contenido incompatible concurrente y timeout real en default file-backed:
  serialización o bloqueo controlado sin efectos parciales ni premios dobles.
- Copia desechable anterior a 0004 con XP, opciones y Rewards V1 completos:
  migrar sin modificar JSON/huellas/causas, recuperar tokens/replays originales,
  aprovisionar solo ante un hecho nuevo y mantener V1 junto a V2. Una base nueva
  también debe funcionar. Rechazar historial monetario incompleto o cruzado.
- Restauración del fixture tras éxito/fallo; default normal nunca abierto para
  la prueba Bank; regresiones Bank, Pasos 1–4, F1-A y suites completas habituales
  y exclusivas, checks/migraciones e integridad de archivos protegidos.

Esas pruebas funcionales no se ejecutaron en la PR documental de Fase 1.
La evidencia limitada de Fase 2A se registra en la sección 11. Ninguna fase ejecuta
seeds, migrate o escrituras sobre SQLite personal.

Al cierre de Fase 1 quedaban para 01B-2 las concreciones físicas y V2, la evidencia
del arnés default y el prompt de implementación separado. Las secciones 11–12
registran los avances de 2A y 2B; la sección 13 añade V2 y la funcionalidad monetaria
interna de 2C. La interfaz sigue pendiente.
Si se necesita cambiar
Bank, el aislamiento o la arquitectura, detener esa parte y devolverla a 02C-2.
Permanecen abiertos Fernando/Core y contratos propietarios, F2-A productivo,
USE-01B, TRACE-01B, fuentes funcionales oficiales e integración con juegos reales.
No Wallet global, monedas oficiales, Shop, objetos, autenticación Core ni activación.
S3 V1 y los datos de otras aplicaciones permanecen fuera de este incremento.

## 11. Fase 2A · Evidencia ejecutable del fixture Bank/default

El auxiliar exclusivo de tests
[bank_default_fixture.py](../../apps/ecomotor/ecomotor_target_demo/bank_default_fixture.py)
se ejecuta por subproceso desde BankDefaultSubprocessTests de
[demo_tests.py](../../apps/ecomotor/ecomotor_target_demo/demo_tests.py). No lo importa
ningún servicio ni se descubre con los tests habituales. No invoca el runner
recursivamente ni cambia sus dos fases.

Cada hijo configura default antes de django.setup(), manteniendo backend protegido,
IMMEDIATE/5 y router oficiales, con BASE_DIR temporal y el nombre de archivo exacto
instance/target_persistent_demo.sqlite3. Un audit hook de Python rechaza cualquier
intento de conexión SQLite fuera de ese archivo; no sustituye sqlite3.connect.
La apertura normal previa a migrate se rechaza sin crear archivo. Solo el comando
migrate real crea la base; migrate/seed posteriores afectan únicamente al temporal,
sin manipular MIGRATING ni otras protecciones.

Cuatro tests padre ejecutan seis casos positivos en hijos, más un fallo deliberado
para probar propagación/limpieza. La primera ejecución específica completó los
cuatro sin fallos ni omisiones en 18,834 s y obtuvo:

- Crédito Bank real de **17 monedas de prueba**, sin actividad ni regla Rewards
  nueva. User/Wallet/Transaction usan default y el mismo archivo/conexión nativa
  del propietario transaccional existente `_xp_transaction`, usado por Rewards.
- SQL nativo: un BEGIN IMMEDIATE, savepoint Bank liberado, dos escrituras Bank en
  esa misma conexión y un único COMMIT exterior. Un observador independiente
  mode=ro ve saldo cero y ninguna Transaction antes de confirmar; después ve 17.
- Fallo tras crédito exitoso: ROLLBACK sin COMMIT, Wallet previa intacta y ninguna
  Transaction. Con aprovisionamiento dentro del exterior, tampoco quedan User/Wallet.
- Misma clave/parámetros: un movimiento; cambiar importe o referencia produce
  IdempotencyConflict. Dos escritores simultáneos con conexiones independientes
  serializan tanto una clave compartida (un crédito) como claves distintas (dos).
- Bloqueo real con otro escritor IMMEDIATE: DemoBusyError tras **5,547 s** en esa
  ejecución, ningún movimiento parcial y reintento explícito compatible sin duplicar.
- Cierre de conexiones/hijos y eliminación del directorio temporal, también ante
  el fallo deliberado. El padre comprueba identidad de su wrapper/conexión default,
  configuración, autocommit, registry y flags intactos, además de hashes protegidos.

Se verifica ausencia de nuevos XPEvent, evoluciones o RewardEvent por el crédito.
No se ha creado una recompensa monetaria ni demostrado todavía su snapshot V2,
causalidad RewardEvent→Transaction, vinculación persistente User/partida o
migración 0004. Esas funcionalidades siguen fuera de Fase 2A. Los resultados de
regresiones y del runner completo se entregan con esta PR de pruebas, distinguiendo
los cuatro tests padre de los seis casos positivos ejecutados dentro de los hijos.

## 12. Fase 2B · Esquema 0004 y compatibilidad histórica

[0004_rewards_bank_schema](../../apps/ecomotor/ecomotor_target_demo/migrations/0004_rewards_bank_schema.py)
depende de 0003, `bank.0001_initial` y la dependencia intercambiable de
`AUTH_USER_MODEL`. Añade `DemoTargetProgress.synthetic_user` OneToOne nullable
con PROTECT, `DemoTargetRewardEvent.coin_amount` PositiveBigInteger con default
cero y `bank_transaction` OneToOne nullable con PROTECT. No crea usuarios,
Wallets ni movimientos y no modifica 0001–0003 ni snapshots V1.

La constraint `demo_reward_outcome_valid` admite exclusivamente APPLIED XP,
APPLIED monedas o NO_REWARD, sin efectos combinados. Se conserva el resto de
restricciones anteriores y se añade el rango explícito de monedas 0–2^63−1.
La integridad local no demuestra correspondencia causal entre partida, User,
Wallet y Transaction: su validación queda para servicios futuros.

Los dos tests padre `Schema0004Tests` reutilizan la protección y limpieza del
arnés de 2A y ejecutan el auxiliar exclusivo
[schema_0004_fixture.py](../../apps/ecomotor/ecomotor_target_demo/schema_0004_fixture.py).
Cada proceso configura default protegido antes de django.setup(), conserva
IMMEDIATE/5 y solo permite conexiones SQLite al archivo temporal canónico.
No modifica backend, settings oficiales ni runner.

- Instalación nueva mediante migrate real: campos, defaults, unicidades, PROTECT,
  tres ramas válidas, rechazos estructurales, rango SQLite y migrate repetido.
  Las filas Bank de esta prueba son fixtures ORM para comprobar FKs/constraints;
  no se invoca credit_coins ni se implementa una actividad monetaria.
- Instalación histórica real hasta 0003: se usan los modelos históricos renderizados
  por Django y las reglas/servicios V1 intactos, vinculando únicamente sus referencias
  ORM al estado histórico. Se generan XP, seis evoluciones, configuraciones Gamer y
  Romano, APPLIED XP, NO_REWARD y tokens firmados reales. Tras cerrar ese proceso,
  el padre copia físicamente la SQLite; otro proceso aplica 0004 sobre la copia.
- Comparación de todas las columnas previas y filas, incluidos JSON V1 sin
  deserializarlos, huellas, identidades y fechas. Se comprueba NULL/cero/NULL en
  los nuevos campos históricos, esquema ajeno idéntico (incluidos triggers),
  conservación de constraints anteriores y ausencia de aprovisionamiento.
- Los tests heredados conservan las huellas AST de 0001–0003. Se amplía el grafo
  esperado con 0004 y se concreta la antigua prohibición general de relaciones
  User: únicamente synthetic_user, nullable y PROTECT, queda admitida por 2B.
- Replays mediante los servicios V1 actuales, sin sustituir reglas ni cálculos:
  resultados históricos idénticos, sin DML/DDL y con tokens previos válidos.
  Reapertura, migrate sin operaciones pendientes, check y makemigrations --check
  se ejecutan exclusivamente sobre el archivo temporal.

En el corte de Fase 2B las pruebas no certificaban snapshots V2, aprovisionamiento desde Rewards ni
créditos monetarios causales. No hay actividad coin_challenge, cambio HTTP ni
interfaz nueva. Fase 2C, F2-A productivo, USE-01B, TRACE-01B y acuerdos externos
permanecen fuera de este incremento. Las ejecuciones y recuentos reales de las
suites se entregan en la PR de 2B, sin reutilizar cifras históricas.

## 13. Fase 2C · Servicio interno y snapshots V2

Implementación para revisión desde develop `ddaae6898607cd1361c07ea7a0caa5a019df155a`.
Se conservan las firmas `issue_reward_fact`, `apply_demo_reward` y
`read_demo_rewards` de [reward_demo_services.py](../../apps/ecomotor/ecomotor_target_demo/reward_demo_services.py).
No hay migraciones nuevas ni cambios en Bank, modelos, settings, backend, runner,
vistas, formularios o templates. La referencia de esquema sigue siendo 0004.

### Compatibilidad y frontera de alias

La restricción default de la sección 8 se aplica al **flujo monetario**. XP,
NO_REWARD y sus replays V1/V2 conservan el alias histórico del laboratorio,
incluido persistent_fixture en tests, sin consultar Bank cuando la partida no
tiene vinculación monetaria. coin_challenge exige default protegido antes de
cualquier escritura o llamada Bank. Una historia con User/causa bancaria requiere
esa misma conexión; no se mueve Bank a otro alias ni se comparten conexiones.
Esto concreta la compatibilidad con el Paso 4 y la frontera monetaria de 2C.

[reward_demo_rules.py](../../apps/ecomotor/ecomotor_target_demo/reward_demo_rules.py)
incorpora la regla `demo-coin-challenge-5-v2` en `demo-rewards-rules-v2` y el hecho
coin_challenge/demo-fact-v2 con el contexto de sección 5. challenge y visit
conservan exactamente su constructor V1, contexto, instante, firma y huella.
ACTIVITIES permanece con las dos opciones HTTP anteriores; la actividad nueva
solo figura en la lista interna del servicio. La Fase 2D no se implementa aquí.

### Confirmación y lectura histórica

Solo una recompensa monetaria nueva, válida y de cinco monedas puede aprovisionar
User/Wallet: usuario `rew-demo-<32 hex>`, inactivo, sin privilegios ni credenciales
utilizables o información personal. Una vinculación existente incompatible se
rechaza sin recrearla. El crédito utiliza credit_coins con los metadatos y clave
rb1 completos de sección 5. Se comprueba LedgerResult, su conexión, el movimiento
real, Wallet/User y la huella bancaria según la codificación pública documentada;
no se importa un helper privado de Bank.

El exterior es el contexto IMMEDIATE existente de Rewards/XP. Bank abre únicamente
su savepoint; tras retornar, se verifica de nuevo la frontera exterior. Antes de
confirmar se relee RewardEvent y se contrasta el snapshot con sus causas reales.
Errores Bank, catálogo, acceso, integridad y bloqueo conservan su significado;
ninguno se transforma en NO_REWARD. No se reintenta automáticamente.

Cada recompensa nueva guarda demo-reward-result-v2, con coin_amount y bank incluso
en XP/NO_REWARD (cero/NULL). DemoRewardResult y el nuevo DemoBankSnapshot son
frozen/slots; la evidencia bancaria contiene únicamente escalares inmutables.
El lector despacha por V1/V2 y compara exactamente la estructura canónica de su
versión contra columnas, identidad semántica, propuesta y causas verificadas.
No acepta claves adicionales, bool como entero ni saldos históricos sustituidos
por el saldo actual. El lector V1 no añade claves ni reescribe sus JSON.

Replay se resuelve antes de evaluar reglas o aprovisionar; devuelve el resultado
original sin llamar a Bank. Se detectan causas ausentes/cruzadas, metadatos
alterados y movimientos rb1 huérfanos de la Wallet vinculada. Una clave derivada
ya existente para un hecho nuevo se rechaza, aunque no haya User vinculado a esa
partida; nunca se adopta como premio. No es una garantía frente a un administrador
capaz de reescribir coordinadamente toda la base.

### Evidencia de pruebas

El auxiliar exclusivo
[reward_bank_fixture.py](../../apps/ecomotor/ecomotor_target_demo/reward_bank_fixture.py)
reutiliza el patrón de subproceso/default protegido de 2A, con audit hook que solo
admite la SQLite temporal canónica y configuración anterior a django.setup().
Cuatro tests padre ejecutan **20 casos monetarios reales** en los hijos. Junto
con el rechazo de alias y la copia histórica ampliada, la ejecución focalizada
completó **6 tests padre, sin fallos ni omisiones, en 35,111 s**:

- Crédito de cinco monedas, User/Wallet/Transaction REWARD/RewardEvent y V2
  enlazados; XP, seis evoluciones y configuraciones Gamer/Romano intactos.
- SQL real: un BEGIN IMMEDIATE, savepoint Bank y un COMMIT sobre la misma conexión
  nativa default. Un observador independiente no ve aprovisionamiento ni crédito
  antes de confirmar. Fallos después del crédito, al guardar Rewards o al verificar
  la causa revierten conjuntamente User/Wallet/Transaction/RewardEvent.
- Replay sin Bank ni evaluación actual, saldo original cinco frente a saldo actual
  diez, ancla XP intacta y recuperación tras reabrir. Dos partidas tienen usuarios
  distintos; tokens ajenos, alterados o cruzados se rechazan sin efectos.
- Conexiones independientes: mismo hecho, hechos distintos, monedas frente a XP
  directa y configuración jugable, e identidad incompatible concurrente. Timeout
  real observado de **5,453 s**, seguido de reintento explícito sin duplicación.
- Corrupción controlada de V2, tipos, causa ausente, Wallet/User cruzados, importe,
  referencia y huella Bank, estados y namespace huérfano: error sin reparación.

La prueba histórica de 2B ahora construye explícitamente V1 en el estado ORM 0003
(reglas V1, serialización V1 y omisión de las columnas todavía inexistentes), sin
sustituir los algoritmos XP, identidad o fingerprint. Después de copiar/migrar
verifica todos los datos originales, añade monedas V2 a la misma partida y vuelve
a ejecutar los tokens V1 tras el aprovisionamiento. No se desactiva ningún test
heredado ni se cambia el runner. Los recuentos de la regresión completa se entregan
en la PR de 2C como ejecuciones nuevas.

El runner completo de dos fases se ejecutó con
`python manage.py test --settings=apps.ecomotor.target_persistent_demo_settings`:
**1297 tests habituales en 174,559 s, sin fallos y con dos omisiones heredadas por
symlinks de Windows**, seguidos de **110 tests persistentes en 386,207 s, sin fallos
ni omisiones**. Los casos hijos monetarios anteriores están incluidos mediante
sus cuatro tests padre, sin sumarlos artificialmente al recuento del runner.
En esa ejecución el timeout monetario real fue de **5,594 s**, con reintento sin
duplicación. Check normal/exclusivo y makemigrations --check --dry-run no detectan
incidencias ni cambios; las comprobaciones de migraciones usan SQLite temporales
(la exclusiva ya migrada por el fixture), nunca las bases personales.
Se verifican enlaces/anclas, git diff --check y hashes SHA-256 intactos de los siete
archivos protegidos del laboratorio.

Este incremento no implementa interfaz, juegos, autenticación Core, compras,
F2-A productivo, USE-01B ni TRACE-01B. Los cinco DuckyCoins, usuarios y reglas son
sintéticos: no hay ratificación económica externa ni autorización funcional.

## 14. Fase 2D · Interfaz HTTP y consulta bancaria

La ruta persistente existente incorpora tres actividades cerradas: challenge
(+700 XP), visit (NO_REWARD) y coin_challenge (+5 DuckyCoins ficticias). El
formulario amplía explícitamente sus opciones sin cambiar ACTIVITIES ni los
constructores de hechos V1. Usa issue_reward_fact y apply_demo_reward existentes:
no acepta importes, origen, destinatario, User, Wallet o Transaction desde HTTP.
No cambia el servicio de concesión aprobado en 2C ni crea migraciones o endpoints.

### Lectura autorizada y representación histórica

read_demo_bank valida contexto aislado y propiedad de sesión, recarga la partida
y comprueba el historial Rewards/XP/Bank dentro de una transacción exterior
IMMEDIATE. Si synthetic_user es NULL devuelve provisioned=False, balance=None
y movimientos vacíos, sin consultar Bank ni aprovisionar nada. Así conserva
también las lecturas XP/NO_REWARD del alias histórico de tests.

Con vinculación bancaria exige default protegido y valida User/Wallet sintéticos.
Reutiliza las APIs públicas wallet_summary(user) y transaction_history(user),
materializando sus resultados dentro de la misma transacción. Contrasta el saldo
con la Wallet validada y las filas con su propietario, tipos y rangos. Devuelve
DemoBankOverview y DemoBankMovement frozen/slots, con escalares y tuplas; no
entrega objetos ORM al template. La consulta no ejecuta DML ni DDL.

La pantalla distingue **Saldo actual · Wallet validada** de **Saldo después de
aquella recompensa**, tomado del snapshot V2 original. Los movimientos muestran
solo identificador, fecha, tipo, importe y saldo histórico. La Wallet todavía no
aprovisionada se identifica expresamente, sin mostrar cero como saldo confirmado.
Se conservan XP, niveles, evoluciones, opciones y configuraciones anteriores.

### HTTP, replay y errores

Se mantiene CSRF real, GET/POST, rechazo de parámetros GET y campos POST extra,
ausentes o duplicados, firmas por sesión/partida/actividad y POST/Redirect/GET.
La sesión retiene los tokens originales de los hechos confirmados en esa sesión
para repetir cada fila, además del replay del último hecho. No se vuelve a firmar
una identidad histórica arbitraria; los tokens V1 originales siguen siendo
válidos conforme a su política existente. Cambiar de partida limpia estas
referencias de sesión, sin borrar el historial persistido de la anterior.

Los mensajes distinguen XP, cinco monedas, NO_REWARD y replay sin nueva
acreditación. Una respuesta POST inválida no muestra avisos anteriores de éxito.
Errores de entrada/importe responden 400; acceso, 403; conflicto o integridad,
409; configuración, Bank operativo, SQL o bloqueo, 503. Los mensajes esperados
de Bank se traducen sin rutas, detalles privados ni trazas. Ningún error se
convierte en NO_REWARD ni provoca reparación automática.

GET no crea usuarios, Wallets, movimientos ni recompensas. Puede guardar en la
sesión local las identidades de formularios que emite, como en los pasos previos;
esto se distingue de las escrituras económicas. Los snapshots V1 no se reescriben.

### Evidencia HTTP y reproducción

Tres tests padre nuevos ejecutan nueve casos HTTP en subprocesos con SQLite
temporal file-backed default, backend protegido y 0004 aplicada únicamente allí.
Otro test padre comprueba lectura no aprovisionada sin escrituras ni llamadas
Bank sobre persistent_fixture. La ejecución focalizada completó cuatro tests
padre en 28,981 s, sin fallos ni omisiones; los nueve casos hijos se contabilizan
separadamente, no se suman de nuevo como tests padre.

Se prueban CSRF real, campos/token manipulados, dos sesiones y cambio de partida,
escape HTML, ausencia de filtraciones, API Bank real, PRG, convivencia V1/V2,
Gamer, reapertura de SQLite, errores Bank/configuración, Wallet ausente y causas
alteradas. Un bloqueo real devuelve 503 tras 5,390 s; el reintento explícito y su
replay dejan un solo crédito. Dos hechos distintos dejan saldo 10; repetir el
primero conserva saldo histórico 5 y no crea un tercer movimiento.

El runner completo de dos fases se ejecutó de nuevo con
`python manage.py test --settings=apps.ecomotor.target_persistent_demo_settings`:
**1297 tests habituales en 183,161 s, sin fallos y con dos omisiones heredadas
por symlinks de Windows**, y **114 tests persistentes en 417,490 s, sin fallos
ni omisiones**. Los tests padre persistentes incluyen seis casos hijos del
arnés Bank/default, dos de esquema nuevo/histórico 0004, veinte del servicio
monetario 2C y nueve HTTP 2D; estos recuentos hijos no se suman al del runner.
En esa ejecución el timeout HTTP real fue de 5,469 s. Se conservan el runner y
todos los tests heredados. Una ejecución inicial dentro del sandbox encontró
permisos insuficientes en directorios temporales; se repitió con el acceso
necesario, sin cambiar ni omitir pruebas para evitar esos errores.

Check normal/exclusivo, makemigrations --check --dry-run en SQLite temporales
(incluida la exclusiva ya migrada), los 16 enlaces/anclas del contrato y
git diff --check pasan. Los siete hashes SHA-256 protegidos se conservan.

La revisión visual real en Chrome, escritorio y viewport móvil de 390 × 844,
utiliza exclusivamente un servidor y SQLite temporales. Confirma Wallet no
aprovisionada, crédito, saldo acumulado, replay histórico y tablas con
desplazamiento horizontal. No se migra ni prueba manualmente la SQLite personal.

Para la revisión posterior en VS Code se mantienen settings, comando de arranque
y URL de la sección 1. La aplicación de 0004 a una SQLite personal requiere antes
copia de seguridad y validación controlada; esta PR no ejecuta ese procedimiento.
Con el entorno preparado: iniciar partida, usar el tercer botón, consultar el
apartado DuckyBank, generar otro hecho y repetir el primero desde su fila.
Verificar saldo actual 10 y saldo histórico 5; probar challenge y visit sin
cambiar reglas ni combinar efectos. Sigue siendo un laboratorio sintético,
sin F2-A productivo, Core, juegos, USE-01B, TRACE-01B ni Rewards–Duckies.
