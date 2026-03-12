"""
Django settings para myproject.
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# ── Rutas base ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# SEGURIDAD

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG       = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

AUTH_USER_MODEL = "usuarios.Usuario"

# APLICACIONES


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    # Propias
    'usuarios',
]

# MIDDLEWARE

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',         # CORS siempre primero
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF    = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'

# TEMPLATES

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "front"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# BASE DE DATOS

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME'),
        'USER':     os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':     os.getenv('DB_HOST', 'localhost'),
        'PORT':     os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# VALIDACIÓN DE CONTRASEÑAS


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# INTERNACIONALIZACIÓN


LANGUAGE_CODE = 'es-co'
TIME_ZONE     = 'America/Bogota'
USE_I18N      = True
USE_TZ        = True

# ARCHIVOS ESTÁTICOS


STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # para collectstatic en producción

STATICFILES_DIRS = [
    BASE_DIR / "front",
]

# DJANGO REST FRAMEWORK

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':  '20/hour',   # no autenticados
        'user':  '200/day',   # autenticados (subido de 100 para no bloquear el dashboard)
        'login': '10/hour',   # throttle especial para login
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Mostrar errores legibles en desarrollo
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

}

# En tests desactivar throttling para no contaminar los resultados
if len(sys.argv) > 1 and sys.argv[1] == 'test':
    REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []

# SIMPLE JWT

SIMPLE_JWT = {
    # Tiempos de vida
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=30),   # subido de 15 para mejor UX
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),        # subido de 1 día

    # Seguridad
    'ROTATE_REFRESH_TOKENS':   True,   # cada refresh genera uno nuevo
    'BLACKLIST_AFTER_ROTATION': True,  # el token viejo queda inválido
    'UPDATE_LAST_LOGIN':        True,  # actualiza last_login del usuario

    # Tipo de token
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME':  'HTTP_AUTHORIZATION',

    # Claims del token (info que viaja dentro del JWT)
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    # Algoritmo de firma
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# CORS

# Orígenes permitidos en desarrollo
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5500",    # Live Server de VS Code
    "http://127.0.0.1:5500",   # Live Server alternativo
    "http://localhost:8080",
    "http://127.0.0.1:8000",
]

# En producción cambiar por el dominio real y eliminar los de localhost
# CORS_ALLOWED_ORIGINS = ["https://tudominio.com"]

# Headers que el frontend puede enviar
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Métodos permitidos
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Permitir cookies / credentials en requests CORS
CORS_ALLOW_CREDENTIALS = True

# SEGURIDAD ADICIONAL (producción)


if not DEBUG:
    # HTTPS
    SECURE_SSL_REDIRECT              = True
    SECURE_HSTS_SECONDS              = 31536000   # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
    SECURE_HSTS_PRELOAD              = True
    SECURE_BROWSER_XSS_FILTER        = True
    SECURE_CONTENT_TYPE_NOSNIFF      = True
    SESSION_COOKIE_SECURE            = True
    CSRF_COOKIE_SECURE               = True
    X_FRAME_OPTIONS                  = 'DENY'


# LOGGING


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # ── Formatos ───────────────────────────
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} | {name} | {message}',
            'style':  '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style':  '{',
        },
        'request': {
            'format': '[{levelname}] {asctime} | {name} | {message}',
            'style':  '{',
        },
    },

    # ── Filtros ────────────────────────────
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },

    # ── Handlers ───────────────────────────
    'handlers': {
        # Consola — solo en desarrollo
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
            'filters':   ['require_debug_true'],
        },

        # Log general de la API
        'file_api': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    os.path.join(BASE_DIR, 'logs', 'api.log'),
            'maxBytes':    1024 * 1024 * 5,   # 5 MB
            'backupCount': 5,
            'formatter':   'verbose',
        },

        # Log de errores (WARNING+)
        'file_errores': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    os.path.join(BASE_DIR, 'logs', 'errores.log'),
            'maxBytes':    1024 * 1024 * 5,
            'backupCount': 5,
            'formatter':   'verbose',
            'level':       'WARNING',
        },

        # Log de seguridad (intentos de login, bloqueos)
        'file_seguridad': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    os.path.join(BASE_DIR, 'logs', 'seguridad.log'),
            'maxBytes':    1024 * 1024 * 2,
            'backupCount': 10,
            'formatter':   'verbose',
        },
    },

    # ── Loggers ────────────────────────────
    'loggers': {
        # Django interno
        'django': {
            'handlers':  ['console', 'file_errores'],
            'level':     'WARNING',
            'propagate': False,
        },

        # Requests HTTP (útil para ver todas las peticiones)
        'django.request': {
            'handlers':  ['console', 'file_api'],
            'level':     'INFO',
            'propagate': False,
        },

        # Tu app de usuarios — auth y seguridad
        'usuarios': {
            'handlers':  ['console', 'file_api', 'file_seguridad'],
            'level':     'INFO',
            'propagate': False,
        },

        # SQL queries (solo en DEBUG, útil para detectar N+1)
        'django.db.backends': {
            'handlers':  ['console'],
            'level':     'DEBUG' if DEBUG else 'WARNING',
            'filters':   ['require_debug_true'],
            'propagate': False,
        },
    },
}

# Crear carpeta logs si no existe
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


SPECTACULAR_SETTINGS = {
    'TITLE': 'API Sistema Académico',
    'DESCRIPTION': 'API para gestión académica universitaria',
    'VERSION': '1.0.0',
}