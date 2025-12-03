import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialise django-environ and read .env if present
env = environ.Env(
    # Required environment variables - no defaults for security
    SECRET_KEY=(str),
    ALLOWED_HOSTS=(str),
    DEBUG=(bool, False),
)
ENV_FILE = BASE_DIR / '.env'
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))

# Security / core - REQUIRED environment variables
SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

# Email configuration - CRITICAL FIX: Handle missing email config gracefully
EMAIL_HOST = env("EMAIL_HOST", default=None)

if not EMAIL_HOST:
    # Use console backend if email host is not configured (development/safe fallback)
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    EMAIL_HOST = "localhost"
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    EMAIL_PORT = 25
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
else:
    # Use SMTP backend if email host is configured
    EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)


# Email subject prefix  
EMAIL_SUBJECT_PREFIX = '[IACOL] '

# Set default from email if not provided
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='no-reply@iacol.online')
SERVER_EMAIL = env('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)

ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS').split(',')]

# Aplicaciones instaladas
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_ratelimit',
    'csp',
    'defender',
]

LOCAL_APPS = [
    'apps.authentication',
    'apps.dashboard.apps.DashboardConfig',
    'apps.agents',
    'apps.payments',
    'apps.api',
    'blog',
]

# Add django_extensions only for development
if DEBUG:
    LOCAL_APPS.insert(0, 'django_extensions')

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django_brotli.middleware.BrotliMiddleware',  # Compresión Brotli (mejor que GZIP)
    'django.middleware.gzip.GZipMiddleware',  # Compresión GZIP como fallback
    'csp.middleware.CSPMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'iacol_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'iacol_project.wsgi.application'
ASGI_APPLICATION = 'iacol_project.asgi.application'

# Base de datos - PostgreSQL for Docker environment (both DEBUG and production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='iacol'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='db'),  # Docker hostname
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Internacionalización
LANGUAGE_CODE = 'es'
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Configuración para URLs sin prefijo de idioma para el idioma por defecto
PREFIX_DEFAULT_LANGUAGE = False

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'
STATICFILES_DIRS = [BASE_DIR / 'static']
# Use compressed static files storage for better performance
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Internationalization
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS - Whitelist de orígenes permitidos (tanto desarrollo como producción)
CORS_ALLOW_ALL_ORIGINS = False  # Siempre False por seguridad

# Lista base de orígenes permitidos
base_allowed_origins = [
    origin.strip() for origin in env('CORS_ALLOWED_ORIGINS', default='').split(',') if origin.strip()
]

# Añadir orígenes de desarrollo específicos
if DEBUG:
    development_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    base_allowed_origins.extend(development_origins)

# Eliminar duplicados
CORS_ALLOWED_ORIGINS = list(set(base_allowed_origins))

# Redis y Celery
REDIS_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Cache configuration - temporarily use local memory cache due to Redis issues
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes default TTL
    }
}

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'iacol_middleware'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Django Allauth
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Logging Configuration - Production optimized
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple' if DEBUG else 'json'
        },
        'file': {
            'level': 'WARNING' if not DEBUG else 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'security.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.dashboard': {
            'handlers': ['console', 'file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
        'apps.agents': {
            'handlers': ['console', 'file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
        'apps.api': {
            'handlers': ['console', 'file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': False,
        },
    },
}

# Application URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy - New format for django-csp 4.0
CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'style-src': ("'self'", "'unsafe-inline'", "https://fonts.cdnfonts.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"),
        'script-src': ("'self'", "https://www.googletagmanager.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "https://crm.iacol.online", "'unsafe-inline'"),
        'font-src': ("'self'", "https://fonts.cdnfonts.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"),
        'img-src': ("'self'", "data:", "https:", "https://flagcdn.com", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"),
        'frame-src': ("'self'", "https://crm.iacol.online"),
        'connect-src': ("'self'", "https://crm.iacol.online", "wss://crm.iacol.online", "https://api.whatsapp.com", "https://www.google-analytics.com", "https://cdn.jsdelivr.net"),
    }
}

# Only set this to True if you're behind a proxy that sets X-Forwarded-Proto header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security settings - conditional based on DEBUG mode
if DEBUG:
    # Disable security features in development
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
else:
    # Enable security features in production
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# HSTS Settings - 1 year for production
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Ensure SecurityMiddleware is in MIDDLEWARE
if 'django.middleware.security.SecurityMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'django.middleware.security.SecurityMiddleware')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración N8N
N8N_WEBHOOK_URL = env('N8N_WEBHOOK_URL', default='http://n8n:5678/webhook/')
N8N_API_URL = env('N8N_API_URL', default='http://n8n:5678/api/v1/')

# Evolution API
EVOLUTION_API_URL = env('EVOLUTION_API_URL', default='http://evolution_api:8080')
EVOLUTION_API_KEY = env('EVOLUTION_API_KEY', default='your-api-key')
