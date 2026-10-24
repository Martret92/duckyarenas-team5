# REW-MULTI-03-DOC-01 · Contrato de Rewards combinado V4

## 1. Estado, autoridad y fuentes

**REW-MULTI-03-ARQ-01, ratificada internamente por Equipo 5 en 02C-2 el
24/10/2026.** El corte documental original #114 describía una ampliación futura.
3A/0006 está integrada por #115. Sobre la baseline
`f88f9be0ba09fad80224de0106cf6d9dc285fcc8`, 3B implementa el servicio y lector V4
para revisión, con REW-MULTI-03-V4-01 ratificada internamente en 02C-2 el
24/10/2026. En aquel corte HTTP combinado seguía pendiente de 3C. El corte y las
pruebas de 3B se registran en [§14](#14-corte-3b--servicio-y-replay-v4).
Sobre #116 integrada, 3C implementa ahora HTTP para revisión en Draft, con
REW-MULTI-03-3C-ARQ-01 ratificada internamente en 02C-2 el 24/10/2026;
su alcance y evidencias se registran en [§15](#15-corte-3c--http-combinado-v4).
DAR3 conserva autoridad funcional. Sus requisitos de identidad/origen, no premiar
dos veces y registro se recogen en [Rewards v0](rewards-v0.md); no atribuyen a
DAR3 las cantidades, claves, esquema o transacción definidos aquí. El original
DAR3 no se ha localizado en el repositorio durante esta revisión documental.

Se conservan R1–R8, T1–T8 y los cortes REW-MULTI-01/02 del
[registro de decisiones](../decisions.md). La aprobación es interna, sin
ratificación externa de Óscar, Core, Fernando o Henry. La modalidad combinada
extiende deliberadamente la exclusividad anterior para una actividad nueva;
las exclusiones de los contratos históricos describen correctamente sus cortes.

Antecedentes: [persistencia XP](ecomotor-target-persistent-demo-v1.md),
[Rewards XP/V1](ecomotor-target-demo-rewards-xp-v1.md),
[Bank/V2](ecomotor-target-demo-rewards-bank-v1.md) y
[Duckies/V3](ecomotor-target-demo-rewards-duckies-v1.md).
Sus pruebas históricas no son ejecuciones de DOC-01 ni prueban la combinación.

## 2. Baseline y hechos comprobados estáticamente

Baseline del corte DOC-01: `develop` en
`8552c54ec1446ccd0e472eda6fdf9632584b2e82`, con #113 integrada.
El laboratorio reside en `apps/ecomotor/ecomotor_target_demo/`, conserva label
`ecomotor_target_demo` y usa exclusivamente
`instance/target_persistent_demo.sqlite3` con sus settings independientes.

Los [tipos F1-A](../../apps/ecomotor/reward_types.py) admiten una secuencia
ordenada de efectos. [evaluate_reward](../../apps/ecomotor/reward_rules.py)
selecciona una regla, sin autenticar, persistir ni conceder. No se necesitan
tres reglas coincidentes: eso sería ambiguo, no una propuesta multiefecto.
En aquel corte el [coordinador](../../apps/ecomotor/ecomotor_target_demo/reward_demo_services.py)
rechazaba más de un efecto. Los [modelos](../../apps/ecomotor/ecomotor_target_demo/models.py)
y [0005](../../apps/ecomotor/ecomotor_target_demo/migrations/0005_rewards_duckies_schema.py)
permitían cuatro resultados excluyentes. Después, #115 amplió únicamente el CHECK
con [0006](../../apps/ecomotor/ecomotor_target_demo/migrations/0006_rewards_combined_schema.py).
3B añade una rama V4 cerrada al coordinador, sin modificar esa migración.

Los [servicios XP](../../apps/ecomotor/ecomotor_target_demo/services.py) ya ofrecen
un núcleo privado sin commit y un exterior controlado. [isolation.py](../../apps/ecomotor/ecomotor_target_demo/isolation.py)
y el [backend](../../apps/ecomotor/ecomotor_target_demo/db_backend/base.py)
protegen archivo efectivo, alias, enlaces y sustitución; la apertura normal
`mode=rw` no crea una SQLite ausente. Solo la migración explícita puede crearla.
No se cambia ese contrato ni se opera sobre SQLite personales en DOC-01.

## 3. Modalidad ratificada y compatibilidad

| Concepto | Valor cerrado del laboratorio |
| --- | --- |
| Actividad | `combo_challenge` |
| Versión del hecho | `demo-fact-v4` |
| Versión de reglas | `demo-rewards-rules-v4` |
| Regla | `demo-combo-challenge-v4` |
| Propuesta ordenada | XP 700 → DUCKYCOINS 5 → ITEM 1 |
| Resultado | Un `APPLIED`, un RewardEvent y tres causas reales |
| Snapshot | `demo-reward-result-v4` |
| Mapeo y artículo | `demo-item-map-v1`, `demo-reward-hint-v1` |

`demo-fact-v4` es la versión, no el `fact_id` único de una ocurrencia.
Importes y nombres son ficticios, no baremos oficiales aprobados por Óscar.
HINT consumible, cantidad 1, `item_level=None`, activo para una concesión nueva.
El servidor resuelve el mapeo histórico inmutable; fixtures o preparación aislada
explícita aportarán el Item. Rewards no crea ni repara artículos o catálogos.

`challenge`, `coin_challenge`, `item_challenge` y `visit` mantienen respectivamente
XP, monedas, objeto y NO_REWARD. Conservan sus constructores, tokens, versiones
de hecho/reglas, motivos y lectores existentes. V1/V2/V3 no reciben nuevas claves
JSON; nuevos hechos de actividades anteriores tampoco se convierten en V4.

## 4. Identidad, huella y autorización sintética

Una sola identidad Rewards: `(origin_code, fact_id, recipient_id)`, construida
por servidor para la partida propietaria de sesión. Se conserva la correspondencia
local `recipient_id=demo-progress:<PK exacta>` y origen sintético
`persist-demo-rewards`; esto no autentica emisores de juegos ni usuarios Core.
El navegador no determina User, Wallet, Ducky, Item, destinatarios o importes.

La [canonización F1-A](../../apps/ecomotor/reward_identity.py) y
`rewards-semantic-v1` permanecen intactas. El hecho original, incluido
`occurred_at` firmado, es estable ante reenvíos. La huella semántica contrasta
contenido; no sustituye identidad, autorización ni claves propietarias.

**REW-MULTI-03-V4-01, ratificada internamente en 02C-2 el 24/10/2026:** la propuesta
de DOC-01 queda concretada en resultado `{"completed":true}` y contexto exacto:

```json
{"demo":"REW-MULTI-03","fact_version":"demo-fact-v4","mapping_version":"demo-item-map-v1","item_code":"demo-reward-hint-v1"}
```

No campos adicionales o valores dinámicos. El token firmado contiene exactamente
ocho campos: `progress` (PK entera exacta), `owner` (SHA-256 hexadecimal del
secreto de sesión), `activity=combo_challenge`, `fact_id` (32 hex minúsculos),
`fact_version=demo-fact-v4`, `occurred_at` (UTC ISO 8601, seis microsegundos y
sufijo `+00:00`), `mapping_version=demo-item-map-v1` e
`item_code=demo-reward-hint-v1`. No incluye result/context, User/Wallet/Ducky/Item,
cantidades, saldos o XP actual. El servidor construye la semántica cerrada.

Se reutilizan `signing.dumps(payload, salt=SALT)` y `signing.loads(token, salt=SALT)`,
con el SALT histórico exacto `ecomotor.persistent-demo.reward-fact.v1`, sin salt
V4 nuevo ni vencimiento propio. El propósito sigue separado de XP directa y
opciones jugables. Una segunda decodificación exclusiva de V4 rechaza claves JSON
duplicadas que el lector estándar colapsaría; no cambia el lector de tokens
V1/V2/V3. Tipos estrictos, firma, propietario, partida, ocho claves exactas,
actividad, versión, mapeo, código y fecha canónica se validan en servidor; bool
no es PK entera. Campos ausentes/adicionales, mayúsculas en fact_id, zona/formato
incorrectos o tokens cruzados se rechazan. No son requisitos DAR3 ni ratificación
externa; se conserva `rewards-semantic-v1` sin modificar su canonicalizador.

Misma identidad y huella compatible recupera el resultado confirmado; otra huella
es conflicto sin escrituras. No se genera otra identidad o clave para eludirlo.
Replay se resuelve antes de reglas actuales, aprovisionamiento o concesiones.
Las unicidades Rewards y de los ledgers son complementarias.

## 5. Propuesta F1-A y validación completa

Una única regla V4 debe producir exactamente, en este orden:
`ProposedEffect("XP", 700)`, `ProposedEffect("DUCKYCOINS", 5)`,
`ProposedEffect("ITEM", 1)`. Es una propuesta hasta el commit exterior.
El servicio comprobará actividad, versiones, regla, elegibilidad y tipos enteros
exactos; rechazará efectos ausentes, adicionales, duplicados, reordenados,
cantidades distintas o tipos no soportados. No conservará solo el subconjunto
válido ni convertirá errores en NO_REWARD. ITEM en actividades antiguas sigue
rechazándose conforme a sus contratos.

## 6. Tres claves y contratos propietarios

Cada array contiene los valores originales de la misma identidad, en ese orden.
JSON compacto (`separators=(",", ":")`), codificado en UTF-8 y SHA-256:

| Clave | Array de entrada | Serialización y digest |
| --- | --- | --- |
| `rx1:` | `["demo-reward-xp-key-v1", origin_code, fact_id, recipient_id]` | `sort_keys=True`, `ensure_ascii=True`, `allow_nan=False`; primeros 28 hex, longitud total 32 |
| `rb1:` | `["demo-reward-bank-key-v1", origin_code, fact_id, recipient_id]` | `sort_keys=True`, `ensure_ascii=True`, `allow_nan=False`; 64 hex, longitud total 68 |
| `ri1:` | `["demo-reward-item-key-v1", origin_code, fact_id, recipient_id]` | `ensure_ascii=False`, `allow_nan=False`, sin normalización Unicode; 64 hex, longitud total 68 |

No se unifican codificaciones, payloads, namespaces o longitudes. No dependen
de fingerprint, importes, reglas actuales, saldo, inventario, PK Rewards o
posición del efecto. El truncado XP no prueba imposibilidad de colisiones;
una causa incompatible se rechaza, sin adoptar o regenerar claves.

XP utiliza `_grant_xp_in_transaction()` y un DemoTargetXPEvent con clave `rx1:`;
unicidad `(progress, operation_key)`, longitud 32. Se comprueban catálogo exacto,
importe, cadena histórica y cada evolución realmente causada.

Firma pública comprobada en [Bank](../../apps/bank/services.py):

```python
credit_coins(user, amount, *, source, operation_key, issuing_entity="Ecomotor",
             reference_type="", reference_id="", description="")
```

Para combo: amount=5, source=`persist-demo-rewards`, issuing_entity=`EcomotorDemo`,
operation_key=reference_id=clave `rb1:` completa,
reference_type=`demo_reward_fact_v1`, description vacío. Debe devolver
`LedgerResult(transaction, created=True)`; tipo de Transaction REWARD.
La idempotencia [bancaria](../../apps/bank/models.py) es `(wallet, operation_key)`.
Se verifican fila persistida, User/Wallet, importe, saldo anterior/posterior,
metadatos, fingerprint bancario y fecha. La canonización de ese fingerprint
bancario es distinta de la derivación `rb1:` y no se sustituye por ella.

Firma pública comprobada en [Duckies](../../apps/duckies/services.py):

```python
grant_item(user, item, quantity, operation_key, *, item_level=None,
           reference_type="", reference_id="")
```

Cantidad 1, variante nula, operation_key=reference_id=clave `ri1:` completa,
reference_type=`demo_reward_item_v1`. Devuelve ItemGrant, también en replay;
no ofrece indicador `created`. Su [unicidad](../../apps/duckies/models.py) es
`(ducky, operation_key)`, límites 255/50/255 para clave/tipo/referencia.
El coordinador debe descartar causas previas y verificar que la entrega es
nueva, persistida y coherente, incluido incremento real de inventario en uno.
No existe FK directa ItemGrant→InventoryItem. Comparar solo hash o PK no verifica
User, Ducky, Item, variante, cantidad y referencias.

## 7. Aprovisionamiento y propietarios

Solo para una operación nueva válida: reutilizar el synthetic_user exclusivo
de la partida o crear cuenta sintética inactiva, sin privilegios, información
personal ni contraseña utilizable, con Wallet inicial cero. Si un User ya
vinculado carece de Wallet, abortar; no reparar o reiniciar saldos.
Reutilizar Ducky compatible del mismo User o crear el mínimo con sexo válido y
selected_outfit=None cuando la historia no exija uno anterior desaparecido.
No perfil V1 ni initialize_ducky; no usuarios/Wallet/Ducky compartidos entre
partidas. Token, lectura y replay no aprovisionan. El Item nunca se crea aquí.

Bank conserva saldo/Transaction y Duckies inventario/ItemGrant. Se usan sus APIs
públicas para acreditar y entregar; no se duplican ledgers ni se modifica su
código. Configuraciones Gamer/Romano y atributos no reciben cambios por combo.

## 8. Una transacción exterior y rollback conjunto

Rewards conserva `_xp_transaction(progress, session_token=...)` sobre el
`default` protegido real: misma base, alias y conexión nativa para los tres
efectos, SQLite IMMEDIATE, timeout cinco segundos. Se valida aislamiento y
sesión/token antes de entrar; el exterior comienza antes de leer estado mutable.

```text
identidad → evaluación → XP → Bank → Duckies → RewardEvent/V4
         → verificación causal → commit exterior
```

1. Recargar progreso e historia propietaria; resolver replay o conflicto primero.
2. Para identidad nueva, validar catálogo congelado exacto, progresión, regla y
   propuesta completa; comprobar claves y ausencia de causas huérfanas/cruzadas.
3. Conceder XP700 mediante el núcleo privado existente y verificar XPEvent y
   evoluciones reales. No llamar al servicio público XP que abre otro exterior.
4. Aprovisionar/reutilizar User/Wallet y llamar a credit_coins; verificar
   LedgerResult.created=True, Transaction persistida y saldo resultante.
5. Aprovisionar/reutilizar Ducky, verificar mapeo/Item e inventario representable
   y llamar a grant_item; verificar entrega nueva e incremento real unitario.
6. Guardar un único APPLIED enlazado a las tres causas y su V4; releer/contrastar
   toda la causalidad y confirmar únicamente al salir correctamente del exterior.

Los atomic internos propietarios son savepoints en ese mismo default, sin commit
autónomo. `_check_xp_transaction()` exige el exterior exacto: se comprueba antes
y después de las llamadas, nunca dentro de un savepoint Bank/Duckies.
Sin BEGIN manual, otra transacción envolvente, alias auxiliar, autocommit
incompatible, reintentos automáticos o I/O externo. select_for_update no es
garantía de bloqueo por fila en SQLite.

Fallo antes/después de cualquier efecto, guardado o comprobación final revierte
el conjunto: aprovisionamiento User/Wallet/Ducky, XP/progreso/evoluciones,
saldo/Transaction, inventario/ItemGrant y RewardEvent. No éxito antes del commit.
En DOC-01 la atomicidad combinada quedó pendiente de demostración empírica en 3B;
la evidencia propia de 3B se recoge en §14. Las pruebas individuales anteriores
no sustituyen esa demostración. No se promete atomicidad
distribuida ni se cambian backend, Bank, Duckies, Core o S3 para conseguirla.

## 9. Futura migración 0006

El diseño siguiente corresponde a DOC-01 y quedó implementado por #115/3A,
incluidas instalación nueva, copia física 0005→0006 y conservación V1/V2/V3.
3B no cambia el esquema. `ecomotor_target_demo.0006`, sucesora estricta
de `0005_rewards_duckies_schema`. Conservar xp_event, bank_transaction e
item_grant: OneToOne nullable/PROTECT. Sin tablas adicionales o ledgers duplicados.
Sustituir únicamente `demo_reward_outcome_valid` para admitir estas cinco ramas:

| Resultado | XP / xp_event | coin_amount / bank_transaction | item_grant |
| --- | --- | --- | --- |
| APPLIED XP individual | >0 / presente | 0 / NULL | NULL |
| APPLIED monedas individual | 0 / NULL | >0 / presente | NULL |
| APPLIED objeto individual | 0 / NULL | 0 / NULL | presente |
| APPLIED combinado | >0 / presente | >0 / presente | presente |
| NO_REWARD | 0 / NULL | 0 / NULL | NULL |

No se admite una combinación parcial de dos efectos ni otra rama. El CHECK solo
certifica forma local; servicio/lectores deben exigir combo_challenge, 700/5/1,
regla V4, tipos, versiones y pertenencia causal completa. No puede certificar
por FK/CHECK el importe de Transaction o cantidad/propietario de ItemGrant.
Se conservan unicidad Rewards, rangos SQLite, formatos de hashes y unicidades
OneToOne. Migración estructural sin RunPython, backfill, usuarios, hechos o
snapshots inventados; 0001–0005 y migraciones propietarias quedan intactas.

3A deberá probar instalación nueva y copia temporal poblada 0005→0006,
comparando columnas comunes, filas/IDs, JSON exactos V1/V2/V3, claves,
referencias, FKs, índices, constraints y triggers del catálogo. Repetir migrate
sin efectos de negocio, sin --fake ni operación sobre SQLite personales.

## 10. Snapshot V4 y replay histórico

Solo combo usa `demo-reward-result-v4`, con estas claves superiores exactas:

```text
schema, identity, activity_type, occurred_at, fingerprint_version, fingerprint,
status, rule_set_version, matched_rule_id, eligible, effects, reason_codes,
xp_amount, xp_event_id, evolution_ids, catalog, anchor_xp_event_id, progression,
coin_amount, bank, item
```

APPLIED, actividad/versiones/regla de §3, eligible=true y reason_codes=[];
effects=`[["XP",700],["DUCKYCOINS",5],["ITEM",1]]` en ese orden.
xp_amount=700, xp_event_id real; evolution_ids y progression reproducen los
cruces reales. anchor_xp_event_id es ese XPEvent, no un ancla estacionaria.
Catálogo original exacto. Desde cero con el catálogo sintético actual, XP700
alcanza nivel 8 y seis evoluciones; no crea una octava época.

coin_amount=5 y `bank` conserva exactamente los campos causales V2:
user_id, wallet_id, transaction_id, operation_key, transaction_type, amount,
balance_before, balance_after, source_platform, issuing_entity, reference_type,
reference_id, request_fingerprint y created_at originales.
`item` conserva los campos V3: mapping_version, item_code, user_id, ducky_id,
item_id, item_grant_id, item_level_id, category, consumable, quantity,
operation_key, reference_type, reference_id y created_at; mapeo/código históricos,
HINT/true/1, variante NULL y causa ri1 exacta. No reconstruir descripción o
actividad histórica desde valores mutables actuales del artículo.

Resultado inmutable con `replay` separado, nunca añadido al JSON persistido.
Progresión, saldo posterior y entrega son históricos; no representan XP, Wallet
o inventario actuales. Los lectores V1/V2/V3 y sus JSON se conservan exactamente.

El futuro lector V4 despachará por versión explícita y comprobará claves exactas,
tipos estrictos (bool no es ID/int), rangos, fechas y datos canónicos. Reproducirá
identidad/huella desde el hecho y contexto históricos versionados; comprobará
las tres claves y filas XP/evolución/Transaction/ItemGrant, mismo progreso,
catálogo y User sintético, Wallet y Ducky correctos, importes/referencias y
snapshot completo. Rechazará efectos ausentes, extra, duplicados, cruzados o
contradictorios y versiones desconocidas.

Replay no reevaluará reglas actuales, recalculará premios, aprovisionará o
llamará a escritores XP/Bank/Duckies, compras, equipamiento o consumo; no hará
INSERT/UPDATE/DELETE de negocio. No exigirá igualdad con XP/saldo actuales ni
existencia de InventoryItem o posesión del HINT. Debe funcionar tras gastar
monedas, consumir el HINT y ganar XP adicional, conservando las tres causas.

## 11. Errores, causas huérfanas y concurrencia

Separar entrada/token inválido, sesión/partida/destinatario no autorizados,
conflicto de huella, regla/combinación no soportada, Item no preparado/inactivo/
incompatible, identidad sintética incoherente, causa huérfana/cruzada, fallo de
XP/Bank/Duckies, guardado/verificación Rewards, snapshot corrupto y fallo de
alias/conexión/bloqueo/timeout SQLite. Ninguno equivale a NO_REWARD o éxito.

Verificar por namespace las causas rx1/rb1/ri1 confirmadas de esa identidad y
destinatario. Una causa previa sin RewardEvent coherente no se adopta aunque
la API propietaria pudiera recuperarla; tampoco se reparan causas ausentes o
intercambiadas. El hash no garantiza por sí solo causalidad o autenticidad.
No se promete protección ante administradores capaces de reescribir la historia.

Concurrencia debe serializarse mediante IMMEDIATE o fallar de forma controlada,
sin efectos parciales. Reintento posterior explícito: misma identidad original,
nueva transacción y verificación del estado confirmado, sin retry automático.
Los códigos HTTP definitivos corresponden a 3C respetando manejadores existentes;
DOC-01 no fija una nueva política HTTP ni expone SQL, tokens, secretos o rutas.

## 12. Aceptación pendiente por fases

Estas pruebas están **planificadas, no ejecutadas en DOC-01**:

| Fase | Evidencia exigida |
| --- | --- |
| 3A, esquema | Instalación limpia 0006 y actualización poblada 0005→0006; cinco ramas válidas y rechazo de combinaciones parciales/inconsistentes mediante INSERT/UPDATE; preservación exacta V1/V2/V3, IDs, claves, referencias, unicidades, FKs, índices y triggers; sin backfill o cambios históricos. |
| 3B, efectos | Un RewardEvent con tres causas reales, XP700/cruces pertinentes, crédito5/Transaction y HINT1/ItemGrant; configuraciones anteriores intactas. |
| 3B, transacción | Misma conexión nativa/default temporal protegido, savepoints y commit exterior único; fallos antes/después de XP, Bank, Duckies y al guardar/verificar Rewards revierten todo, incluido aprovisionamiento. |
| 3B, concurrencia | Conexiones independientes para hechos iguales, incompatibles y distintos; bloqueo y timeout reales de cinco segundos; retry explícito sin duplicación o efectos parciales. |
| 3B, historia | Conflictos, causas huérfanas/cruzadas, claves de otro destinatario, snapshots incompletos/extra/corruptos y tipos inválidos; replay tras gasto, consumo, XP adicional, reglas modificadas y reapertura, sin DML ni llamadas de concesión; regresiones estrictas V1/V2/V3. |
| 3C, HTTP | Formulario sintético cerrado, firma/sesión/CSRF, campos extra/duplicados rechazados, confirmación tras commit y PRG; historial con tres causas, replay último/por fila, histórico frente a estado actual, errores saneados y Client real aislado; revisión visual escritorio/móvil. |

3B/3C usarán subprocesos y default protegido real sobre archivos temporales
desechables, auditoría de aperturas y cierre/limpieza completos. Mocks aislados
no acreditan la combinación. Mantener runner normal/persistente y protección
de las siete rutas personales; ninguna base personal es fixture.

## 13. Secuencia, dependencias y exclusiones

**DOC-01 → 3A esquema → 3B servicio/V4 → 3C HTTP.** Cada PR requiere revisión y
fusión antes de iniciar la siguiente. DOC-01 no crea ramas de implementación.
El contexto/token de §4 quedó ratificado mediante REW-MULTI-03-V4-01 antes de 3B.

Continúan pendientes Core/A3.5; USE-01B; TRACE-01B; F2-A productivo; identidad,
autenticación y permisos globales del Equipo 0; contratos de hechos/emisores
reales; valores oficiales de Óscar; integración productiva con propietarios;
cualquier activación del escritor XP objetivo y recuperación distribuida entre
bases/conexiones independientes. S3 V1 permanece como único escritor XP V1 activo
fuera del laboratorio. F2-A productivo y la activación del escritor objetivo
continúan pendientes. El núcleo XP sintético del laboratorio no supone una
activación productiva.

Según información transmitida por el Equipo 5, Henry comunicó el 24/10/2026 su
intención de reutilizar Rewards–Duckies en una demo visual conjunta separada.
No constituye aprobación o prueba de recompensas combinadas por Henry. No se
modifican su rama/interfaz, Core, Bank, Duckies, Shop, V1, objetivo, settings o
backend. No economía oficial, juegos reales, nuevos endpoints, consumo o
equipamiento dentro de Rewards, tablas propietarias duplicadas o autorización
productiva. La revisión humana de este contrato precede a toda implementación.

## 14. Corte 3B · Servicio y replay V4

Implementación para revisión desde `f88f9be0ba09fad80224de0106cf6d9dc285fcc8`,
con #114/#115 integradas. V4-01 concreta §4; los apartados de DOC-01 y su plan
conservan su procedencia histórica. 3A ya está integrada; 3C no se implementa.

### Implementación y fronteras

`reward_demo_rules.py` añade únicamente la actividad interna, el constructor V4
cerrado y COMBO_RULE_SET. RULE_SET/ITEM_RULE_SET y las actividades HTTP anteriores
mantienen versiones y semántica. `reward_demo_services.py` conserva las firmas
públicas y DemoRewardResult frozen/slots: sus bloques Bank/Item existentes
permiten expresar las tres causas sin nuevos modelos, DTO propietarios o tablas.
SALT, `_xp_key`, `_bank_key` y `_item_key` permanecen exactos.

El coordinador valida la propuesta completa antes del primer efecto y comprueba
globalmente las tres claves preexistentes, sin adoptar causas. Reutiliza el
núcleo XP privado en el exterior existente; Bank devuelve LedgerResult.created
verdadero y Duckies se contrasta con ausencia previa y entrega persistida.
Se verifica el contexto antes/después de APIs propietarias, fuera de savepoints.
Guarda un APPLIED/V4 y relee toda su causalidad antes del único commit exterior.
El aprovisionamiento perezoso reutiliza las invariantes sintéticas existentes;
no crea Items, perfiles V1 o identidades durante token, consulta o replay.

El lector `_recorded_combo` es exclusivo de V4, sin evaluación actual ni consulta
de InventoryItem. Contrasta filas reales, claves/propietarios, huella histórica,
regla/efectos exactos, ancla XP y evoluciones. Compara canónicamente el JSON
completo reconstruido: claves omitidas/extrañas, bool como ID, floats, versiones
desconocidas, referencias contradictorias y modalidades cruzadas se rechazan.
También rechaza claves causales reutilizadas en otro destinatario. Las ramas
V1/V2/V3 siguen separadas; combo no puede presentarse como un resultado antiguo.

### Evidencia focalizada propia de 3B

El arnés [reward_combo_fixture.py](../../apps/ecomotor/ecomotor_target_demo/reward_combo_fixture.py)
configura default antes de django.setup, exige directorio temporal propietario
nuevo, audita toda apertura SQLite y conserva backend/IMMEDIATE/timeout5.
Solo migrate explícito crea el archivo; solo el fixture prepara el HINT.
El padre verifica configuración/conexión/registro de apps, hashes personales y
limpieza tras cerrar cada hijo. No se usa la partida personal como origen.

Ejecución focalizada: cinco padres y 16 casos hijos, sin fallos/errores/omitidos
en el pase final (53,137 s; hijos contabilizados aparte). Comprueba:

- Una recompensa, tres causas, claves exactas; desde XP0, XP700/nivel8/Siglo XX
  y seis evoluciones, Bank5 y HINT1. Reutilización de identidad e infraestructura
  previa, XP no inicial, monedas/inventario existentes y configuración Gamer.
- 36 variantes inválidas de token, incluido JSON duplicado; 12 propuestas
  incompatibles/ambiguas, sin efectos parciales. Recursos inválidos, ItemLevel,
  mapeo incompatible, overflow, exterior ajeno y frontera de alias rechazados.
- 84 corrupciones de snapshot y 26 corrupciones causales rechazadas; causas
  ausentes/cruzadas y namespaces huérfanos no se adoptan. Las referencias rotas
  se fabrican exclusivamente en el fixture desechable, se restauran y se vuelven
  a comprobar las FKs; no se cambia el backend ni el aislamiento.
- Traza real `BEGIN IMMEDIATE → SAVEPOINT → RELEASE → SAVEPOINT → RELEASE → COMMIT`.
  Orden de INSERT XP/Bank/ItemGrant/Reward, misma conexión nativa/default y
  recompensa no visible desde lector independiente antes del commit.
- 26 escenarios de rollback con infraestructura nueva y existente, incluido
  aprovisionamiento, evolución intermedia, antes/después de escritores,
  RewardEvent ya insertado, construcción V4 y validación final; todas las tablas
  regresan al estado anterior, sin transacciones abiertas o efectos parciales.
- Conexiones nativas independientes: hecho idéntico, identidad incompatible,
  hechos distintos, competencia con XP directa y con monedas individuales.
  Timeout real de 5,297 s y reintento explícito con misma identidad, sin duplicar.
- Replay sin DML, escritores, evaluación o consulta de inventario tras gastar
  monedas, equipar/consumir realmente el HINT en el fixture, ganar más XP,
  cambiar reglas actuales y reabrir SQLite; convivencia V1/V2/V3/V4. Consumo y
  equipamiento no forman parte del coordinador ni de HTTP.

El primer pase focalizado detectó dos defectos del arnés (clase esperada de
ambigüedad y restauración de updated_at al retirar una causa huérfana fabricada).
Se corrigieron sin cambiar F1-A/Bank ni relajar las comprobaciones; el pase final
incluye además variantes, causas ausentes y rollback intermedio ampliados.

### Regresión completa ejecutada en 3B

`python manage.py test --settings=apps.ecomotor.target_persistent_demo_settings --verbosity=1`
terminó con código 0 usando DemoRunner original de dos fases:

| Ámbito | Ejecutados | Correctos | Omitidos | Fallos/errores | Duración |
| --- | --- | --- | --- | --- | --- |
| Habitual | 1320 | 1318 | 2 | 0 | 180,421 s |
| Persistente, padres | 139 | 139 | 0 | 0 | 661,423 s |
| Casos hijos reportados | 105 en 36 informes | 105 | 0 | 0 | No se suman a los padres |

Las omisiones habituales corresponden a la limitación de privilegios Windows
para symlinks ya observada en el entorno; no se desactivan ni modifican pruebas.
Los 16 casos nuevos forman parte de esos hijos. La regresión incluye XP/opciones,
Rewards V1/V2/V3, consumo/replay Duckies, HTTP histórico y migraciones
0004/0005/0006, sin modificar sus fixtures o expectativas. El propio fixture V4
ejecutó Django check y makemigrations --check --dry-run exclusivamente contra su
default temporal: sin incidencias ni cambios de modelos/migraciones pendientes.
El timeout V4 observado en esta ejecución completa fue 5,313 s.

Todos los informes hijos confirmaron cierre y aperturas limitadas al archivo
temporal autorizado; el padre comprobó su eliminación y preservación de registro,
conexión/configuración propias. Las siete rutas personales conservaron existencia
y SHA-256. No migrate, seed, servidor o Django sobre una SQLite personal.

No se demuestra atomicidad distribuida ni autenticidad productiva de emisores.
Los snapshots no son certificados frente a administradores capaces de reescribir
toda la base. Revisión humana y fusión de 3B preceden a cualquier trabajo 3C;
no cambia la autoridad DAR3, el contrato candidato F2-A o dependencias Core.

## 15. Corte 3C · HTTP combinado V4

### Autoridad y alcance

REW-MULTI-03-3C-ARQ-01 fue ratificada internamente por Equipo 5 en 02C-2 el
24/10/2026. Este corte implementa HTTP sobre develop
`a7be00162e68f4d20a963c65020a2b4559676a28`, con #114/#115/#116 integradas;
conserva como históricos DOC-01, 3A y 3B. Se prepara para revisión humana en
Draft, sin autorización productiva de Core, Óscar, Henry ni otros equipos.

No cambia el coordinador, reglas, lectores V1/V2/V3/V4, modelos, migraciones,
backend, settings, aislamiento, URLconf ni runner. S3 V1 permanece como único
escritor XP V1 activo fuera del laboratorio. F2-A productivo, USE-01B, TRACE-01B,
integración Core y activación del escritor objetivo siguen pendientes.

### Formulario, ruta y mensajes

La ruta sigue siendo `/demo/objetivo-persistente/`, nombre `persistent-demo`.
RewardDemoForm ofrece quinta actividad `combo_challenge`, con etiqueta exacta:

> Desafío combinado ficticio (+700 XP, +5 DuckyCoins y +1 HINT)

Mantiene exclusivamente `action=reward`, `activity` y `fact_token`, más CSRF.
El servidor emite el hecho firmado; no recibe importes, destinatarios, artículos,
IDs propietarios, reglas ni referencias como autoridad. Se conservan las cuatro
actividades individuales y los propósitos separados de XP/opciones/Rewards.

La vista invoca `apply_demo_reward()` existente y utiliza POST/Redirect/GET.
Solo tras retorno confirmado establece el aviso nuevo exacto:

> APPLIED: +700 XP sintéticas, +5 DuckyCoins ficticias y +1 HINT sintético concedidos en una única recompensa.

El replay devuelve 302 con el aviso exacto:

> Replay Rewards V4: resultado histórico recuperado (700 XP, 5 DuckyCoins y 1 HINT originales). No se ha vuelto a conceder ningún premio.

Se mantienen replay del último hecho y por fila, identidad/instante originales,
emisión de otro hecho después de confirmar y limpieza de tokens/avisos al iniciar
otra partida. Los errores eliminan el aviso previo; no confirman una recompensa
nueva ni se convierten en NO_REWARD.

### Historial y estado presente

Una fila por RewardEvent combinado presenta tres bloques, antes de las ramas
individuales: XP anterior/posterior, nivel y evoluciones con XPEvent; monedas y
saldo histórico con Transaction; HINT, cantidad histórica, código/mapeo con
ItemGrant. Incluye referencias causales originales y versión/regla V4.

El saldo actual procede de la consulta Wallet existente y la cantidad actual
del HINT de inventario. Gastar monedas, consumir el objeto o ganar XP adicional
no modifica el resultado histórico. No se promete atomicidad global entre las
consultas independientes de toda la página. La tabla permite desplazamiento
horizontal, foco visible y encabezados de columna accesibles.

### Seguridad y respuestas

La sesión propietaria y firma se comprueban en el coordinador existente, con
CSRF real y rechazo de campos extra, duplicados y ausentes. GET con parámetros
inesperados se rechaza; no se añaden endpoints, consumo o equipamiento HTTP.
La salida usa escape Django y mensajes controlados sin SQL, rutas o trazas.

| Situación | HTTP |
| --- | --- |
| Nueva recompensa confirmada o replay compatible | 302 |
| Formulario o parámetros inválidos | 400 |
| CSRF, token, sesión o pertenencia no autorizados | 403 |
| Método no admitido, superada la comprobación CSRF aplicable | 405 |
| Conflicto semántico o historia incoherente | 409 |
| Configuración, recursos obligatorios, BD o timeout | 503 |

### Excepción histórica y arnés 3C

La excepción complementaria de 02C-2 autoriza exactamente esta adaptación en
`reward_combo_fixture.py`, sin ningún otro cambio en ese archivo:

```diff
- self.assertNotIn("combo_challenge", dict(REWARD_HTTP_ACTIVITIES))
+ self.assertIn("combo_challenge", dict(REWARD_HTTP_ACTIVITIES))
```

La anterior aserción documentaba la ausencia HTTP durante 3B; su actualización
comprueba la publicación ratificada en 3C. No altera pruebas del coordinador.

El nuevo `reward_combo_http_fixture.py` usa Client real con CSRF, subproceso,
directorio temporal propio y default protegido file-backed. Configura antes de
django.setup(), audita todas las aperturas y migra/prepara HINT solo en el
temporal. Cinco padres nuevos se registran una sola vez mediante load_tests.
El padre verifica conservación de su conexión/configuración/registro de apps,
hashes personales y eliminación de temporales después de cerrar conexiones.

El pase focalizado final ejecutó cinco padres y 11 casos hijos: sin fallos,
errores ni omitidos, 51,680 s. Comprueba formularios extraídos del HTML, PRG,
una recompensa/tres causas, XP700/nivel8/seis evoluciones, Bank5 y HINT1; replay
original/último/por fila sin cambios de negocio y reapertura de SQLite.
Tras XP adicional real, gasto Bank y equipamiento/consumo Duckies en el fixture,
XP actual900/Wallet0/inventario0 conservan historia XP0→700/saldo5/entrega1.
Las operaciones de consumo/equipamiento siguen fuera de HTTP.

Incluye CSRF, campos cerrados, métodos, tokens alterados/cruzados, dos sesiones,
reinicio, escape y ausencia de filtraciones; 409 por conflicto/corrupción y 503
por recursos/configuración/BD. Tres fallos HTTP inyectados después de escrituras
reales Transaction/ItemGrant/RewardEvent revierten todas las tablas de negocio.
Contención real: 503 tras 5,313 s, sin efectos parciales; retry explícito y replay
posterior dejan una única recompensa. Las sesiones Django se distinguen de las
escrituras de negocio.

El primer pase focalizado falló en el propio test de métodos: CSRF rechazaba la
petición antes del 405. El pase final aporta CSRF válido para llegar a la vista;
la comprobación de sesión cruzada también usa CSRF del destinatario para probar
la autorización real. No se ha relajado ninguna protección de la aplicación.

La regresión 3B volvió a ejecutar cinco padres y 16 hijos, sin fallos/errores/
omitidos en 53,541 s: 26 escenarios de rollback, transacción única con savepoints,
causalidad, corrupción, concurrencia y timeout real de 5,329 s. Estos hijos no se
suman a los padres ni se presentan como nuevos casos HTTP.

### Revisión visual

Se inspeccionó en Chrome el HTML real obtenido por el test, con CSS local,
a anchos 375, 768 y 1280. Exportación inerte fuera del repositorio: tokens y
campos ocultos retirados, botones desactivados, sin formularios operativos ni
conexión Django/SQLite. Se comprobaron quinta etiqueta, aviso, tres bloques y
referencias; en móvil/tablet la tabla usa desplazamiento horizontal, con foco
visible y desplazamiento mediante teclado. Viewport restaurado al finalizar.
Se guardaron capturas locales. No sustituye una validación interactiva manual
de la demo montada; el flujo operativo se verificó mediante Client real.

### Regresión completa ejecutada en 3C

`python manage.py test --settings=apps.ecomotor.target_persistent_demo_settings --verbosity=1`
terminó con código 0 mediante el DemoRunner original de dos fases:

| Ámbito | Ejecutados | Correctos | Omitidos | Fallos/errores | Duración |
| --- | --- | --- | --- | --- | --- |
| Habitual | 1320 | 1318 | 2 | 0 | 191,659 s |
| Persistente, padres | 144 | 144 | 0 | 0 | 701,156 s |
| Casos hijos reportados | 116 en 41 informes | 116 | 0 | 0 | No se suman a los padres |

Los cinco padres/11 hijos HTTP nuevos están incluidos en esos totales, junto
con las regresiones 3B, XP, Bank, Duckies, configuraciones Gamer/Romano, HTTP
histórico y esquemas 0004/0005/0006. El timeout HTTP V4 en este pase fue 5,282 s;
su reintento explícito confirmó una sola recompensa, seguido de replay sin efectos.
No se han introducido omisiones. Una ejecución diagnóstica adicional de los dos
tests de symlink confirmó ambos skips por WinError 1314 (privilegio Windows),
sin modificar pruebas. La exportación visual repitió un padre/un hijo funcional;
tampoco se cuenta como caso nuevo ni se añade al total de la suite.

Django check y makemigrations --check --dry-run se ejecutaron exclusivamente
en los fixtures con default temporal protegido: sin incidencias ni cambios de
modelos/migraciones pendientes. Se verificaron 273 enlaces locales y anclas en
los tres documentos, diff sin errores de whitespace y alcance de diez archivos.
El arnés histórico conserva exactamente la sustitución de una línea autorizada.

Los 41 informes confirmaron conexiones cerradas y aperturas limitadas a su
archivo autorizado; tras concluir se comprobó también la ausencia física de las
41 SQLite reportadas. Las siete rutas personales conservan existencia y SHA-256.
No se abrió su contenido, migró, sembró, copió como fixture ni arrancó Django
contra ellas. El worktree independiente no se utilizó ni modificó.

La fase queda preparada para revisión en Draft, sin merge automático. La prueba
visual es del HTML inerte del fixture, no una sesión interactiva sobre la partida
personal. Se mantienen pendientes las validaciones humanas de 01B-2/02C-2 y las
dependencias productivas; este corte no activa ninguna integración global.
