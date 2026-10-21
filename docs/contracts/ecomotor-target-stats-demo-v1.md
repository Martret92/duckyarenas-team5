# A4-DEMO-01 · Pantalla local de reparto de estadísticas

## Estado y autoridad

Decisión interna aprobada por Equipo 5 en 02C; implementación en PR para revisión,
no integración hasta merge autorizado. Base: develop
`22e979e8ec48fb9fb3a70716ac0da5bc745c0edb`, tras #81.
DAR3 conserva autoridad funcional. Esta demo no autoriza configuración oficial,
selección de Ducky, persistencia o activación del Ecomotor objetivo.

Separar A4-DEMO-01 de A4-PRESUPUESTO-PROV-01: esta última fija internamente
45 puntos provisionales por configuración, no una cantidad confirmada por Óscar.
[Decisiones](../decisions.md) y [A4.1](ecomotor-target-stats-validation-v1.md).

## Arranque y aislamiento

Desde la raíz del repositorio:

```powershell
py manage.py runserver 127.0.0.1:8000 --settings=apps.ecomotor.demo_settings
```

Abrir http://127.0.0.1:8000/demo/ecomotor/.
demo_settings reutiliza config.settings y cambia únicamente ROOT_URLCONF a
apps.ecomotor.demo_urls. Ese URLconf solo incluye la demostración, sin admin ni
rutas V1. Con config.settings/config.urls, la ruta de demo no existe.
El carácter local depende de este arranque explícito en loopback; no se añade
una política de autenticación, autorización o publicación global.

## Datos y pantalla

Developer, Ciber, Sistemas, Data IA y Gamer son etiquetas de demostración.
Sus identificadores demo-* son locales, no códigos canónicos ni elegibilidad
de nivel 8. ATK Ataque, DEF Defensa, VEL Velocidad, INT Inteligencia, LOG Lógica
y CUACK Cuak siguen TARGET_STAT_CODES; no reinterpretan log_stat ni spe V1.

La página independiente permite introducir seis incrementos y comprobar el
reparto. Muestra opción, puntos gastados/restantes y validación. No muestra
bases o estadísticas efectivas finales, ni botones para guardar o confirmar.
Advertencias visibles:

- «Demostración local: no se guardan datos».
- «45 puntos es un presupuesto provisional del Equipo 5».
- «Las estadísticas base y la selección definitiva todavía no están disponibles».

## Validación y seguridad

Solo GET y POST; otros métodos, incluido HEAD, devuelven 405. Acceso anónimo
sin obtener perfiles ni datos de User. CSRF real conservado en middleware,
decorador y token de formulario; no csrf_exempt ni sesiones de negocio.

demo_forms exige option válida y exactamente los seis campos de incremento,
sin duplicados y sin campos adicionales salvo csrfmiddlewaretoken, también
único si está presente. Un campo ausente/vacío no recibe cero por defecto.
Textos numéricos: únicamente dígitos ASCII, sin espacios, signos, decimales,
exponentes o conversiones permisivas. Máximo técnico HTTP de diez dígitos,
comprobado antes de int(); no es máximo funcional del núcleo Ecomotor.

Tras validar HTTP se llama a validate_target_stats con seis bases cero sintéticas,
incrementos canónicos y DEMO_BUDGET=45 del servidor. No se recibe presupuesto,
bases, perfil, nivel o versiones desde el navegador ni mediante campos ocultos.
Los ceros son un requisito técnico para validar reparto con A4.1, no bases
oficiales. No se invocan A4.2.1/A4.3.1 ni se duplica la aritmética de presupuesto.

Errores públicos estructurales/numéricos/exceso de A4.1 se traducen a errores
comprensibles sin detalles internos. POST inválido: 400 y entradas escapadas;
válido: 200 en la misma página, mostrando solo los totales obtenidos de A4.1.
No ORM, conexiones, almacenamiento, concesiones XP, eventos, recompensas,
estadísticas persistentes o llamadas a servicios V1. La cookie CSRF no almacena
la propuesta ni crea una sesión de jugador.

## Pruebas y pendientes

27 tests SimpleTestCase (BD prohibida) cubren pantalla, opciones/atributos,
repartos completos/parciales/cero, manipulación HTTP y duplicados, escape,
delegación pública, CSRF real, métodos, settings y rutas aisladas, anonimato
y ausencia de llamadas a servicios anteriores. Ejecuciones reales con settings
normales y de demo, suite completa y comprobación visual se detallan en la PR.

Siguen pendientes bases definitivas, fuente y resolución confiable, consumidores,
Core/A3.5 y persistencia/activación coordinada del objetivo. Los acuerdos con
Henry, Rewards, Shop y Bank no se resuelven por esta pantalla. V1/S3 permanece
intacto e INITIAL_CONFIGURATION no se modifica. No modelos ni migraciones.
