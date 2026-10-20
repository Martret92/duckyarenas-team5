# A3.2 · Inventario legacy de solo lectura · Contrato candidato v1

## 1. Autoridad y estado

A3.2-ARQ-01, aprobado **internamente por el Equipo 5**, comunicado en el encargo
documental. Corte del 20/10/2026 sobre develop
`8024fa7673e5587bcc49025a2fafe3eb215c1273`. DAR3 conserva su autoridad funcional
principal; extracción ORM, API y transacciones son decisiones técnicas internas,
no una especificación literal del profesor ni aprobación de permisos Core.
Se usa trazabilidad existente de fuentes, sin afirmar nueva consulta de PDFs.

A3 general está integrado por PR #57 y [A3.1 puro](../../apps/ecomotor/legacy_transition_audit.py)
por PR #58, con sus [pruebas existentes](../../apps/ecomotor/test_legacy_transition_audit.py).
**A3.2 no está implementado. S3 V1 sigue siendo escritor activo; no hay migración
ni activación objetivo.** Nombre/firma definitivos se revisarán en 01B.
[Decisiones](../decisions.md#a32--inventario-legacy-de-solo-lectura--20102026),
[arquitectura](../architecture.md#12-a32--extracción-legacy-de-solo-lectura),
[pendientes](../pending-decisions.md#16-a32--alcance-y-validaciones-pendientes)
y [transición A3](ecomotor-transition-target-v1.md#12-a32--extracción-de-evidencia-separada-de-auditoría).

## 2. Alcance por operación · A3.2-SCOPE-01

Extraer evidencia de **un único UserProfileEcomotor**: perfil, CharacterStats,
todos sus XPEvent, todos sus EvolutionEvent, catálogo EvolutionStage V1 completo
del alias elegido y comprobaciones causales mínimas hacia/desde otros perfiles.
Sin inventario masivo o paginación que se presente como cobertura completa.

No se declaran integralmente auditados StatAllocationEvent, especializaciones/
UserSpecializationProgress, dominio/rangos, inventario/vestimenta/equipamiento o
relaciones completas Duckies, umbrales históricos, puntos gastados ni compatibilidad
con una futura migración objetivo. Copiar active_specialization_code del perfil
no audita sus progresos. Leer el catálogo actual no reconstruye sus atributos
históricos; XPEvent/EvolutionEvent mantienen las limitaciones de snapshots V1.

## 3. Interfaz conceptual y tipos · A3.2-API-01

`extract_legacy_audit_snapshot(profile_id, *, using) -> LegacyAuditSnapshot`

No es servicio disponible ni firma definitiva. Recibe ID de perfil Ecomotor
persistido, entero estricto (sin bool o conversiones implícitas), y alias Django
seleccionado por llamador interno confiable. Validar entrada y existencia en ese
alias; no recibir User arbitrario ni elegir alias desde datos de cliente.
El llamador debe estar autorizado para inspeccionar ese perfil. El extractor no
sustituye permisos Core ni crea autenticación propia o acceso público.

Retornar exclusivamente LegacyAuditSnapshot compuesto por clases tipadas ya
existentes de A3.1, con colecciones materializadas, sin modelos Django/QuerySets,
resultados de auditoría, permisos de migración o relaciones diferidas:

| Componente A3.1 | Datos observados mínimos |
| --- | --- |
| LegacyProfileSnapshot | profile_id, historical_xp_total, current_level, current_stage_code, active_specialization_code. Sin User, nombre/correo u otros datos Core. |
| LegacyCharacterStatsSnapshot o None | profile_id, atk, def_stat, log_stat, spe, vel, int_stat, available_points; None solo cuando se haya consultado y observado ausencia. |
| LegacyXPEventSnapshot | id, profile_id, operation_key exacta, amount, xp_before, xp_after de cada evento propio. |
| LegacyEvolutionEventSnapshot | id, profile_id, xp_event_id, stage_id de cada evolución propia; preservar referencias observadas representables, no reconstruir causas. |
| LegacyStageSnapshot | id, code, ordinal, minimum_xp de todo EvolutionStage del alias; sin validar que el catálogo sea funcionalmente válido por el hecho de consultarlo. |
| LegacyAuditCoverage | Cuatro flags verdaderos solo tras completar correctamente lecturas y comprobaciones previstas (§5). |

Datos representables pero incoherentes pueden ser evidencia para A3.1; no
normalizarlos para que parezcan válidos. Si no pueden representarse mediante sus
clases estrictas, fallar explícitamente, sin convertir tipos o inventar valores.

## 4. Fotografía consistente · A3.2-CONS-01

Todas las lecturas necesarias se realizan en una **transacción corta del mismo
alias**, incluidas consultas causales. La [configuración actual](../../config/settings.py)
SQLite utiliza transaction_mode="IMMEDIATE" y timeout=5. BEGIN IMMEDIATE permite
una fotografía coherente durante la extracción, pero puede bloquear temporalmente
escritores o fallar por timeout: solo lectura de negocio no significa ausencia de
costes de concurrencia. select_for_update no aporta bloqueos de fila en SQLite.

Se propone **rechazar una transacción exterior activa** para no depender de una
frontera desconocida. El detalle de verificación se revisará antes de implementar;
no se afirma que esa protección exista. Alias inválido/no confiable o condiciones
que impidan garantizar la fotografía deben causar fallo explícito.

Materializar todos los snapshots antes de salir; ninguna lectura pendiente tras
cerrar la transacción. No introducir I/O externo, esperas o auditorías extensas;
no llamar al evaluador A3.1 dentro de la transacción ni automáticamente después.
No hay escrituras de negocio, clasificación, persistencia adicional o reparación.
Una modificación posterior no invalida retrospectivamente lo observado, pero el
snapshot no es evidencia vigente indefinidamente ni permiso para migrar después.
No se promete coherencia conjunta entre aliases o bases independientes.

## 5. Cobertura íntegra, no coherencia · A3.2-COV-01

La primera versión **no devuelve snapshots parciales**. Una devolución correcta
incluye los cuatro flags True con los siguientes significados:

| Flag | Afirmación limitada a la observación |
| --- | --- |
| xp_events_complete=True | Se leyeron íntegramente todos los XPEvent cuyo propietario es el perfil inspeccionado. |
| evolution_events_complete=True | Se leyeron íntegramente sus EvolutionEvent y se completaron las comprobaciones causales previstas en ambos sentidos. |
| stages_complete=True | Se consultó íntegramente el catálogo EvolutionStage del alias seleccionado. |
| character_stats_observed=True | Se consultó correctamente CharacterStats del perfil, exista o no fila. |

Colecciones vacías tras consultas completas son observaciones válidas. Ausencia
observada de CharacterStats produce character_stats=None, **no error de lectura**;
el auditor A3.1 puede diagnosticar CHARACTER_STATS_MISSING posteriormente. Cobertura
no demuestra catálogo válido, historia íntegra de umbrales o registros coherentes.

Timeout, error de consulta, truncado o imposibilidad de cobertura íntegra producen
fallo explícito; nunca flags falsos como éxito parcial, colecciones vacías inventadas
o una ausencia supuesta. Un snapshot tipado por sí solo no certifica la veracidad
de flags suministrados por terceros: A3.1 confía en evidencia recibida, no extrae BD.

## 6. Causalidad bidireccional · A3.2-CAUS-01

Comprobar dos casos, en el mismo alias/fotografía:

1. EvolutionEvent del perfil cuya XPEvent causal pertenece a otro perfil.
2. EvolutionEvent de otro perfil que referencia un XPEvent del perfil inspeccionado.

Las consultas externas usan solo identificadores/propietarios imprescindibles
para esa comprobación, sin ampliar autorización a historiales ajenos ni incorporarlos
al snapshot ordinario. **Causalidad extranjera confirmada: fallo explícito**, sin
retornar inventario presentado como válido o una cobertura completa engañosa.
No exponer IDs, operation_key o datos personales de terceros en mensajes públicos
ni logs. No copiar una causa extranjera al conjunto XP propio para ocultar el caso.

Distinguir referencia ausente de causa extranjera. Cuando la causa realmente no
exista, conservar xp_event_id observado para que A3.1 pueda emitir
**XP_CAUSE_NOT_FOUND**, siempre que el snapshot siga siendo representable y la
extracción íntegra/coherente. No inventar la causa ni descartarla mediante un join.
Si no puede garantizarse esa observación o integridad, fallar; nunca reparar datos.
No se amplían permisos para inspeccionar otros jugadores por esta comprobación.

## 7. Minimización y privacidad · A3.2-PRIV-01

Extraer solo campos de las clases anteriores. operation_key se conserva **exacta**
porque A3.1 comprueba estructura/idempotencia; no recortar, normalizar, truncar o
anonimizar su valor dentro del snapshot. Eso no autoriza registrar su contenido
en logs, errores, trazas de diagnóstico o exportaciones. No volcar snapshots o
consultas con payload sensible como mecanismo de diagnóstico.

No incluir nombre, correo, tokens, contraseñas u otros datos personales Core.
Mensajes de fallo deben ser controlados, sin datos de terceros ni claves; no se
fijan excepciones públicas que incorporen esos valores. Sin endpoint público,
comando de exportación masiva, archivos de volcado o almacenamiento adicional.

## 8. Responsabilidades y errores · A3.2-SEP-01

A3.2 obtiene evidencia persistida y construye snapshots tipados; A3.1 evalúa
snapshots y devuelve diagnósticos. Clasificar, migrar o conceder XP exigirán sus
propias decisiones/autorizaciones/garantías. No invocar automáticamente auditoría,
clasificación o migración, ni activar política al obtener fotografía compatible.
Un diagnóstico COMPATIBLE de A3.1 solo cubre su subconjunto observable V1, no
inventario completo, elegibilidad XP o autorización de transición.

Distinguir errores conceptuales, sin nombres definitivos de excepciones Python
ni códigos HTTP: ID inválido; alias inválido/no confiable; perfil inexistente;
lectura/timeout BD; causalidad extranjera; evidencia no representable mediante
clases A3.1; imposibilidad de cobertura íntegra. La propuesta de rechazar frontera
exterior desconocida debe comunicarse como fallo explícito, no como inventario.
No convertir fallos BD en vacíos/parciales, normalizar o reparar datos V1.

## 9. Implementación futura y pruebas previstas

En 01B se revisarán nombres/firmas de candidatos
apps/ecomotor/legacy_inventory_reader.py y
apps/ecomotor/test_legacy_inventory_reader.py; **no se crean aquí**. Sin cambios
iniciales en legacy_transition_audit.py, xp_service.py, modelos Ecomotor/Users/
Duckies, migraciones o configuración BD. No se cambia S3 ni el contrato V1.

Pruebas previstas, todavía no implementadas ni ejecutadas en esta PR:

- Perfil existente/inexistente; entero estricto y alias inválido, ajeno o confiable.
- Eventos vacíos, estadísticas ausentes, cuatro coberturas completas y catálogo
  observado aunque sus datos requieran diagnóstico posterior.
- Causas extranjeras en ambos sentidos, sin historiales/IDs ajenos filtrados;
  referencia ausente preservada y XP_CAUSE_NOT_FOUND en evaluación separada.
- Fallos de consulta/timeout/truncado y representabilidad: sin falso vacío/parcial,
  reparación o claves expuestas; propuesta de rechazo de transacción exterior.
- Fotografía coherente bajo lecturas concurrentes; TransactionTestCase y conexiones
  SQLite independientes, sin prometer lectura gratuita ni row locking.
- Materialización íntegra, cero escrituras, no invocación automática de A3.1 y
  regresión S3 V1 sin cambios de puntos, replay o conflictos.

## 10. Límites que continúan abiertos

Auditoría integral StatAllocationEvent, especializaciones/dominio/rangos,
dependencias completas Duckies, umbrales históricos y puntos gastados no se cubren.
Modelo físico de clasificación, catálogo objetivo, nuevas relaciones causales,
migración/activación, conservación/anonimización/eliminación/on_delete Core/P5 y
autorización de operadores/consumidores siguen pendientes. No se desbloquean
S13-A2, dominio persistente, Rewards F2-A o integración económica. A3.2 futuro no
es migración ni certificación global de compatibilidad; esta PR solo documenta.
