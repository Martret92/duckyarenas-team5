# Parte C · Ecommerce y DuckyBank

## 1. Estado y alcance

Este documento registra el diseño técnico provisional de la Parte C del Equipo 5,
responsable de Ecommerce y DuckyBank.

La implementación definitiva depende de la consolidación de las fronteras entre
Ecomotor, Avatar/Inventory, Ecommerce/DuckyBank y el servicio común de Rewards.

Este documento no sustituye las decisiones globales del Equipo 5 ni autoriza,
por sí mismo, el ORM definitivo.

## 2. Responsabilidades de la Parte C

### 2.1 DuckyBank

DuckyBank es responsable de la economía del usuario, incluyendo:

- cartera/saldo;
- entradas y salidas de monedas;
- débitos;
- créditos;
- ajustes;
- reembolsos;
- historial y trazabilidad de los movimientos.

### 2.2 DuckyShop

DuckyShop es responsable del proceso comercial, incluyendo:

- catálogo comercial;
- productos/ofertas;
- precios;
- disponibilidad;
- compras;
- estado de la compra;
- entrega comercial.

### 2.3 Límites con otros dominios

Inventory es responsable de la posesión de los objetos.

Avatar/Equipment es responsable del estado de equipamiento.

Ecomotor es responsable de XP, evolución y estadísticas.

Rewards es un servicio común del Equipo 5 y su frontera definitiva con
DuckyBank, DuckyShop y Ecomotor todavía depende de la consolidación de los contratos.

## 3. Principios

### 3.1 Autoridad por dominio

Cada dominio debe mantener su propia responsabilidad:

- Bank → saldo y movimientos financieros;
- Shop → proceso comercial;
- Inventory → posesión;
- Avatar/Equipment → equipamiento;
- Ecomotor → XP, evolución y estadísticas;
- Rewards → coordinación de recompensas, según el contrato aprobado.

### 3.2 Autoridad del servidor

Una compra debe ser validada y procesada en el servidor.

El cliente no debe determinar:

- saldo final;
- precio efectivo;
- autorización del débito;
- posesión del objeto;
- resultado final de la compra.

### 3.3 Idempotencia

Las operaciones críticas deben disponer de una clave persistente de idempotencia.

Una misma operación repetida con los mismos parámetros debe devolver el resultado
ya procesado.

Una misma clave utilizada con parámetros incompatibles debe producir un conflicto,
sin reescribir la operación original.

## 4. Entidades candidatas

La Parte C deberá evaluar, como mínimo, las siguientes entidades:

### DuckyBank

- Wallet
- Transaction

### DuckyShop

- ShopItem
- Purchase

Los campos definitivos, cardinalidades, constraints y relaciones con Inventory,
Ecomotor y Rewards se definirán antes del ORM definitivo.

## 5. Flujo conceptual de compra

El flujo previsto es:

1. El usuario selecciona un producto.
2. Shop presenta y valida el precio.
3. El usuario confirma la compra.
4. El servidor valida las condiciones de la operación.
5. DuckyBank valida y registra el débito.
6. Shop registra/procesa la compra.
7. El objeto digital se entrega a Inventory o, en el caso de merchandising físico,
   se crea el pedido correspondiente.
8. El resultado de la operación se persiste de forma idempotente.

El orden exacto y la frontera transaccional entre Shop, Bank e Inventory todavía
dependen de la decisión global del Equipo 5.

## 6. Tipos de entrega

### Digital

La compra deberá resultar en la entrega de un objeto al dominio responsable
de la posesión, actualmente identificado como Inventory.

### Física

Una compra de merchandising físico deberá generar un pedido con los estados
comerciales correspondientes.

El conjunto definitivo de estados y reglas todavía depende de la consolidación
funcional.

## 7. Transacciones y concurrencia

La implementación seguirá D-19:

- SQLite;
- `transaction_mode = IMMEDIATE`;
- timeout de 5 segundos;
- `transaction.atomic()` antes de leer el estado mutable;
- transacciones cortas;
- sin HTTP ni I/O externo dentro de la transacción;
- constraints en la base de datos;
- idempotencia persistente;
- los reintentos deben iniciar una nueva transacción.

La atomicidad global entre diferentes dominios todavía no está definida.

## 8. Cuestiones pendientes

Antes del ORM definitivo deben definirse:

- ERD consolidado A+B+C;
- frontera exacta entre Shop e Inventory;
- coordinador de la compra completa;
- frontera transaccional Shop/Bank/Inventory;
- estrategia de rollback y recuperación;
- contrato con Ecomotor;
- contrato con Rewards;
- contrato con Core/User;
- claves y alcance global de la idempotencia;
- catálogo comercial;
- precios oficiales;
- reglas definitivas de compra;
- alcance de V1.

## 9. Pruebas previstas

La Parte C deberá contemplar, como mínimo:

- compra válida;
- saldo insuficiente;
- idempotencia;
- conflicto de `operation_key`;
- débito correcto;
- crédito/reembolso;
- rollback;
- cantidades válidas;
- concurrencia;
- autorización del usuario;
- integración con Inventory;
- contratos con los demás dominios.

## 10. Estado del documento

Estado: **provisional / en elaboración**.

Este documento no representa una aprobación global de los contratos A/B/C/Core.

El ORM definitivo solo deberá crearse después de la consolidación de las decisiones
y del ERD del Equipo 5.
