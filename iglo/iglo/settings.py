import datetime
import os
from pathlib import Path

import dj_database_url
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration


def env(key, as_bool=False, as_list=False, as_int=False, required=True, default=None):
    try:
        value = os.environ[key]
        if not value:
            raise ValueError()
        elif as_bool:
            return value.lower() == 'true'
        elif as_list:
            return value.split(',')
        elif as_int:
            return int(value)
        return value
    except (KeyError, ValueError):
        if default is not None:
            return default
        if not required:
            return None
        raise ImproperlyConfigured('missing environment variable: {0}'.format(key))


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY", default="secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", as_bool=True, default=True)

ALLOWED_HOSTS = [env("DOMAIN", default="*")]

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
    "crispy_forms",
    "crispy_bootstrap5",
    "debug_toolbar",
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

DATABASES = {
    'default': dj_database_url.config(default="sqlite://./db.sqlite3"),
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

TIME_ZONE = "UTC"

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

DATE_FORMAT = "d/m/Y"
DATETIME_FORMAT = "d/m/Y H:i"

AUTH_USER_MODEL = "accounts.User"

LOGIN_REDIRECT_URL = "/"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

LOGIN_URL = '/login'

if "SENTRY_DSN" in os.environ:
    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )

DEFAULT_GAME_TIME = datetime.time(16, 0)

DEFAULT_FROM_EMAIL = "IGLO <no-reply@szalenisamuraje.org>"

if "EMAIL_HOST" in os.environ and "EMAIL_HOST_USER" in os.environ and "EMAIL_HOST_PASSWORD" in os.environ:
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


INTERNAL_IPS = [
    '127.0.0.1',
]
