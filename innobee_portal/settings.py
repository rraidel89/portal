import os
import djcelery

djcelery.setup_loader()

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Tonny', 'lb@inprise.ec'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'innobee_portal_buzon',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '192.168.1.22',
        'PORT': '5432',
        'OPTIONS': {
        'autocommit': True,}
    },
    'test': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'innobee_proceso_facturacion',
        'USER': 'postgres',
        'PASSWORD': 'multinnovaciones*',
        'HOST': '178.32.236.89',#'142.4.207.146',
        'PORT': '5432',
    },
    'innobee': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'innobee_proceso_facturacion',
        'USER': 'postgres',
        'PASSWORD': 'multinnovaciones*',
        'HOST': '142.4.207.146',#'142.4.207.146',
        'PORT': '5432',
    },
    'dune': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'innobee_proceso_facturacion',
        'USER': 'postgres',
        'PASSWORD': 'multinnovaciones*',
        'HOST': '192.99.104.20',#'142.4.207.146',
        'PORT': '5432',
    },
    'duke': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'innobee_proceso_facturacion',
        'USER': 'postgres',
        'PASSWORD': 'multinnovaciones*',
        'HOST': '198.27.111.24',#'142.4.207.146',
        'PORT': '5432',
    },

}

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
# PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.4/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Guayaquil'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es-ec'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# MEDIA_ROOT = os.path.join(PROJECT_ROOT, '../media')
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

FILE_UPLOAD_PERMISSIONS = 0777
# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'content')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'dajaxice.finders.DajaxiceFinder'
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@6_xn3tj%iuxs0u%xh%d#0x_#$ehne*wo8mk0&amp;9su_#36(b$ec'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.csrf',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'innobee_portal.context_processors.context',
    'innobee_portal.context_processors.notificaciones',
)

# #For django-debug-toolbar
# INTERNAL_IPS = ('127.0.0.1',)
# DEBUG_TOOLBAR_CONFIG = {
# 'INTERCEPT_REDIRECTS': False,
#     'SHOW_TOOLBAR_CALLBACK': None,
#     'EXTRA_SIGNALS': [],
#     'HIDE_DJANGO_SQL': True,
#     'SHOW_TEMPLATE_CONTEXT': True,
#     'TAG': 'body',
# }

ROOT_URLCONF = 'innobee_portal.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'innobee_portal.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
    os.path.join('/home', 'sysadmin', 'innobee-docs'),
    os.path.join('/home', 'sysadmin', 'aron-docs'),
    os.path.join('/home', 'sysadmin', 'argo-docs'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.auth.models',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'dajax',
    'dajaxice',
    'selectable', # Django-Autocomplete
    'adm',
    'emisor_receptor',
    'core',    
    'wkhtmltopdf',
    'validatedfile',
    'djcelery',  # Add Django Celery
    'visits',
    'facebook_comments',
    'ckeditor',
    'imprenta_digital'
)

BROKER_URL = "amqp://guest:guest@localhost:5672//"

CELERY_ENABLE_UTC = False
CELERY_IMPORTS = ("core.tasks", )
CELERY_TIMEZONE = 'America/Guayaquil'
DJANGO_SETTINGS_MODULE = "settings"

AUTH_PROFILE_MODULE = "core.poroperador"


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.testinnobee.com'
EMAIL_HOST_USER = 'notificador@testinnobee.com'
EMAIL_HOST_PASSWORD = 'NotificadorF2014*NS'
EMAIL_PORT = 587

GRAPPELLI_ADMIN_TITLE = 'Innobee, FACTURACION ELECTRONICA'

BUZON_WS_URL = 'https://ws.innobeefactura.com/prjInbBuzonWS/Buzon'
BUZON_WS_NAMESPACE = 'http://servicio.inb.com/'
BUZON_WS_CREATE_ACTION = 'http://servicio.inb.com/crearBuzonSimple'
BUZON_WS_SEC_RUC = '1791809564001'
BUZON_WS_SEC_USER = '1791809564001'
BUZON_WS_SEC_PWD = 'Y2hhbmdlbWU='

VERSION_FINAL = False
DOMAIN_INNOBEE = 'http://localhost:8000'

CKEDITOR_UPLOAD_PATH = 'uploads/'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Full',
    },
}

PUBLIMES_WS_URL = 'http://online.publimes.com:5000/Service.svc'
PUBLIMES_WS_NAMESPACE = 'http://tempuri.org/'
PUBLIMES_WS_CREATE_ACTION = 'http://tempuri.org/IService/EnviarMensaje'
PUBLIMES_WS_EMPRESA = 'QUALITYSOFTEC'
PUBLIMES_WS_CLIENT = '122'
PUBLIMES_WS_PWD = 'QSTF5693'
PUBLIMES_WS_OPERADORA = 'C'

SFTP_HOST = '178.32.236.88'
SFTP_HOST_ARGO = 'argo.innobee.net'
SFTP_HOST_ARON = 'aron.innobee.net'

FIELD_ENCRYPTION_KEY = '@6_xn3tj%iuxs0u%xh%d#0x_#$ehneabc999'

WKHTMLTOPDF_CMD_OPTIONS = {
'quiet': True,
}