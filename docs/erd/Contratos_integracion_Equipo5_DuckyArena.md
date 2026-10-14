## 1. Tabla de soluciones y responsables

| **Integración**      | **Solución propuesta**                                                                                   | **¿Por qué conviene?**                                                                                       | **Responsable**                                      |
| -------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| Ecomotor → Duckies   | Crear `unlock_stage_items()` para conceder las piezas históricas cuando Ecomotor confirme una evolución. | Jaime controla la evolución y Henry el inventario. Evita duplicar piezas y conserva las anteriores.          | Henry implementa; Jaime define etapas y condiciones. |
| Shop → Duckies       | Crear `grant_item()` para entregar al inventario los objetos comprados.                                  | Centraliza las entregas, valida cantidades y niveles y evita duplicados. También sirve para Rewards.         | Henry implementa; Fernando integra.                  |
| Duckies → Shop       | Crear `get_item_ownership()` para consultar si el usuario ya posee un objeto.                            | Evita ofrecer compras innecesarias de objetos permanentes y permite consultar el inventario sin modificarlo. | Henry implementa; Fernando utiliza.                  |
| Shop → Bank          | Crear `debit_coins()` para descontar monedas y registrar el movimiento.                                  | Centraliza los gastos, comprueba fondos y evita cobros duplicados.                                           | Fernando implementa ambas partes.                    |
| Ecomotor → Bank      | Crear `credit_coins()` para conceder monedas por actividades recompensadas.                              | Ecomotor decide el premio y Bank controla el saldo. Evita acreditar dos veces la misma recompensa.           | Fernando implementa; Jaime integra.                  |
| Bank → Perfil global | Hacer que Bank opere sobre el saldo oficial del perfil, sin crear otro saldo independiente.              | Mantiene las DuckyCoins sincronizadas con toda la plataforma `notodoescodigo.com`.                           | Fernando + Óscar/Core.                               |
| Juegos → Ecomotor    | Crear `process_game_result()` para recibir resultados de partidas validados por el servidor.             | Centraliza XP y recompensas e impide que el cliente se conceda premios arbitrarios.                          | Jaime implementa; equipos de juegos integran.        |
| Juegos → Duckies     | Crear `consume_item()` para validar y descontar objetos utilizados en partidas.                          | Evita consumos duplicados, controla cantidades y registra el historial de uso.                               | Henry implementa; equipos de juegos integran.        |

**En las siguientes soluciones propuestas para cada contrato que queda por resolver para el equipo 5. Los códigos que se muestran en cada solución son solo ejemplos de lo que debería implementar el miembro al que le corresponda.**

## Contrato 1. Ecomotor → Duckies

Propuesta lista para aprobar

Responsables: Jaime define las etapas y confirma la evolución; Henry implementa la entrega de piezas.

Solución: Ecomotor notifica una evolución confirmada y Duckies concede las piezas históricas correspondientes.

```python
unlock_stage_items(
    user=user,
    stage_code="grecia",
    operation_key="evolution-15-grecia",
 )
```

| **Elemento**       | **Acuerdo propuesto**                                                              |
| ------------------ | ---------------------------------------------------------------------------------- |
| **Entrada**        | Usuario, código de etapa, clave de operación                                       |
| **Validación**     | Etapa confirmada por Ecomotor, piezas configuradas y ausencia de entrega duplicada |
| **Acción**         | Conceder piezas mediante grant_item()                                              |
| **Respuesta**      | Piezas entregadas, piezas ya poseídas y estado de operación                        |
| **Errores**        | Etapa inválida, operación no autorizada, conflicto de clave                        |
| **Regla especial** | Conservar piezas anteriores; no equipar automáticamente                            |

Por qué: Ecomotor sigue siendo responsable de la evolución y Duckies de la propiedad de los objetos. Se evita almacenar inventarios paralelos.

Para cerrarlo: Jaime debe confirmar los códigos oficiales de etapas y si todas las piezas se conceden al alcanzar la etapa o existen condiciones adicionales.

## Contrato 2. Shop → Duckies

Propuesta lista para aprobar

Responsables: Henry implementa; Fernando utiliza.

Solución: Shop entrega objetos exclusivamente mediante grant_item().

```python
grant_item(
    user=user,
    item_code="escudo",
    level=2,
    quantity=1,
    source="shop",
    operation_key="purchase-527-line-1",
    reference_id="527",
 )
```

| **Elemento**     | **Acuerdo propuesto**                                                        |
| ---------------- | ---------------------------------------------------------------------------- |
| **Entrada**      | Usuario, objeto, nivel, cantidad, origen, referencia y clave                 |
| **Validación**   | Objeto válido, nivel compatible, cantidad positiva, propiedad y autorización |
| **Acción**       | Actualizar InventoryItem y registrar la concesión                            |
| **Respuesta**    | ID de entrega, cantidad y already_applied                                    |
| **Errores**      | Objeto inexistente, nivel inválido, objeto permanente ya poseído, conflicto  |
| **Idempotencia** | Registrar cada concesión con una identidad única persistente                 |

Por qué: centraliza las entregas y permite que Shop y Rewards utilicen la misma lógica.

Para cerrarlo: aprobar la firma del servicio y el registro persistente de concesiones, por ejemplo ItemGrant.

## Contrato 3. Duckies → Shop

Propuesta lista para aprobar

Responsables: Henry implementa; Fernando utiliza.

Solución: crear una consulta de propiedad que Shop pueda utilizar antes de vender un objeto.

```python
get_item_ownership(
    user=user,
    item_code="casco-romano",
    level=None,
 )
```

Respuesta acordada:

```python
{
    "owned": True,
    "quantity": 1,
    "is_consumable": False,
}
```

| **Elemento**        | **Acuerdo propuesto**                                    |
| ------------------- | -------------------------------------------------------- |
| **Entrada**         | Usuario, objeto y nivel opcional                         |
| **Validación**      | Usuario y objeto válidos                                 |
| **Acción**          | Consultar inventario sin modificarlo                     |
| **Respuesta**       | Propiedad, cantidad y si es consumible                   |
| **Errores**         | Objeto inexistente, nivel inválido, acceso no autorizado |
| **Regla de compra** | Permanentes no duplicables; consumibles acumulables      |

Por qué: Shop no necesita conocer las tablas internas de Duckies y puede mostrar correctamente qué objetos tiene el usuario.

Para cerrarlo: Fernando debe aceptar que esta consulta es informativa y que la validación definitiva se realiza durante la entrega transaccional.

## Contrato 4. Shop → Bank

Propuesta lista para aprobar

Responsable: Fernando, tanto en Shop como en Bank. Henry participa en las pruebas de compra y entrega.

Solución: Shop solicita a Bank el cargo correspondiente.

```python
debit_coins(
    user=user,
    amount=150,
    source="shop",
    operation_key="purchase-527-payment",
    reference_id="527",
 )
```

| **Elemento**       | **Acuerdo propuesto**                                           |
| ------------------ | --------------------------------------------------------------- |
| **Entrada**        | Usuario, importe, origen, compra y clave                        |
| **Validación**     | Fondos, importe positivo, autorización y operación no duplicada |
| **Acción**         | Descontar saldo y registrar movimiento                          |
| **Respuesta**      | ID del movimiento, importe, estado y already_applied            |
| **Errores**        | Fondos insuficientes, importe inválido, conflicto               |
| **Regla especial** | Cargo y entrega deben ser consistentes                          |

Por qué: Bank controla los movimientos económicos y Shop no modifica directamente el saldo.

Para cerrarlo: Fernando debe definir purchase_item() como coordinador del cargo y la entrega. Si las operaciones comparten una base de datos, utilizar una transacción común; si no, definir estados de compra y recuperación ante fallos.

## Contrato 5. Ecomotor → Bank

Propuesta lista para aprobar

Responsables: Jaime define recompensas; Fernando implementa el crédito.

Solución: Rewards solicita a Bank la concesión de monedas.

```python
credit_coins(
    user=user,
    amount=10,
    source="rewards",
    operation_key="reward-quiz-854-coins",
    reference_id="quiz-854",
 )
```

| **Elemento**     | **Acuerdo propuesto**                                            |
| ---------------- | ---------------------------------------------------------------- |
| **Entrada**      | Usuario, importe, origen, referencia y clave                     |
| **Validación**   | Recompensa autorizada, importe positivo y operación no duplicada |
| **Acción**       | Acreditar monedas y registrar movimiento                         |
| **Respuesta**    | ID del movimiento, importe y estado                              |
| **Errores**      | Recompensa no autorizada, importe inválido, conflicto            |
| **Idempotencia** | Una recompensa concreta solo puede acreditarse una vez           |

Por qué: Ecomotor controla las reglas de recompensas y Bank la economía. Ningún juego modifica directamente el saldo.

Para cerrarlo: Jaime y Fernando deben acordar cómo se construye el identificador único de cada recompensa.

## Contrato 6. Bank → Perfil global

Requiere confirmación de Core

Responsables: Fernando + Óscar/Core.

Solución: Bank utiliza la fuente oficial de DuckyCoins de notodoescodigo.com, sin almacenar un segundo saldo independiente.

Si Core confirma que el saldo oficial sigue siendo Profile.ducky_coins, se propone:

```text
BANK
├── get_balance()
├── credit_coins()
└── debit_coins()
        │
        ▼
Profile.ducky_coins
```

| **Elemento**         | **Acuerdo propuesto**                                |
| -------------------- | ---------------------------------------------------- |
| **Fuente del saldo** | Profile.ducky_coins, pendiente de confirmación       |
| **Lectura**          | get_balance(user)                                    |
| **Escritura**        | Operaciones autorizadas de crédito y débito          |
| **Registro**         | Movimientos contables de Bank                        |
| **Wallet**           | Puede existir como envoltorio, sin saldo duplicado   |
| **Seguridad**        | Acceso controlado y operaciones concurrentes seguras |

Por qué: las monedas pertenecen a toda la plataforma, no solamente al juego. Un único saldo evita inconsistencias.

Para cerrarlo: Óscar debe confirmar si Bank accederá mediante ORM o mediante un servicio global existente, y qué garantías transaccionales ofrece.

Este contrato no debería aprobarse definitivamente sin esa respuesta.

## Contrato 7. Juegos → Ecomotor

Propuesta lista para aprobar

Responsables: Jaime implementa; equipos de juegos integran.

Solución: los juegos envían resultados validados por el servidor a Ecomotor.

```python
process_game_result(
    user=user,
    game_code="quiz_battle",
    session_id="battle-854",
    result_id="result-854",
    score=850,
    correct_answers=8,
    total_questions=10,
 )
```

| **Elemento**     | **Acuerdo propuesto**                                         |
| ---------------- | ------------------------------------------------------------- |
| **Entrada**      | Usuario, juego, partida, resultado y métricas validadas       |
| **Validación**   | Partida legítima, finalizada y no procesada anteriormente     |
| **Acción**       | Registrar progreso, calcular XP y evaluar recompensas         |
| **Respuesta**    | Resultado procesado, XP aplicada y referencias de recompensas |
| **Errores**      | Resultado inválido, origen no autorizado, conflicto           |
| **Idempotencia** | Cada resultado se procesa una única vez                       |

Por qué: centraliza las reglas de progresión y evita que cada juego conceda directamente XP o monedas.

Para cerrarlo: Jaime y los equipos de juegos deben aprobar un formato común de resultados y las reglas de verificación.

## Contrato 8. Juegos → Duckies

Propuesta lista para aprobar

Responsables: Henry implementa; equipos de juegos integran.

Solución: los juegos solicitan el consumo de objetos a Duckies, que valida propiedad y cantidad.

```python
consume_item(
    user=user,
    item_code="turbo-preguntas",
    level=2,
    quantity=1,
    operation_key="battle-854-use-1",
    source_game="quiz_battle",
    session_id="battle-854",
 )
```

| **Elemento**       | **Acuerdo propuesto**                                            |
| ------------------ | ---------------------------------------------------------------- |
| **Entrada**        | Usuario, objeto, nivel, cantidad, juego, partida y clave         |
| **Validación**     | Propiedad, cantidad, nivel, autorización y operación no repetida |
| **Acción**         | Descontar inventario y registrar ItemUsage                       |
| **Respuesta**      | ID de consumo, cantidad y estado                                 |
| **Errores**        | Sin existencias, objeto inválido, uso no permitido, conflicto    |
| **Regla especial** | Coordinar consumo con aplicación del efecto                      |

Por qué: Duckies controla el inventario y los juegos únicamente aplican los efectos permitidos.

Para cerrarlo: Henry y los equipos de juegos deben definir cuándo se confirma el uso y cómo se recupera una operación si falla el juego.
