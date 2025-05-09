import datetime
import os
from decimal import Decimal
from pathlib import Path

import dj_database_url
import sentry_sdk
from celery.schedules import crontab
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration

from league.utils.egd import Location, TimeLimit, ByoYomi, TournamentClass


def env(key, as_bool=False, as_list=False, as_int=False, required=True, default=None):
    try:
        value = os.environ[key]
        if not value:
            raise ValueError()
        elif as_bool:
            return value.lower() == "true"
        elif as_list:
            return value.split(",")
        elif as_int:
            return int(value)
        return value
    except (KeyError, ValueError):
        if default is not None:
            return default
        if not required:
            return None
        raise ImproperlyConfigured("missing environment variable: {0}".format(key))


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", as_bool=True, default=True)

ALLOWED_HOSTS = [env("DOMAIN", default="*")]

DOMAIN = env("DOMAIN", default="127.0.0.1:8000")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "misc",
    "league",
    "review",
    "timetable",
    "crispy_forms",
    "crispy_bootstrap5",
    "debug_toolbar",
    "django_countries",
    "rest_framework",
    "utils",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "misc.middleware.ProfilingMiddleware",
]

ROOT_URLCONF = "iglo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "iglo.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

IGLO_DB_PORT = env("IGLO_DB_PORT", default="5432")
IGLO_DB_URL = f"postgres://postgres:postgres@localhost:{IGLO_DB_PORT}/postgres"
DATABASES = {
    "default": dj_database_url.config(default=IGLO_DB_URL),
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "pl"

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_L10N = False

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "../../data/static"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "../../data/media"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TIME_FORMAT = "H:i"
DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"

AUTH_USER_MODEL = "accounts.User"

LOGIN_REDIRECT_URL = "/"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_URL = "/login"

if "SENTRY_DSN" in os.environ:
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"), integrations=[DjangoIntegration()], traces_sample_rate=1.0, send_default_pii=True
    )

DEFAULT_GAME_TIME = datetime.time(16, 0)

DEFAULT_FROM_EMAIL = "IGLO <no-reply@szalenisamuraje.org>"
REPLY_TO_EMAIL = "internetowagoligao@gmail.com"

if "EMAIL_HOST" in os.environ and "EMAIL_HOST_USER" in os.environ and "EMAIL_HOST_PASSWORD" in os.environ:
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INTERNAL_IPS = [
    "127.0.0.1",
]

EGD_SETTINGS = {
    "CLASS": TournamentClass.D,
    "NAME": "Internet Go League IGLO - Season #{season_number} - Group {group_name}",
    "LOCATION": Location(
        country="PL",
        city="OGS",
    ),
    "KOMI": Decimal("6.5"),
    "TIME_LIMIT": TimeLimit(
        basic=30,
        byo_yomi=ByoYomi(
            duration=30,
            periods=3,
        ),
    ),
}

COUNTRIES_FIRST = [
    "PL",
]

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env("CELERY_TASK_ALWAYS_EAGER", default=True, as_bool=True)

# Periodic task schedules uses the UTC time zone
CELERY_BEAT_SCHEDULE = {
    "send-upcoming-games-reminder": {
        "task": "league.tasks.send_upcoming_games_reminder",
        "schedule": crontab(minute=0, hour='*'),
    },
    "send-delayed-games-reminder": {
        "task": "league.tasks.send_delayed_games_reminder",
        "schedule": crontab(hour="8", minute="0"),
    },
    "mark-overdue-games-as-unplayed": {
        "task": "league.tasks.mark_overdue_games_as_unplayed",
        "schedule": crontab(minute="15", hour='*'),
    }
}

AI_SENSEI = {
    "AUTH_URL": env("AI_SENSEI_AUTH_URL", required=False),
    "SERVICE_URL": env("AI_SENSEI_SERVICE", required=False),
    "EMAIL": env("AI_SENSEI_EMAIL", required=False),
    "PASSWORD": env("AI_SENSEI_PASSWORD", required=False),
}

OGS_GAME_LINK_REGEX = r"https:\/\/online-go\.com\/game\/(\d+)"
OGS_SGF_LINK_FORMAT = "https://online-go.com/api/v1/games/{id}/sgf"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "misc.middleware": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

LANGUAGES = [
    ("pl", "Polski"),
    ("en", "English"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

ENABLE_AI_ANALYSE_UPLOAD = env("ENABLE_AI_ANALYSE_UPLOAD", as_bool=True, default=False)
ENABLE_UPCOMING_GAMES_REMINDER = env("ENABLE_UPCOMING_GAMES_REMINDER", as_bool=True, default=True)
ENABLE_DELAYED_GAMES_REMINDER = env("ENABLE_DELAYED_GAMES_REMINDER", as_bool=True, default=False)
ENABLE_AUTO_MARK_UNPLAYED_GAMES = env("ENABLE_AUTO_MARK_UNPLAYED_GAMES", as_bool=True, default=True)
ENABLE_PROFILING = env("ENABLE_PROFILING", as_bool=True, default=False)
FAST_IGOR = env("FAST_IGOR", as_bool=True, default=False)

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}

# Small IGOR_MAX_STEPS is useful when CELERY is eager and we want just some fast iteration for IGoR recalculation.
# In debug mode, limit to 30 iterations for faster results during development
if FAST_IGOR:
    IGOR_MAX_STEPS = env("IGOR_MAX_STEPS", default=30, as_int=True)
else:
    IGOR_MAX_STEPS = env("IGOR_MAX_STEPS", default=1000, as_int=True)
IGOR_CONFIG = {
    'season_rating_stability': 0.5,
    'smoothing': 0.25,
    'initial_lr': 1.0,
    'do_log': True,
    'max_steps': IGOR_MAX_STEPS,
    'winner_prior_rating': 2000.0,
    'loser_prior_rating': 2000.0,
    'winner_prior_match_count': 0.0,
    'loser_prior_match_count': 0.0,

}
