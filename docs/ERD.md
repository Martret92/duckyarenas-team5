# ERD y diccionarios del Equipo 5

## Estado y autoridad

Corte DOC-2 del 18/10/2026: develop en `33b4e87139e86730902300eb358257fdd299ef13`,
tras PR #33. Este es el punto de entrada común de diagrama y diccionarios para
PR07; conserva el criterio ERD, cardinalidades, relaciones y reglas on_delete
previas al ORM afectado. DAR3 sigue siendo la fuente funcional principal.
No representa aprobación global del profesor, Core ni contratos A/B/C.

## Diagrama global candidato

![ERD global candidato del Equipo 5](erd/erd_global_equipo5.png)

El [ERD global propuesto](erd/erd-global-propuesta.md) conserva su diagrama y
Mermaid históricos. Incluye RewardEvent, ItemGrant y relaciones físicas propuestas:
**no es el esquema ORM global confirmado ni incorpora la ampliación S7-A de Parte A**.
No debe utilizarse como evidencia de migraciones globales aplicadas.

## Diccionarios y esquema integrado

| Dominio | Diccionario | Estado en la baseline |
| --- | --- | --- |
| Parte A / Jaime | [Ecomotor](erd/ecomotor.md) | Nueve entidades locales: ocho en apps.ecomotor y UserProfileEcomotor en apps.users. Día 4 y S7-A integrados; V2 histórico de ocho conservado separadamente. |
| Parte B / Henry | [Duckies](erd/duckies.md) | Diseño compartido de nueve modelos, fechado 13/10. No acredita su integración en develop ni servicios/migraciones globales. ItemGrant sigue candidato. |
| Parte C / Fernando | [Bank/Shop](erd/bank-shop.md) | Borrador 0.2 de la rama de Parte C, no del ORM integrado en develop. Reubicación y reconciliación de migraciones A/C pendientes. |
| Integración | [Contrato Equipo 5 v0](contracts/integracion-equipo5-v0.md) y [Rewards v0](contracts/rewards-v0.md) | Candidatos; matriz de procedencia, respuestas externas y conflictos sin ratificación técnica global. |

Parte A integra ecomotor.0001_initial, 0002_characterstats,
0003_xp_and_evolution_events, 0004_user_specialization_progress y
0005_stat_allocation_event, además de users.0002_ecomotor_progress.
[El detalle físico](erd/ecomotor.md#12-esquema-físico-vigente--statallocationevent-s7-a)
explica StatAllocationEvent y su FK al perfil con CASCADE provisional.
UserProfileBank existe como perfil, sin demostrar Wallet o saldo integrado.
S1–S7-A locales están integrados; S8-A continúa aprobado y pausado, sin implementar.

RewardEvent y RewardRule no son tablas aprobadas; ItemGrant tampoco se incorpora
por este documento. Las FK EvolutionItem–EvolutionStage, ShopItem–Item/ItemLevel,
las referencias de compras y las fronteras transaccionales A/B/C requieren acuerdo.
Core conserva User, identidad/autorización, membresías, fuente económica y
conservación/legacy. No se duplica saldo ni se modifica AUTH_USER_MODEL.

## Normalización de rutas y compatibilidad

DOC-2 aplica estos renombrados documentales, preservando el contenido histórico
mediante Git. Las dos copias iniciales del contrato tenían el mismo objeto Git
`a0d6cfccad119a03af3c9a4b5be69fa08e40ed9d`; se conserva una sola en contracts.

| Ruta anterior | Ruta canónica |
| --- | --- |
| docs/erd/ERD-duckies.md | [docs/erd/duckies.md](erd/duckies.md) |
| docs/erd/parte-c-ecommerce-bank.md | [docs/erd/bank-shop.md](erd/bank-shop.md) |
| docs/erd/Resolucion_ERD_Global_Equipo5.md | [docs/erd/erd-global-propuesta.md](erd/erd-global-propuesta.md) |
| docs/contracts/Contratos_integracion_Equipo5_DuckyArena.md | [docs/contracts/integracion-equipo5-v0.md](contracts/integracion-equipo5-v0.md) |
| docs/erd/Contratos_integracion_Equipo5_DuckyArena.md | Copia duplicada eliminada; usar [el contrato canónico](contracts/integracion-equipo5-v0.md). |

Las referencias relativas del repositorio se actualizan. Las URLs a rutas antiguas
compartidas externamente o en PR/ramas anteriores pueden dejar de resolver sobre
develop: no se garantiza su redirección ni se reescribe documentación externa.
Para consultar un antecedente, utilizar su commit histórico y esta correspondencia.
Los diccionarios de Henry y Fernando solo se renombran y corrigen en referencias;
no se modifican sus reglas funcionales ni se acredita implementación posterior.
