# DEMO-REWARDS-XP-01 · Paso 4: Rewards y XP sintéticos persistentes

Aprobado **internamente por Equipo 5 / 02C-2 el 22/10/2026**, implementado para
revisión 01B desde develop `510886ffdf19309991f385d26d59ba221172fd73`.
DAR3 conserva autoridad funcional. No implementa F2-A productivo, autorización
USE-01B, procedencia productiva TRACE-01B ni integración Core/juegos.

## Alcance y datos ficticios

En el Paso 4 se amplió `apps.ecomotor_target_demo` (ruta histórica).
CONSOLIDACIÓN-A-01 sitúa ahora el paquete en
`apps.ecomotor.ecomotor_target_demo`, sin cambiar el label Django
`ecomotor_target_demo`, sus migraciones ni los contratos Rewards. Se conserva su SQLite
`instance/target_persistent_demo.sqlite3`, en la misma ruta y entorno de los
[Pasos 2](ecomotor-target-persistent-demo-v1.md) y
[3](ecomotor-target-playable-persistent-demo-v1.md). Demo #94, backend/settings,
protecciones de apertura y runner de dos fases permanecen intactos.

Dos actividades cerradas: desafío ficticio completado (`challenge`) propone
700 XP; visita ficticia al archivo (`visit`) no coincide con una regla y produce
NO_REWARD. No hay efectos ficticios de cantidad cero. Los importes, reglas y
hechos no son baremos aprobados por Óscar ni actividades de juegos reales.

`reward_demo_rules.py` construye RewardIdentity y ValidatedRewardFact y declara
RewardRuleSet `demo-rewards-rules-v1`, con RewardRule `demo-challenge-700-v1` y
ProposedEffect XP700. `reward_demo_services.py` llama realmente a
`semantic_fingerprint()` y `evaluate_reward()`, y conserva RewardDecision.
[Rewards F1-A](rewards-v0.md) sigue siendo evaluación/huella pura: no autentica
emisores, persiste ni concede. Su contrato global candidato no se modifica.

Solo se admite cero efectos o un único efecto XP positivo representable. Monedas,
objetos, puntos directos o efectos adicionales rechazan íntegramente la operación.
Un error nunca equivale a NO_REWARD. APPLIED solo se devuelve tras confirmar XP;
NO_REWARD es un hecho válido evaluado y registrado sin XP ni evolución.

## Identidad, tiempo y clave causal

Identidad F1-A `(origin_code, fact_id, recipient_id)`:

- Origen fijo servidor `persist-demo-rewards`.
- fact_id: 32 hex aleatorios, identidad estable de una actividad concreta.
- Destinatario `demo-progress:<PK exacta>`; correspondencia uno a uno con la FK
  progress dentro de esta SQLite. No representa User/Core.
- Hecho versionado `demo-fact-v1`, contexto sintético fijo y resultado cerrado.
- Token firmado con salt exclusivo, ligado a partida/hash de secreto de sesión,
  actividad, fact_id e instante UTC original con microsegundos. El mismo formulario
  conserva occurred_at; no se regenera en el reenvío. No vencimiento propio para
  demostrar replay tras reinicio; requiere sesión y firma vigentes del servidor.

Huella SHA-256 `rewards-semantic-v1`, calculada por F1-A incluyendo el instante
original. La huella compara contenido y no sustituye identidad ni autenticación.
Misma identidad con otra huella es conflicto, sin nueva recompensa.

La clave XP de 32 caracteres es `rx1:` más los primeros 28 hex SHA-256 de un JSON
ordenado de `[demo-reward-xp-key-v1, origen, fact_id, destinatario]`. Codificación
versionada sin concatenaciones ambiguas; depende de identidad, nunca de huella.
El prefijo con dos puntos no puede confundirse con las claves directas hex32 del
Paso 2. Se comprueba causalidad; una colisión o XP de este namespace sin RewardEvent
coherente se rechaza como integridad, sin reconstruir o premiar automáticamente.
El truncado no acredita imposibilidad matemática de colisiones: se rechazan las
contradicciones observables y existe unicidad por partida/clave.

## Modelo y migración locales

Único modelo nuevo `DemoTargetRewardEvent`, BigAutoField. Migración
`ecomotor_target_demo.0003_synthetic_rewards`, dependiente exclusivamente de
`0002_playable_configurations`; solo CreateModel y constraints, sin RunPython.

FK progress PROTECT; origin_code/recipient_id Char64, fact_id Char32,
activity_type Char32, occurred_at DateTime; fingerprint_version Char32 y huella
Char64; rule_set_version/matched_rule_id Char64 (esta última nullable); status
Char16; reason_codes y snapshot JSON; xp_amount PositiveBigInteger; xp_event
OneToOne nullable PROTECT; confirmed_at de servidor.

Unicidad `(progress, origin_code, fact_id)` equivale a la terna lógica porque el
servicio exige recipient_id derivado inequívocamente de progress. OneToOne evita
reutilizar una causa XP para dos recompensas. APPLIED exige XP>0 y causa; NO_REWARD
exige XP0 sin causa. Checks de estado, rango SQLite 0…2⁶³−1, identidades no vacías,
formato hexadecimal completo de fact_id/huella. Las comprobaciones regex SQLite
usan la función REGEXP registrada por Django. max_length se valida en la capa de
servicio/F1-A; no se atribuye a SQLite su aplicación automática. Las relaciones
entre tablas y la semántica JSON se comprueban en servicio. PROTECT es política
local de demo, sin decidir conservación productiva ni permisos Core.

## Una única transacción

Se extrae de services.py el núcleo privado `_grant_xp_in_transaction(context,
amount=..., operation_key=...)`. No abre/termina transacciones ni valida tokens
HTTP por su cuenta. Solo admite el contexto exacto y vivo emitido por el propietario
privado `_xp_transaction`, con ContextVar local a hilo/contexto y referencias a
conexión y bloque atomic exterior. El propietario comprueba el alias/archivo protegido antes de atomic; el núcleo
comprueba conexión y contexto exactos, autocommit desactivado, conexión nativa en transacción, IMMEDIATE y exactamente
el bloque exterior esperado. Un atomic arbitrario, savepoint anidado, contexto
inventado o contexto finalizado no es suficiente.

`grant_demo_target_xp()` conserva firma, token XP propio, validación, rechazo de
transacciones envolventes, replay/conflictos y DemoGrantResult. Usa el mismo núcleo
bajo su propia frontera exterior. No hay cambios a la XP V1/S3. El núcleo recarga
la partida, valida catálogo congelado/A1.1, estado, límites SQLite y cadena de
historial y delega el cálculo en A2.1/A1.2, igual que el Paso 2.

`apply_demo_reward(progress, activity=..., fact_token=..., session_token=...)`:

1. Valida hecho firmado y sesión, abre una única atomic exterior IMMEDIATE.
2. Recarga pertenencia, historia Rewards/XP y resuelve primero identidad existente.
3. Replay compatible devuelve snapshots originales sin evaluar reglas actuales,
   recalcular progresión ni escribir. Huella distinta produce conflicto.
4. Si es nueva, valida catálogo/estado y evalúa F1-A; rechaza efectos no soportados.
5. APPLIED invoca el núcleo XP en la misma conexión/transacción; NO_REWARD no lo llama.
6. Guarda RewardEvent y contrasta resultado con causas/tablas reales antes del commit.

XP, progreso, seis cruces para 0→700 y RewardEvent se confirman o revierten juntos.
No hay commits parciales, select_for_update ni reintentos automáticos. Fallos de
BD, integridad, sesión, configuración o bloqueo son errores explícitos; timeout5s.
No se escribe sobre configuraciones jugables ni sobre otra app.

## Historial, resultados y límites

Resultado frozen/slots `DemoRewardResult`: identidad, actividad/instante, estado,
huella/versiones, RewardDecision y motivos, XP, IDs XP/evolución, progresión completa
inmutable y replay separado del snapshot original.

Snapshot `demo-reward-result-v1`: identidad/instante/huella, propuesta histórica,
versiones/motivos, estado/importe, catálogo técnico/lógico exacto, IDs causales y
XP/niveles/épocas antes/después, todos los cruces/desbloqueos. NO_REWARD conserva
el ancla XP anterior (o ausencia inicial) para contrastar su observación original
sin utilizar el total actual. No se fabrica una evolución inicial ni una octava época.

Se valida F1-A de la propuesta histórica, identidad/huella, propiedad y catálogo,
causa XP real, cantidad, clave determinista, evoluciones reales y cadena de XP;
se compara estrictamente el JSON esperado con el almacenado. Causas ausentes,
ajenas, huérfanas o snapshots contradictorios rechazan; no reparación automática.
Las reglas actuales no reinterpretan decisiones confirmadas. No existe protección
criptográfica de tablas ante un administrador capaz de reescribir toda la historia;
la observación de coherencia no prueba autorización funcional ni origen real.

`read_demo_rewards()` verifica sesión y devuelve historia inmutable, sin escrituras.
`issue_reward_fact()` solo emite identidad firmada; no confirma el hecho en BD.

## HTTP, reproducción y pruebas

Misma página, CSRF real, solo GET/POST, rechazo de extras/duplicados, escape y
POST/Redirect/GET. No importes, origen, destinatario, reglas o instante enviados
como autoridad. Los formularios solo transportan actividad cerrada y token servidor.
La sesión conserva tokens pendientes y anterior para replay; tras éxito emite
una identidad nueva. Iniciar otra partida no borra el historial anterior.

```powershell
New-Item -ItemType Directory -Force instance | Out-Null
py manage.py migrate --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py seed_persistent_target_demo --settings=apps.ecomotor.target_persistent_demo_settings
py manage.py runserver 127.0.0.1:8002 --settings=apps.ecomotor.target_persistent_demo_settings
```

Abrir http://127.0.0.1:8002/demo/objetivo-persistente/. Crear partida, completar
el desafío, observar XP700/nivel8/seis evoluciones/APPLIED, repetir el mismo hecho,
registrar visita NO_REWARD y repetirla. Configurar Gamer. Reiniciar Django con
cookies/SECRET_KEY conservadas: recuperar todos los registros y resultados originales.
La limpieza exclusiva de la SQLite sintética sigue el contrato del Paso 2.

Los tests amplían demo_tests.py, preservando los Pasos 2/3 y el runner de dos fases:
F1-A, identidad/instante, estados, mezcla XP directa, replay sin reglas actuales,
conflicto, claves/causas, snapshots manipulados, rollback en cada fase, una sola
transacción, sesión/HTTP/CSRF, reapertura y concurrencia file-backed con conexiones
independientes, incluido timeout5s. Resultados reales, omisiones y comprobación
visual/reinicio se entregan en la PR; no se afirman ejecuciones anteriores como nuevas.

No F2-A productivo, Wallet, ItemGrant, RewardLimitUsage, User/Core, juegos reales,
Rewards global, USE-01B/TRACE-01B productivos ni activación objetivo. Siguen pendientes
los contratos externos y valores oficiales de Óscar. S3 V1 permanece intacto.
