# sentinelops/settings.py
import os
import sys
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def get_env(key, default=None):
    try:
        from decouple import config
        return config(key, default=default)
    except ImportError:
        return os.environ.get(key, default)

SECRET_KEY = get_env("SECRET_KEY", "uWA9fBPF1pQNb-yA243poZIhlpgbhFN1uAH8qKme3YikfZDgj2FVunMuo_gqVYIT6io")
DEBUG = get_env("DEBUG", "True") == "True"
ALLOWED_HOSTS = get_env("ALLOWED_HOSTS", "*").split(",")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "channels",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
]

LOCAL_APPS = [
    "apps.accounts", "apps.agents", "apps.logs", "apps.events",
    "apps.rules", "apps.alerts", "apps.incidents", "apps.notifications",
    "apps.dashboard", "apps.search", "apps.reports", "apps.threat_intel",
    "apps.playbooks", "apps.scheduler", "apps.mitre", "apps.forensics",
    "apps.risks", "apps.honeypot", "apps.compliance", "apps.topology",
    "apps.ai_assistant", "apps.analytics", "apps.gamification",
    "apps.audit.apps.AuditConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sentinelops.urls"
WSGI_APPLICATION = "sentinelops.wsgi.application"
ASGI_APPLICATION = "sentinelops.asgi.application"

# ============ DATABASE ============
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default=get_env('DATABASE_URL', 'postgresql://neondb_owner:npg_mKyV6YLfaqp1@ep-late-lab-aoc78l5l-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'),
        conn_max_age=600,
        ssl_require=True
    )
}

# ============ REDIS & CACHE ============
USE_REDIS = get_env("USE_REDIS", "False") == "True"
REDIS_URL = get_env('REDIS_URL', '')

if USE_REDIS and REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        },
    }
else:
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    }
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }

# ============ REST FRAMEWORK ============
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# ============ JWT ============
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ============ CORS & CSRF ============
_cors_origins = get_env("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
if _cors_origins == "*":
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
else:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]

_csrf_origins = get_env("CSRF_TRUSTED_ORIGINS", "http://localhost:3000")
if _csrf_origins == "*":
    CSRF_TRUSTED_ORIGINS = []
else:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]



# ============ USER MODEL ============
AUTH_USER_MODEL = "accounts.User"



# ============ STATIC ============
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")



# ============ TEMPLATES ============
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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



# ============ LOGGING ============
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}



# ============ PASSWORD ============
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
]



# ============ EMAIL ============
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env("EMAIL_HOST", "localhost")
EMAIL_PORT = get_env("EMAIL_PORT", "25")
DEFAULT_FROM_EMAIL = get_env("DEFAULT_FROM_EMAIL", "shefathossain7@gmail.com")