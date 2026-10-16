# S6-A · Configuración confiable y diagnóstico V1

Decisión interna aprobada por Jaime/Parte A: JSON local de carga explícita desde
un contexto confiable. DAR3 aporta requisitos de dominio; no establece este
mecanismo técnico ni convierte ejemplos de atributos/XP en valores aprobados.
La aprobación funcional de todos los valores sigue siendo independiente.

## Carga sin activación

`load_initialization_configuration(path, *, using="default")` lee un JSON local
UTF-8 con exactamente atk, def_stat, log_stat, spe, vel, int_stat y
ordered_stage_codes. Rechaza campos ausentes/desconocidos/duplicados, raíces
distintas de objeto, conversiones implícitas y estadísticas booleanas/fraccionarias.
Los enteros respetan únicamente el rango técnico de los IntegerField de
CharacterStats en el alias seleccionado, sin rango funcional nuevo.
Los siete códigos únicos no vacíos, de hasta 32 caracteres, corresponden por
posición a Prehistoria, Griega, Romana, Renacentista, Contemporánea, Siglo XX y
Actual. No se deducen de filas ni nombres visibles. Validar posiciones no permite
demostrar que los valores hayan recibido autorización funcional.

Devuelve InitializationConfiguration frozen, con copia defensiva de códigos.
ConfigurationFileError (incluye ConfigurationFileMissingError),
ConfigurationSyntaxError y ConfigurationStructureError distinguen acceso,
sintaxis y estructura/tipos/rangos. No expone contenido del archivo en mensajes.
Rutas de red/URL no admitidas. No guarda, instala ni altera INITIAL_CONFIGURATION.
Su valor inicial sigue siendo None, sin defaults ni JSON de producción ficticio.

## Diagnóstico

`check_ecomotor_readiness(*, configuration=<referencia actual>, using="default")`
usa la referencia del proceso si se omite configuration; None explícito significa
ausencia. Devuelve ReadinessResult frozen con status, issues (tupla de
ReadinessIssue con code y message) y technically_consistent. Sin propiedad de
aprobación funcional. Errores reales de alias/acceso BD producen
ReadinessDatabaseError con causa preservada, no un estado de configuración.

Precedencia determinista: CONFIGURATION_MISSING, INVALID_CONFIGURATION,
INVALID_CATALOG, CATALOG_INCOMPLETE, TECHNICALLY_READY. Configuración inválida
o ausente impide consultar catálogos. Con configuración válida se leen ambos y
se acumulan incidencias en orden niveles/etapas. Invalidez prevalece sobre falta.

Catálogo incompleto: niveles vacíos o menos de siete etapas cuyas filas presentes
son válidas. Catálogo inválido: filas técnicamente inválidas, niveles con huecos
o sin nivel 1, umbrales incoherentes, ordinal/código incompatible o exceso de
etapas. Las filas parciales de etapas también deben respetar la correspondencia,
XP inicial si está presente y crecimiento de sus umbrales. Un único nivel 1 con
XP 0 es completo y válido; no se inventa el total final de niveles.
Reutiliza validate_level_catalog y validate_evolution_stage_catalog para catálogos
completos, precedidos de validación estricta de tipos/rangos sin normalización.

TECHNICALLY_READY significa técnicamente consistente, no necesariamente aprobado
para producción. Solo SELECT; sin reparar catálogos, perfiles ni historial y sin
snapshot transaccional único frente a ediciones concurrentes. Sin BEGIN IMMEDIATE
ni bloqueos añadidos para diagnóstico. V2-A28 permanece pendiente.

## Comando y códigos de salida

`python manage.py check_ecomotor_readiness`

`python manage.py check_ecomotor_readiness --config RUTA_JSON_LOCAL --database default`

Sin --config consulta solo la referencia actual del proceso, normalmente None.
Con --config diagnostica el candidato sin instalarlo. Salida 0: técnicamente
consistente; 2: diagnóstico no preparado o JSON ausente/inválido; 3: fallo
operativo de archivo/alias/BD. Mensajes genéricos, sin trazas ni secretos. Errores
de programación no se reclasifican como configuración inválida. Toda salida
esperada recuerda que aprobación funcional y activación son independientes.
Un proceso de comando no activa configuración del servidor web.

## Compatibilidad y límites

S2-A/S3 siguen leyendo INITIAL_CONFIGURATION sin cambios. Una futura instalación
en cada proceso servidor exigirá una acción explícita autorizada, especificada
separadamente: este contrato no añade un punto de arranque. Tests pueden cargar
un candidato y sustituir temporalmente la referencia, nunca producción implícita.
S3 sigue necesitando solo códigos, sin validar stats iniciales; S2-A existente y
S4-A/S5-A básicos no requieren configuración actual. Sin cambios de esquema.
Valores oficiales, conservación legacy, Core/Rewards, contratos compartidos y
política histórica de catálogos no quedan aprobados por este diagnóstico.
