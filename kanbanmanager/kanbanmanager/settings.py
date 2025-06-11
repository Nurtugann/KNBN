import os
from pathlib import Path
import dj_database_url

# 1) Базовый путь проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# 2) Секретный ключ и режим отладки
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'dev-secret-key-please-replace-in-production'
)
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# 3) ALLOWED_HOSTS и CSRF_TRUSTED_ORIGINS
raw_allowed = os.getenv('ALLOWED_HOSTS', '')
if raw_allowed:
    ALLOWED_HOSTS = [h.strip() for h in raw_allowed.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

raw_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in raw_csrf.split(',') if u.strip()]
else:
    CSRF_TRUSTED_ORIGINS = []

# 4) Приложения и middleware
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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # для отдачи статики
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 5) Корневой URL-конфиг
ROOT_URLCONF = 'kanbanmanager.urls'

# 6) Настройка шаблонов
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

# 7) WSGI
WSGI_APPLICATION = 'kanbanmanager.wsgi.application'

# 8) База данных из окружения через DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# 9) Валидация паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 10) Локализация
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE     = 'Asia/Almaty'
USE_I18N      = True
USE_TZ        = True

# 11) Статические файлы
STATIC_URL        = '/static/'
STATICFILES_DIRS  = [BASE_DIR / 'main' / 'static']
STATIC_ROOT       = BASE_DIR / 'staticfiles'

# 12) Медиа-файлы
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 13) Авторизация/перенаправления
LOGIN_REDIRECT_URL = 'main:index'
LOGIN_URL          = 'login'

# 14) Поле по умолчанию для моделей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
