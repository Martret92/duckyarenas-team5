# DuckyArenas · Equipo 5

Repositorio de integración del Equipo 5. DAR3 conserva autoridad funcional.
Las decisiones internas no sustituyen acuerdos de Óscar, Core u otros propietarios.
Equipo 0 es responsable de Core, User, autenticación y montaje global.

## Estado actual

ALFA-A-01 parte de develop `9c90020002d5fc23384377dd588cea1776c83df8`, con
[ALFA-A-DOC-01 / PR #107](https://github.com/Martret92/duckyarenas-team5/pull/107)
integrada. Implementa una primera alfa **de consulta Ecomotor V1**, todavía sin
montaje global ni ratificación externa de Óscar/Core.

| Área | Disponible | Límite |
| --- | --- | --- |
| Ecomotor V1 | Progresión, inicialización S2-A, concesión histórica XP/nivel/evolución S3, consultas S4-A, páginas e historiales S5/S9/S10, asignación S7/S8 y servicios posteriores documentados. | S3 V1 sigue único escritor XP activo. Servicios locales no certifican cifras oficiales ni integración global. |
| Alfa V1 | Tres páginas autenticadas de lectura, navegación sin asignación y montaje aislado testeable. | No incluida en config/urls.py; Core debe montar rutas, login y menú. |
| Ecomotor objetivo | Validadores, cálculos y componentes preparatorios de catálogo documentados. | No activan escritor XP productivo, autorización USE-01B o procedencia TRACE-01B; no reinterpretan V1. |
| Demo persistente Rewards–Bank | XP/evoluciones ficticias, opciones/stats y Rewards XP, NO_REWARD y cinco monedas ficticias con Wallet/Transaction locales. | SQLite y settings exclusivos; no F2-A productivo ni economía/autenticación Core. |
| Duckies, Bank y Shop | Apps y pruebas propias presentes. | Esta alfa no las modifica ni afirma integración global entre equipos. |

La V1 completa conserva cuatro rutas y asignación GET/POST con CSRF. Sus atributos
siguen siendo ATK, DEF, LOG, SPE, VEL e INT, sin reinterpretación como CUACK.
S6-A carga/diagnostica candidatos sin instalarlos; la alfa no inventa bases,
umbrales o presupuestos. Los incrementos y sus cortes históricos están en
[arquitectura](docs/architecture.md), [decisiones](docs/decisions.md) y
[pendientes](docs/pending-decisions.md).

## Requisitos y preparación de tests

Git y Python disponibles; entorno verificado con Python 3.12. requirements.txt
fija **Django 5.2.17**. Ejemplo PowerShell desde la raíz, sin cambiar políticas de
ejecución ni configuración global:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test apps.ecomotor.test_alpha_views
```

Django prepara y destruye sus bases de tests; los fixtures son sintéticos.
No hace falta ejecutar migrate ni seeds sobre SQLite personales para correr tests.
No usar credenciales/datos reales o instalar cifras ficticias como oficiales.
Los settings normales son de desarrollo: no publicar el servidor ni reutilizar
su clave de desarrollo como configuración productiva.

## Primera alfa Ecomotor V1

[Contrato técnico](docs/contracts/ecomotor-alpha-v1.md).
`apps.ecomotor.alpha_urls` declara exactamente tres patrones relativos:

| Ruta relativa | Nombre reversible | Contenido |
| --- | --- | --- |
| `progress/` | `ecomotor:progress` | XP histórica, nivel/etapa, stats base/saldo, objetivos disponibles y diez concesiones recientes. |
| `xp-history/` | `ecomotor:xp-history` | Historial paginado de XP, snapshots y referencias causales de evolución. |
| `allocation-history/` | `ecomotor:allocation-history` | Historial paginado de asignaciones existentes; no permite gastar puntos. |

El URLconf fija alpha_mode=True en servidor. Las vistas trasladan el modo al
contexto para evitar reversos de asignación en base, progreso e historial vacío.
GET/POST no eligen el modo. La V1 completa conserva el valor predeterminado y
sus enlaces/formularios anteriores.

Solo GET/HEAD, login_required y propietario desde request.user. IDs del navegador
no seleccionan perfil. La alfa no inicializa, concede XP, asigna ni repara datos.
Requiere usuario autenticado, perfil V1 y CharacterStats previamente preparados
por un proceso autorizado. Perfil ausente: 404; incoherencia: 409; cursor inválido:
400; fallo BD: 503; método no admitido: 405 tras autenticación y middleware.
El anónimo se redirige al LOGIN_URL con next: eso no prueba que el login exista.
Los objetivos no calculables se muestran sin cifras inventadas.

### Integración orientativa de Core

**No existe una URL pública de alfa bajo config.urls**, que solo monta admin.
No hay settings ni login nuevos. Los tests montan un prefijo aislado y crean
fixtures: su URLconf no es un entorno de arranque manual ni prepara perfiles
al ejecutar runserver.

Core debe acordar prefijo, namespace, LOGIN_URL efectivo, retorno next y menú.
Después puede incluir el módulo en su código propietario. Ejemplo orientativo,
no aplicado al repositorio ni confirmado como prefijo definitivo:

```python
from django.urls import include, path

urlpatterns = [
    path("prefijo-acordado/", include("apps.ecomotor.alpha_urls")),
]
```

El menú enlaza por reverse("ecomotor:progress"), sin cuarta página raíz. Un montaje
simultáneo de alfa y V1 completa requiere coordinar namespaces y reversos, sin
dos instancias ambiguas ecomotor. Core conserva sus rutas, middleware y auth;
comprobar templates/staticfiles y el asset `ecomotor/ecomotor.css`.

Tras el montaje acordado y la preparación autorizada del perfil, arranque local:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

La URL será el prefijo acordado más una ruta relativa de la tabla. **Sin ese
montaje, runserver no hace aparecer la alfa.** Antes de presentarla a Óscar faltan
login/retorno operativos, menú y navegación global verificados y datos de revisión
autorizados. Pasar tests locales no acredita integración ni aceptación externa.

## Comprobaciones y regresiones

Desde la raíz; se puede sustituir el ejecutable por `py` si selecciona el entorno:

```powershell
.\.venv\Scripts\python.exe manage.py test apps.ecomotor.test_alpha_views
.\.venv\Scripts\python.exe manage.py test apps.ecomotor.test_progress_views apps.ecomotor.test_xp_history_views apps.ecomotor.test_stat_allocation_history_views apps.ecomotor.test_stat_allocation_views apps.ecomotor.test_progress_queries apps.ecomotor.test_stat_allocation_queries apps.ecomotor.test_xp_service apps.ecomotor.test_stat_allocation
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py test --settings=apps.ecomotor.target_persistent_demo_settings
.\.venv\Scripts\python.exe manage.py check --settings=apps.ecomotor.target_persistent_demo_settings
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
git diff --check
```

La suite habitual no instala la app auxiliar persistente. El runner exclusivo
conserva dos fases: suite habitual con registro normal y suite explícita de demo
con su app instalada. Incluye fixtures file-backed/subprocesos que crean y migran
solo SQLite desechables para Bank/default, concurrencia y compatibilidad histórica.
Informar los casos hijos separados de los tests padre, sin sumarlos dos veces;
no reutilizar cifras antiguas como resultados nuevos.

makemigrations --check --dry-run no genera ni aplica migraciones, pero puede
consultar el historial de la conexión configurada. Para evitar abrir bases
personales se configura una SQLite temporal en el proceso de comprobación, como
hacen los fixtures exclusivos. No ejecutar migrate/seed personales como regresión.

## Laboratorios objetivo independientes

La [demo navegable objetivo](docs/contracts/ecomotor-target-demo-v1.md) y la
[demo persistente](docs/contracts/ecomotor-target-persistent-demo-v1.md) no son
la alfa V1 ni usan su autenticación. El laboratorio persistente reside en
`apps/ecomotor/ecomotor_target_demo/`, app auxiliar ecomotor_target_demo instalada
solo con settings exclusivos. Conserva `instance/target_persistent_demo.sqlite3`,
apertura protegida y sesiones locales. La alfa no lo lee ni modifica.

Para un laboratorio **ya preparado** con su procedimiento aislado:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8002 --settings=apps.ecomotor.target_persistent_demo_settings
```

URL local `http://127.0.0.1:8002/demo/objetivo-persistente/`, solo con esos settings.
Preparación explícita, respaldo de bases anteriores, migraciones 0001–0004 y
límites están en los contratos del [Paso 2](docs/contracts/ecomotor-target-persistent-demo-v1.md),
[Paso 3](docs/contracts/ecomotor-target-playable-persistent-demo-v1.md) y
[Rewards–Bank](docs/contracts/ecomotor-target-demo-rewards-bank-v1.md).
No aplicar migraciones automáticamente a una partida personal ni considerar un
catálogo congelado o sus monedas ficticias autorización económica/funcional.

## Pendientes y documentación

A3.5, USE-01B, TRACE-01B, Rewards F2-A productivo, valores oficiales e integración
siguen abiertos. La alfa no activa Ecomotor objetivo ni resuelve conservación o
migración legacy, inventario, equipamiento o permisos globales.

- [Arquitectura y alcance](docs/architecture.md).
- [Decisiones internas y autoridad](docs/decisions.md).
- [Dependencias pendientes](docs/pending-decisions.md).
- [ERD común y diccionarios PR07](docs/ERD.md).
- [Plan del Equipo 5](docs/team5-work-plan.md).

Los requisitos DAR3 y referencias se recogen en esos documentos, sin inventar
nuevos acuerdos del profesor. develop es la rama de integración; los cambios
se revisan en PR desde feature/*, fix/* o docs/* antes de integrar con Equipo 0.
