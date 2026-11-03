"""Base de datos separada: NUNCA usar para producción."""
from .settings import *
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
DATABASES['default']['NAME'] = BASE_DIR / 'db_team5_demo.sqlite3'
LOGIN_URL = '/accounts/login/'

# Valores SINTÉTICOS exclusivos de esta demo; no son reglas oficiales.
from apps.ecomotor import initialization_config
initialization_config.INITIAL_CONFIGURATION = initialization_config.InitializationConfiguration(
    atk=3, def_stat=3, log_stat=3, spe=3, vel=3, int_stat=3,
    ordered_stage_codes=('PREHISTORIA','GRECIA','ROMA','MEDIEVAL','RENACIMIENTO','REVOLUCION_INDUSTRIAL','SIGLO_XX'),
)

TEAM5_DEMO_ENABLED = True

INSTALLED_APPS = [*INSTALLED_APPS, "apps.team5_demo.apps.Team5DemoConfig"]
