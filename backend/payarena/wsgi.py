import os
from django.core.wsgi import get_wsgi_application
from decouple import config

if config('env', '') == 'prod' or os.getenv('env', 'dev') == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payarena.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payarena.settings.dev')

application = get_wsgi_application()
