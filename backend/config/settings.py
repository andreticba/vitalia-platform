# backend/config/settings.py em 2025-12-13 18:30

import os
from pathlib import Path
from datetime import timedelta
from kombu import Queue
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Define explicitamente onde está a pasta .git (um nível acima do backend)
# Isso permite que bibliotecas de versionamento encontrem o repositório corretamente.
GIT_DIR = BASE_DIR.parent 

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# --- Aplicações ---
INSTALLED_APPS = [
    # Django Core (Daphne deve vir antes de tudo para assumir o runserver)
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # Third-party libs
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "channels",
    "django_crypto_fields.apps.AppConfig",
    "django_celery_beat",
    
    # Vitalia Apps (Core Business)
    "core",          # Identidade, DataVault, RBAC
    "medical",       # Prontuário, Planos
    "gamification",  # Pontos, Leaderboards
    "social",        # Feed, Interações
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware", # CORS antes de tudo
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Configuração ASGI/WSGI ---
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT"),
    }
}

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ---
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Cuiaba"
USE_I18N = True
USE_TZ = True

# --- Static/Media ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- REST Framework & JWT ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

# --- Celery & Redis ---
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Filas dedicadas para Vitalia (P15 - Performance)
CELERY_TASK_QUEUES = (
    Queue("default", routing_key="default"),
    Queue("ai_reasoning", routing_key="ai_reasoning"), # Para geração de planos (pesado)
    Queue("notifications", routing_key="notifications"), # Nudges e alertas
)

# --- Channels (WebSocket) ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, int(REDIS_PORT))],
        },
    },
}

# --- Security: Crypto Fields (Vital para LGPD/DataVault) ---
KEY_PATH = os.getenv("CRYPTO_KEY_PATH")
if not KEY_PATH:
    raise ImproperlyConfigured("CRYPTO_KEY_PATH must be set in .env")
# Auto-criação de chaves em modo Debug para facilitar setup
if DEBUG:
    AUTO_CREATE_KEYS = True

# --- CORS (Frontend) ---
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Configurações do Ollama AI ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL")
OLLAMA_GENERATION_MODEL = os.getenv("OLLAMA_GENERATION_MODEL")

# --- Configurações do Unstructured API ---
UNSTRUCTURED_API_URL = os.getenv("UNSTRUCTURED_API_URL")

