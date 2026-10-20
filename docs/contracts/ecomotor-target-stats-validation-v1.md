# A4.1 · Validación pura de estadísticas objetivo · Contrato conceptual v1

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
**Diseño del componente puro, no implementado:** sin API Python definitiva,
persistencia, servicios nuevos, modelos, migraciones o activación objetivo.
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
- Bases explícitas numéricas con tipos apropiados para el cálculo, sin booleanos
  o representaciones incompatibles. Valores oficiales, dominio numérico concreto,
  límites y reglas adicionales de bases/efectivos pendientes antes de codificar;
  no ratificar aquí tipos numéricos alternativos, mínimos, máximos o signos permitidos.
- Incrementos: enteros no negativos, excluyendo booleanos; no aceptar valores no
  enteros o negativos ni convertirlos silenciosamente para hacer válido un reparto.
- Presupuesto: entero no negativo, excluyendo booleanos.

Representación de entrada y firma por concretar. Si la representación admite
claves repetidas, detectarlas antes de perderlas en una conversión a mapping;
un mapping ya colapsado no demuestra que su fuente careciese de duplicados.
No se fija aquí un formato JSON o un nuevo tipo Python.

## 4. Reparto y resultado · A4.1-BUDGET-01

Suma de los seis incrementos <= presupuesto. Se permite dejar puntos pendientes,
incluidos reparto cero y gasto parcial. Por cada atributo:
**valor efectivo = base validada + incremento validado**.

Resultado conceptual: seis valores efectivos, puntos utilizados (suma de
incrementos), puntos restantes (presupuesto menos utilizados) y datos de entrada
validados sin mutaciones. Con mismas entradas válidas, mismo resultado;
representación concreta del resultado aún pendiente.

El presupuesto se aplica independientemente a cada Ducky/configuración: no se
consume presupuesto de otros Duckies. No es un saldo global compartido ni una
concesión de puntos. OP-RED-01 sigue gratuita/ilimitada; el cálculo puro no ejecuta
redistribución persistente, registra su historia o selecciona una opción.

## 5. Errores conceptuales

Distinguir entrada inválida, cobertura incompleta/sobrante/duplicada, tipos
inválidos, presupuesto excedido y configuración inconsistente. Un fallo no
normaliza, repara o completa silenciosamente entradas ni produce efectos parciales.
Reglas de consistencia adicionales requieren aprobación; no inventar límites
para convertir valores base en configuración supuestamente oficial.
No clases definitivas de excepciones, modelos de error HTTP o firmas obligatorias.

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

## 7. Pendientes y pruebas futuras en 01B

Pendientes: bases oficiales por opción, presupuesto numérico autorizado, dominio
y posibles límites adicionales de bases/efectivos, fuentes/versionado de
configuración y reglas funcionales adicionales si se aprueban. También contratos
de consumo con otros equipos, modelos/conservación/migración con Óscar/Core y
activación coordinada del objetivo. **45 puntos no es presupuesto oficial.**
No fijar valores predeterminados o máximos de juego/almacenamiento por inferencia.

Tests futuros: reparto válido y efectivas; gasto total/parcial; reparto cero;
presupuesto excedido; claves ausentes/sobrantes/duplicadas; booleanos y no enteros
en incrementos/presupuesto, negativos donde sean inválidos y tipos base incompatibles
con su dominio acordado; entradas sin mutaciones; dos opciones con configuraciones
y presupuestos independientes; compatibilidad sin modificar V1.
No se implementan ni ejecutan tests Django en esta PR documental ni se crea código.
