# backend/config/celery.py

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Define o settings padrão
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('vitalia')

# Configurações com namespace CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks em todos os apps
app.autodiscover_tasks()
