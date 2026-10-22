# A3-TARGET-DEMO-01 · Demo navegable del Ecomotor objetivo

**Aprobación interna Equipo 5 / 02C-2: 22/10/2026. Implementación en PR para revisión.**
DAR3 mantiene la autoridad funcional. La demo no constituye integración global,
publicación, autorización de catálogo ni activación del escritor objetivo.

## Alcance y datos sintéticos

Una página independiente muestra siete épocas: Prehistórico, Griego, Romano,
Medieval, Renacentista, Revolución Industrial y Siglo XX. Desde nivel 8 permite
visualizar doce opciones: esas siete históricas (opciones jugables, no simples
vestimentas) y Developer, Ciber, Sistemas, Data IA y Gamer. Sus códigos `demo-*`
son locales y provisionales. No cambian códigos o datos V1.

El catálogo `synthetic-target-web-demo`, versión `demo-2026-10-22-v1`, contiene
nueve niveles con umbrales **ficticios** 0, 100, 200, 300, 400, 500, 600, 700 y
900 XP. Los siete primeros coinciden con las épocas. Nivel 8 desbloquea elección,
sin octava época; nivel 9 conserva Siglo XX. No son cifras oficiales de Óscar.

El reparto reutiliza A4.1 (`ATK, DEF, VEL, INT, LOG, CUACK`) con bases cero
exclusivamente sintéticas y **45 puntos provisionales internos por opción**,
según A4-PRESUPUESTO-PROV-01. Permite gasto completo, parcial o cero. Muestra
incrementos, usados y restantes; no estadísticas efectivas oficiales. No llama
a la resolución A4.4.1 ni fabrica una fuente confiable.

Los siete placeholders locales de vestimenta son conceptuales, sin diseños
finales de Henry ni integración Duckies. Durante la progresión se muestra la
época actual; tras visualizar una especialización tecnológica se pueden explorar
las vestimentas anteriores desbloqueadas. No hay equipamiento, propiedad o inventario.

## Ejecución Windows / PowerShell

Desde la raíz del repositorio, con sus dependencias instaladas:

```powershell
New-Item -ItemType Directory -Force instance | Out-Null
py manage.py migrate --settings=apps.ecomotor.target_demo_settings
py manage.py seed_target_demo_catalog --settings=apps.ecomotor.target_demo_settings
py manage.py runserver 127.0.0.1:8001 --settings=apps.ecomotor.target_demo_settings
```

Abrir **http://127.0.0.1:8001/demo/objetivo/**. Sumar 700 XP desde cero para
explorar nivel 8, elegir cualquiera de las doce opciones y comprobar un reparto.
Sumar otras 200 XP permite ver nivel 9. Reiniciar con el botón de la página o
el enlace de cabecera; una nueva visita GET comienza desde cero.

La única base es `instance/target_demo.sqlite3`, ignorada por Git. No hay fallback
a `db.sqlite3`. El comando exige el marcador `A3-TARGET-DEMO-01`, ruta exacta,
alias interno configurado y SQLite IMMEDIATE/timeout=5; rechaza memoria, URI y
sobrescritura `OPTIONS.database`. La carpeta se crea explícitamente antes de
migrar. Sin archivo migrado, la vista rechaza el entorno; con catálogo ausente
o incompatible devuelve 503 sin instalarlo. No se exponen admin, Core o V1.
A4-DEMO-01, su URLconf y sus settings permanecen independientes e intactos.

El comando es el único componente de la demo que inserta el catálogo: dentro
de una transacción instala o comprueba exactamente las mismas filas y valida
mediante el lector ORM/A1.1. Es idempotente para ese catálogo preparatorio exacto;
rechaza diferencias, versiones adicionales o congeladas sin repararlas. No crea
usuarios, perfiles ni configuraciones oficiales, ni congela/publica versiones.

Para eliminar **solo la base sintética aislada**, detener este servidor, confirmar
que la ruta corresponde a esta demo y ejecutar desde la raíz:

```powershell
Remove-Item -LiteralPath .\instance\target_demo.sqlite3
```

Repetir después migrate y seed con los settings exclusivos. No eliminar otras
bases ni ejecutar estos pasos con settings normales. El estado firmado del
navegador puede descartarse con el enlace «Empezar de cero».

## Cálculo, seguridad y límites

- GET inicial/sin incremento: catálogo validado bajo una lectura IMMEDIATE y
  `calculate_target_progression(xp, xp, snapshot)`; sin concesión ficticia positiva.
- POST de incremento: `preview_target_xp(..., using=..., xp_before=..., amount=...)`
  y su resultado A2.1/A1.2, sin cálculo paralelo de nivel o época.
- Estado efímero firmado y fechado (máximo cuatro horas): solo XP simulada,
  opción visual y vestimenta conceptual. Firma y estructura revalidadas; nivel,
  época y elegibilidad recalculados por el servidor. No es un historial ni un
  permiso; conocer la clave de desarrollo no otorga ninguna capacidad de negocio.
- Solo GET sin parámetros y POST con campos explícitos únicos. Rechazo de campos
  extra, duplicados, estados manipulados, valores negativos, signos, espacios,
  decimales, exponentes y dígitos no ASCII. Máximo HTTP de 20 dígitos: protección
  de transporte de la demo, no límite funcional de los núcleos puros.
- CSRF real, escape HTML, sin sesiones de jugador, autenticación, perfiles o
  presupuestos/bases seleccionables desde el cliente. Acceso local al ligar
  runserver explícitamente a `127.0.0.1`; no es un servicio listo para despliegue.
- GET/POST solo leen la base de demo. No crean fixtures, cambian `frozen_at`,
  conceden XP, guardan elecciones, puntos, eventos, inventario o saldos. Las
  transacciones IMMEDIATE breves pueden bloquear escritores temporalmente.
- Una lectura no convierte el catálogo preparatorio en congelado o autorizado.
  La simulación y su selección no son trazabilidad persistente USE/TRACE.

## Verificación y dependencias

`apps/ecomotor/test_target_demo.py` prueba instalación explícita e idempotente,
rechazo de entorno/base habitual, rollback, siete épocas, doce opciones desde
nivel 8, continuidad posterior, vestimenta, reparto A4.1, delegación PREVIEW,
estado firmado, HTTP estricto, CSRF, escape, métodos y ausencia de DML/DDL en
peticiones. Regresiones A1/A2, PREVIEW y A4-DEMO-01 y suite completa requeridas
antes de entregar. Las comprobaciones visuales reales se distinguen de Test Client
en el informe de PR.

S3 V1 permanece como único escritor XP activo y no interviene en la demo.
Siguen pendientes configuración oficial de Óscar, diseños/vestimentas de Henry,
Core/A3.5, USE-01B/TRACE-01B, selección/estadísticas persistentes y activación
coordinada. Véanse [estado y bloqueos](../pending-decisions.md) y el
[contrato A3](ecomotor-transition-target-v1.md). Esta demo no los desbloquea.
