"""
Django settings for Prologicielsucces project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-4b4s@z1apg3h&&3w@-v^i#-096pk69q$so8x7^jlhr7&v_cv7v"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'utilisateurs',
    'mutualistes',
    'contrats',
    'centres',
    'prestations',
    'facturations',
    'rapports',
    'configurations',
    'cotisations',
    'rest_framework',
    # 'rest_framework_simplejwt',
    # 'corsheaders', 
    'rest_framework.authtoken',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = "Prologicielsucces.urls"

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

WSGI_APPLICATION = "Prologicielsucces.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db.straphael',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Abidjan"

USE_I18N = True
USE_TZ = True

CORS_ALLOW_ALL_ORIGINS = True  # Autorise tous les domaines (à restreindre en production)

from datetime import timedelta
# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = "0VsOaN--Ae5wyY2y4LJsB7ZYUjDQpW2EN86zFIHoTSS2c4rI39ACDjMlBjF8IqS7i4Y"

from datetime import timedelta

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # Expiration rapide pour plus de sécurité
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=7),      # Refresh token valable 7 jours
#     "ROTATE_REFRESH_TOKENS": True,  # 🔄 Régénérer un nouveau refresh token à chaque rafraîchissement
#     "BLACKLIST_AFTER_ROTATION": True,  # 🔒 Ancien token invalide après rotation
#     "ALGORITHM": "HS256",
#     "SIGNING_KEY": SECRET_KEY,  # 🔑 Utilise la clé secrète Django
#     "AUTH_HEADER_TYPES": ("Bearer",),
# }

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework_simplejwt.authentication.JWTAuthentication",
        'rest_framework.authentication.TokenAuthentication',
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Authentification standard
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configuration pour les fichiers médias (images)
MEDIA_ROOT = os.path.join(BASE_DIR, 'mutualistes/photos/')
MEDIA_URL = 'mutualistes/photos/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTH_USER_MODEL = 'utilisateurs.Utilisateur'  # Si vous utilisez un modèle d'utilisateur personnalisé
LOGIN_URL = '/login/'                     # URL pour rediriger en cas de non-authentification
LOGIN_REDIRECT_URL = '/'                  # URL après connexion
LOGOUT_REDIRECT_URL = '/login/'           # URL après déconnexion
