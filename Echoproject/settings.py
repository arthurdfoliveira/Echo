from pathlib import Path
import os
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

TARGET_ENV = os.getenv('TARGET_ENV')
NOT_PROD = not TARGET_ENV.lower().startswith('prod')

if NOT_PROD:
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = '<django-insecure-t1g921njm7@gxvv!whqs4s4a*x017-4sf+s_wh2fh!8$d!e6>'
    ALLOWED_HOSTS = []
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', '0').lower() in ['true', 't', '1']
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(' ')
    CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS').split(' ')

    SECURE_SSL_REDIRECT = \
        os.getenv('SECURE_SSL_REDIRECT', '0').lower() in ['true', 't', '1']

    if SECURE_SSL_REDIRECT:
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DBNAME'),
            'HOST': os.environ.get('DBHOST'),
            'USER': os.environ.get('DBUSER'),
            'PASSWORD': os.environ.get('DBPASS'),
            'OPTIONS': {'sslmode': 'require'},
        }
    }
    
# Application definition

# --- APPS INSTALADOS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # --- APPS DE TERCEIROS ---
    "whitenoise.runserver_nostatic",

    # --- SEUS APPS ---
    'Echo_app',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Whitenoise para arquivos estáticos em produção
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# --- TEMPLATE CONFIG ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # caso queira usar templates globais, adicione aqui
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

# --- URL RAIZ ---
ROOT_URLCONF = 'Echoproject.urls'

# --- STATIC FILES ---
# STATIC_URL = "static/"
STATIC_URL = os.environ.get('DJANGO_STATIC_URL', "/static/")
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = ('whitenoise.storage.CompressedManifestStaticFilesStorage')
STATICFILES_DIRS = [BASE_DIR / "static"]  # opcional, se você tiver uma pasta 'static' no projeto

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- MEDIA FILES (UPLOADS) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- LOGIN CONFIG ---
LOGIN_URL = 'Echo_app:entrar'  # redireciona para a página de login se usuário não autenticado

# ==============================================================
# 📧 EMAIL SETTINGS (NECESSÁRIO PARA REDEFINIÇÃO DE SENHA) 📧
# ==============================================================

# LÊ TODAS AS VARIÁVEIS DE AMBIENTE RELACIONADAS AO E-MAIL PRIMEIRO
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ['true', 't', '1']
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

if NOT_PROD:
    # 🌟 ALTERAÇÃO APLICADA: Usa SMTP para testar o envio real em desenvolvimento.
    # Certifique-se de que suas variáveis no .env estão corretas (Host, User, Password).
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' 
    
    # Em desenvolvimento, usamos um valor padrão que não causa NameError
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'test@example.com')
else:
    # Configurações reais para envio em produção
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    # EM PRODUÇÃO, USAMOS EMAIL_HOST_USER como fallback (aqui ELE ESTÁ DEFINIDO)
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Configuração para Redirecionamento de Senha (Password Reset)
# Após o usuário concluir a redefinição de senha, ele será redirecionado para a tela de login.
PASSWORD_RESET_COMPLETE_REDIRECT_URL = 'Echo_app:entrar'


# --- INTERNACIONALIZAÇÃO (caso ainda não tenha) ---
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_TZ = True

# --- DEFAULT AUTO FIELD ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'