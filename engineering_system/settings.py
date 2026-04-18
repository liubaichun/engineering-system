"""
Django settings for engineering_system project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

# 安全修复：限制允许访问的域名/IP，禁止使用*
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    # Third-party apps
    'rest_framework',
    'knox',
    'corsheaders',
    # Local apps
    'users',
    'projects',
    'tasks',
    'crm',
    'finance',
    'inventory',
    'attachments',
    'exports',
    'notifications',
    'approvals',
    'operation_logs',
    'apps.workers',
    'apps.gps_attendance',
    'apps.flow_engine',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'engineering_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'engineering_system.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'engineering_db'),
        'USER': os.environ.get('DB_USER', 'engineer'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'Engineer@2026'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

# ===================== REST Framework Configuration =====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'knox.auth.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Rate Limiting (Default Throttle Rates)
    # Three tiers: login (login attempts), register (registration), user (general API access)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/minute',      # Login attempts: 5 per minute
        'register': '30/hour',     # Registration: 30 per hour
        'user': '50/minute',      # General API: 50 per minute (lowered)
        'anon': '20/minute',      # Anonymous: 20 per minute (new)
        '敏感API': '10/minute',   # Sensitive APIs: 10 per minute (new)
    },
}

# ===================== Security Settings =====================
# Force HTTPS/SSL
SECURE_SSL_REDIRECT = False              # Redirect all HTTP to HTTPS
SECURE_HSTS_SECONDS = 31536000          # HSTS: 1 year (31536000 seconds)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # Include subdomains in HSTS
SECURE_HSTS_PRELOAD = True              # Allow HSTS preload list inclusion

# Additional Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True      # Secure cookie over HTTPS only
CSRF_COOKIE_SECURE = True        # CSRF cookie over HTTPS only
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing

# ===================== Celery Configuration =====================
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'engineering_system.settings')

# Celery Broker & Backend
CELERY_BROKER_URL = 'redis://host.docker.internal:6379/0'
CELERY_RESULT_BACKEND = 'redis://host.docker.internal:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# 缓存配置（解决Gunicorn多worker下throttle计数不共享问题）
# DRF Throttling cache
THROTTLE_CACHE = 'default'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ===================== Install Apps (add approvals) =====================
# Note: 'approvals' should be added to INSTALLED_APPS above

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://43.156.139.37',
    'https://43.156.139.37',
]
CORS_ALLOW_CREDENTIALS = True
