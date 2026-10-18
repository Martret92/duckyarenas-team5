# S8-A · Interfaz web local de asignación V1

Reactivada por Jaime/Parte A tras coordinación de octubre y DOC-6. Convenciones
internas HTTP, no requisitos atribuidos a DAR3, Óscar/Core o Rewards. F2-A sigue
bloqueada para persistencia hasta Core y no cambia en este incremento.

## Identidad y operación

allocate_points_view(request), login_required, GET/POST y CSRF estándar Django.
Perfil solo mediante UserProfileEcomotor.objects.get(user=request.user); ignora
IDs de URL/GET/POST. Sin creación/inicialización ni permisos paralelos.
GET usa get_progress_overview de S4-A: seis stats base/saldo, sin exigir Actual
o configuración activa. Datos informativos, no autorización para gastar.

StatAllocationForm es forms.Form, nunca ModelForm: attribute ChoiceField según
STAT_ATTRIBUTES; points decimal ASCII positivo estricto, sin signo/espacios/
fracción/exponente o conversión de 1.0; operation_key oculto obligatorio de 1–255
caracteres sin strip/truncamiento. Rango técnico según campo de gasto del evento
y alias del perfil; longitud decimal limitada antes de int(), sin máximo funcional.
S7-A conserva toda validación definitiva de elegibilidad, saldo y overflow.

Cada GET nuevo genera secrets.token_urlsafe(32). POST conserva exactamente la
clave recibida, también en errores; ausente/inválida es 400, sin regeneración.
Sin almacenamiento propio de claves en sesión. CSRF es protección independiente.
POST válido llama una vez a allocate_stat_points: sin prevalidar saldo, Actual,
configuración o reglas, ni siquiera consultar overview antes del servicio.
S7-A es el único propietario; sin transacciones/escrituras de negocio en la vista.

Nuevo/replay generan mensajes Django distintos y redirect 302 a asignación,
POST/Redirect/GET. El GET posterior recarga estado y genera formulario nuevo, sin
alterar la clave anterior. Replay histórico funciona tras otras asignaciones/S3
y cambios/retirada de configuración; no reinterpreta snapshots.

## HTTP seguro

| Situación | HTTP |
| --- | --- |
| GET válido | 200 |
| Anónimo | 302 a LOGIN_URL con next estándar |
| POST nuevo/replay | 302 con mensajes distintos |
| Formulario inválido o InvalidAttributeError/InvalidPointsError/InvalidAllocationKeyError | 400 |
| Perfil ausente, InvalidAllocationProfileError/InvalidQueryProfileError | 404 |
| IneligibleStageError/InsufficientPointsError/AllocationConflictError | 409 |
| InconsistentAllocationStateError/InconsistentQueryStateError | 409 |
| AllocationOverflowError | 409, incompatibilidad técnica controlada |
| InvalidAllocationConfigurationError/AllocationDatabaseError/ProgressQueryDatabaseError/DatabaseError | 503 |
| Método no admitido | 405 |
| CSRF inválido/ausente | 403 estándar Django |

CSRF conserva la precedencia normal del middleware/decorador sobre POST.
Mensajes genéricos sin trazas, SQL, claves ni identificadores ajenos; sin capturar
Exception ni errores arbitrarios de programación. Nunca éxito antes del servicio.
Error POST renderiza formulario vinculado conservando clave, sin S4-A ni reparación;
stats disponibles al volver mediante GET. Mensajes/sesión Django pueden escribir
su propio estado, distinto del negocio.

## Presentación y límites

Ruta local allocate-points/, ecomotor:allocate-points; ecomotor:progress intacta.
No montaje en config/urls.py. Template autónomo semántico/autoescapado con stats,
saldo, formulario, csrf_token, mensajes, errores y enlace de regreso. Progress
solo añade enlace, sin historial de asignaciones, JS, CSS externo o base global.
Pruebas HTTP con URLconf del propio módulo y Client(enforce_csrf_checks=True),
token real, aislamiento de usuarios, validación, PRG/replay y conservación de datos.
Fixtures ficticios; S1–S7-A, Rewards F1/DOC-6/F2-A, modelos/migraciones y otros
equipos intactos. Core/login/montaje/home/base compartida, configuración oficial,
conservación y contratos globales pendientes. No iniciar F2-A.
