"""Entorno aislado Team5. Nunca utilizar en producción ni como configuración oficial."""
from .settings import *  # noqa
DATABASES['default']['NAME'] = BASE_DIR / 'db_team5_local.sqlite3'
INSTALLED_APPS = [
    'apps.duckies.team5_local.apps.Team5LocalConfig' if app == 'apps.duckies.apps.DuckiesConfig' else app
    for app in INSTALLED_APPS
]
TEAM5_LOCAL_ISOLATED = True
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
