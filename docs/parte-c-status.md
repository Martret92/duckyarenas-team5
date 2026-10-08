# Parte C · Ecommerce y DuckyBank

## Estado

Documento inicial de seguimiento del trabajo de la Parte C del Equipo 5.

Este documento es provisional y no sustituye las decisiones globales del equipo,
el ERD consolidado ni los contratos definitivos con Ecomotor, Inventory, Rewards
o Core.

## Alcance inicial

La Parte C contempla:

- DuckyBank;
- DuckyShop;
- gestión del saldo y movimientos;
- catálogo y compras;
- idempotencia de operaciones;
- integración con la entrega de objetos a Inventory.

## Principios iniciales

- El servidor mantiene el estado económico oficial.
- Las operaciones de crédito y débito deben ser idempotentes.
- Las compras no deben producir cargos ni entregas duplicadas.
- El precio y las condiciones de compra deben validarse en el servidor.
- La integración con Inventory debe evitar duplicar la responsabilidad sobre la
  posesión de los objetos.
- La implementación deberá respetar las decisiones de concurrencia y transacciones
  ya establecidas por el Equipo 5.

## Próximos pasos

1. Confirmar el alcance V1 de DuckyBank y DuckyShop.
2. Revisar las dependencias con Inventory, Ecomotor y Rewards.
3. Definir contratos mínimos entre dominios.
4. Consolidar el ERD de la Parte C con el resto del Equipo 5.
5. Implementar el ORM únicamente después de cerrar las dependencias necesarias.
6. Añadir pruebas de idempotencia, saldo insuficiente, compra y rollback.

## Estado del documento

**Provisional — seguimiento de trabajo de la Parte C.**
