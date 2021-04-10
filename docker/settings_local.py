import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#SECRET_KEY = 'k&4-)t-@bw3^2eyt(!2dax#%9ly804^+%k-fjbw0&hn)1tp$7c'
#FIELD_ENCRYPTION_KEYS = [
#    "f164ec6bd6fbc4aef5647abc15199da0f9badcc1d2127bde2087ae0d794a9a0b"
#]

SECRET_KEY = os.environ.get("SECRET_KEY")
FIELD_ENCRYPTION_KEYS = os.environ.get("FIELD_ENCRYPTION_KEYS")

DEBUG = int(os.environ.get("DEBUG", default=0))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler'
        },
    },
    'loggers': {
        '': {  # 'catch all' loggers by referencing it with the empty string
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# 'DJANGO_ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")
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

#ELASTICSEARCH_HOSTS = ["elasticsearch:9200"]

# Location where HTML are stored
STATIC_ROOT = '/home/ddosdb/ddosdb-static/'

# MongoDB URI
MONGODB="mongodb:27017"
