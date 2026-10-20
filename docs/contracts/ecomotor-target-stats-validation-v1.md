# A4.1 · Validación pura de estadísticas objetivo · Contrato técnico v1

## 1. Autoridad, alcance y estado

A4.1-ATTR-01, BASE-01, BUDGET-01 y PURE-01, aprobadas internamente por Equipo 5
en 02C y documentadas el 21/10/2026 sobre develop
`0e960de432cc08d62933d8218586ae114dad9949`. DAR3 sigue siendo la fuente funcional
principal; ATR-OBJ-01 es nomenclatura interna E5. Aclaraciones del profesor no
aprueban por sí solas esquemas Django o configuración numérica.

[Decisiones](../decisions.md#a41--validación-pura-de-estadísticas-objetivo--21102026),
[opciones objetivo](ecomotor-playable-options-target-v1.md#3-opciones-y-estadísticas)
y [pendientes](../pending-decisions.md#25-a41--parámetros-y-dependencias-del-validador-objetivo).
Se desarrolla E-01/E-02 de 02C con ATR-OBJ-01 y se conserva OP-RED-01.
**Estado vigente del 21/10/2026:** implementación pura integrada mediante PR #74;
la referencia previa a revisión en 01B conserva su corte histórico.
A4.1-NUM-01 resuelve el dominio numérico básico que el corte documental de PR #73
mantenía pendiente. Firma y representación concretadas internamente en 01B;
no son reglas numéricas oficiales del profesor ni autorización adicional de Core.
Sin persistencia, modelos, migraciones o activación objetivo.
Se usa trazabilidad existente; no se afirma nueva consulta directa de PDFs.

## 2. Atributos exactos · A4.1-ATTR-01

| Código objetivo | Significado |
| --- | --- |
| ATK | Ataque |
| DEF | Defensa |
| VEL | Velocidad |
| INT | Inteligencia |
| LOG | Lógica |
| CUACK | Especial / Especialización |

CUACK es numérico, no identidad de una especialización tecnológica. No añadir
SPE como séptimo atributo ni usarlo en sustitución de CUACK en entradas objetivo.
No efectos especiales, atributos adicionales, multiplicadores o bonificaciones
por época aprobados por este contrato.

## 3. Entradas conceptuales y bases · A4.1-BASE-01

El componente recibe bases autorizadas de una opción, incrementos elegidos para
los mismos seis atributos y presupuesto autorizado de esa configuración.
La fuente confiable proporciona bases/presupuesto; el validador comprueba datos,
no demuestra que una configuración aportada esté funcionalmente autorizada.

- Bases e incrementos contienen **exactamente** las seis claves canónicas: sin
  ausencias, sobrantes o duplicados. No completar entradas con defaults.
- Bases, incrementos y presupuesto: **enteros Python exactos no negativos**,
  `type(value) is int` y `value >= 0`, según A4.1-NUM-01 aprobada internamente
  en 02C el 21/10/2026. Rechazar bool, float, Decimal, cadenas y cualquier otro
  tipo; sin conversión, redondeo, truncamiento ni completar ausencias.
- Sin máximos funcionales inventados ni límites técnicos de campos Django en
  esta capa pura. Bases y presupuesto oficiales siguen pendientes; no hay defaults.

### 3.1. API pura concretada en 01B

`validate_target_stats(bases, increments, *, budget: int) -> TargetStatsResult`

`budget` es obligatorio y explícito. Bases e incrementos aceptan exclusivamente
listas o tuplas explícitas de pares, cada par una lista o tupla de longitud dos.
Códigos de tipo `str` exacto. Rechazar mappings directos, generadores, iteradores,
strings/bytes, pares incompletos o ampliados y otros contenedores incompatibles.

Detectar cada código duplicado **antes** de incorporarlo al mapping interno;
sin claves faltantes/adicionales, alias SPE, capitalización o espacios alternativos.
No normalizar claves ni completar con cero. Se admite cualquier orden válido;
solo el resultado se ordena como ATK, DEF, VEL, INT, LOG, CUACK.
Duplicados ya descartados por una adaptación previa no pueden recuperarse ni
detectarse retrospectivamente. Esta API no define un formato JSON ni certifica
la autoridad de la configuración recibida.

## 4. Reparto y resultado · A4.1-BUDGET-01

Suma de los seis incrementos <= presupuesto. Se permite dejar puntos pendientes,
incluidos reparto cero y gasto parcial. Por cada atributo:
**valor efectivo = base validada + incremento validado**.

`TargetStatsResult`, dataclass `frozen=True, slots=True`, contiene únicamente:
`bases`, `increments`, `effective`, `budget`, `points_used` y `points_remaining`.
Las tres colecciones son tuplas de seis pares `(str, int)` en orden canónico,
sin listas/dicts internos ni referencias mutables a entradas. Se hacen copias
defensivas incluso al construir directamente la clase pública.

`points_used = sum(increments)`, `points_remaining = budget - points_used`;
efectivas = bases + incrementos para cada código. La construcción directa valida
estructura, tipos, cobertura, presupuesto y todas las igualdades: cifras derivadas
contradictorias se rechazan. Con las mismas entradas válidas, mismo resultado;
no se modifican los objetos recibidos. No incluye identidad, permisos, versión,
XP, clasificación ni estado persistente.

El presupuesto se aplica independientemente a cada Ducky/configuración: no se
consume presupuesto de otros Duckies. No es un saldo global compartido ni una
concesión de puntos. OP-RED-01 sigue gratuita/ilimitada; el cálculo puro no ejecuta
redistribución persistente, registra su historia o selecciona una opción.

## 5. Errores de validación

Distinguir entrada inválida, cobertura incompleta/sobrante/duplicada, tipos
inválidos, presupuesto excedido y configuración inconsistente. Un fallo no
normaliza, repara o completa silenciosamente entradas ni produce efectos parciales.
Reglas de consistencia adicionales requieren aprobación; no inventar límites
para convertir valores base en configuración supuestamente oficial.
Jerarquía mínima derivada de `ValueError`:

- `InvalidTargetStatsError`: base general.
- `InvalidTargetStatsStructureError`: representación, códigos, cobertura o duplicados.
- `InvalidTargetStatsNumericError`: tipos/valores numéricos o cálculos derivados
  contradictorios en construcción directa.
- `TargetStatsBudgetExceededError`: suma de incrementos superior al presupuesto.

No errores HTTP ni persistencia. Comprobar estos datos no acredita una fuente
oficial autorizada; esa responsabilidad permanece fuera del validador.

## 6. Separación pura y compatibilidad · A4.1-PURE-01

Componente determinista de validación/cálculo, separado de persistencia, permisos
y selección. No consulta/escribe BD, comprueba identidad/permisos, selecciona
opciones, crea perfiles/estados/eventos, confirma transacciones ni concede XP,
puntos de nivel o monedas. No reinterpreta estadísticas/eventos V1.
Servicios persistentes futuros gestionarán esas responsabilidades conforme a 02C
y dependencias Core, fuera del validador. Su integración no queda aprobada aquí.

V1 conserva log_stat = Logística y spe = Especial / Especialización; CharacterStats,
StatAllocationEvent y contratos/servicios/migraciones V1 no cambian. No renombrar
campos, convertir SPE histórico a CUACK o reinterpretar datos. S3 V1 conserva
su comportamiento y puntos por nivel hasta activación coordinada autorizada.

## 7. Pendientes y pruebas en 01B

Pendientes: bases oficiales por opción, presupuesto numérico autorizado,
posibles límites funcionales adicionales, fuentes/versionado de
configuración y reglas funcionales adicionales si se aprueban. También contratos
de consumo con otros equipos, modelos/conservación/migración con Óscar/Core y
activación coordinada del objetivo. **45 puntos no es presupuesto oficial.**
No fijar valores predeterminados o máximos de juego/almacenamiento por inferencia.

El corte de PR #73 solo documentaba pruebas futuras. Este incremento añade
[validador puro](../../apps/ecomotor/target_stats_validation.py) y
[tests sintéticos](../../apps/ecomotor/test_target_stats_validation.py) de cálculo,
gasto total/parcial/cero, tipos estrictos, claves/duplicados, inmutabilidad,
construcción directa, independencia, enteros grandes y aislamiento de Django/V1.
Los resultados reales de ejecución se registran en la PR de implementación;
no se presentan cantidades sintéticas como parámetros oficiales.

## 8. Relación con A4.2 · Definiciones y autorización

[A4.2](ecomotor-target-stats-config-v1.md) separa definición de bases por opción
(con identidad y versiones de catálogo/estadísticas) del presupuesto autorizado
del jugador, utilizable independientemente en cada configuración. No modifica
validate_target_stats, TargetStatsResult, A4.1-NUM-01 o su comportamiento integrado.
TargetStatsResult valida números y reparto, no demuestra fuente/publicación/vigencia
o autorización funcional. A4.2.1 será otro validador puro, todavía no implementado;
resolución confiable, conservación y consumo quedan para componentes posteriores.
