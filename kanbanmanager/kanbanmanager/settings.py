import os
from pathlib import Path

import environ

# 1) Базовый путь проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# 2) Инициализируем django-environ
env = environ.Env(
    DEBUG=(bool, False)
)

# Локально читаем .env, если файл существует
env_file = BASE_DIR / '.env'
if env_file.exists():
    env.read_env(env_file)


# 3) Секретный ключ и режим отладки
SECRET_KEY = env('SECRET_KEY', default='dev-secret-key-please-replace-in-production')
DEBUG      = env('DEBUG')

# 4) ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# 5) Приложения и middleware
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # отдача статики
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 6) URL-конфиг и шаблоны
ROOT_URLCONF = 'kanbanmanager.urls'

TEMPLATES = [
    {
        'BACKEND':  'django.template.backends.django.DjangoTemplates',
        'DIRS':     [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS':  {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kanbanmanager.wsgi.application'

# 7) База данных из переменных окружения
DATABASES = {
    'default': env.db(),  # прочитает DATABASE_URL
}

# 8) Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 9) Локализация
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE     = 'Asia/Almaty'
USE_I18N      = True
USE_TZ        = True

# 10) Статические файлы
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'main' / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'

# 11) Медиа-файлы
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 12) Авторизация/перенаправления
LOGIN_REDIRECT_URL = 'main:index'
LOGIN_URL          = 'login'

# 13) Поле по умолчанию для моделей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
