import os
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = int(os.environ.get("DEBUG", default=0))

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CONN_MAX_AGE = 3600

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", default='*').split(" ")
#ALLOWED_HOSTS = ['*']
# Raw path to fingerprint and attack vector data
# pcap and json are stored here
RAW_PATH = "/home/ddosdb/ddosdb-data/"

# Which email should be used for access requests
ACCESS_REQUEST_EMAIL = ""

# ReCAPTCHA keys for access requests
RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = ""

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "ddosdb"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "ddosdb"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

# Location where HTML are stored
STATIC_ROOT = '/home/ddosdb/ddosdb-static/'

# MongoDB URI
MONGODB="mongodb:27017"

# CELERY STUFF
CELERY_BROKER_URL = 'pyamqp://rabbitmq:5672'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Amsterdam'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_RESULT_EXPIRES = 604800  # Expire after a week
CELERY_IMPORTS = ('ddosdb.tasks',)
