
"""
Django settings for Aniscents project.
"""
import os
from pathlib import Path
import environ
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default=env('SECRET_KEY', default='django-insecure-aniscents-perfume-luxury-2024-key-change-this'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=env.bool('DEBUG', default=True), cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=','.join(env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1']))).split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    # Third party apps
    'crispy_forms',
    'crispy_tailwind',
    'django_filters',
    'ckeditor',
    'django_htmx',
    'django_countries',
    'debug_toolbar',
    # Local apps
    'accounts',
    'store',
    'cart',
    'orders',
    'dashboard',
    'reviews',
    'analytics',
    'feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'aniscents.urls'

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
                'cart.context_processors.cart',
                'store.context_processors.categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'aniscents.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=env('DATABASE_URL', default='sqlite:///db.sqlite3'))
    )
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Custom user model
AUTH_USER_MODEL = 'accounts.User'


# Authentication settings
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True

SITE_ID = 1





# Email settings
# Use console backend for development (prints emails to terminal)
# Change to 'django.core.mail.backends.smtp.EmailBackend' for production
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default=env('EMAIL_HOST', default='smtp.gmail.com'))
EMAIL_PORT = config('EMAIL_PORT', default=env('EMAIL_PORT', default=587), cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=env.bool('EMAIL_USE_TLS', default=True), cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default=env('EMAIL_HOST_USER', default=''))
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default=env('EMAIL_HOST_PASSWORD', default=''))

# Cart settings
CART_SESSION_ID = 'cart'

# Paystack settings
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default=env('PAYSTACK_SECRET_KEY', default=''))
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default=env('PAYSTACK_PUBLIC_KEY', default=''))

# Flutterwave settings
FLUTTERWAVE_SECRET_KEY = config('FLUTTERWAVE_SECRET_KEY', default=env('FLUTTERWAVE_SECRET_KEY', default=''))

# Debug toolbar
INTERNAL_IPS = ['127.0.0.1']

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
