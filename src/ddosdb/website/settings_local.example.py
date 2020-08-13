# This file contains the machine-specific configuration for DDoSDB

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'm^nfx&3zrbgx1(kuk@dd^4)9atr-^28t5rkyur#hev$&n+#1kn'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Which hosts are allowed
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

ADMINS = [("Your Name", "Your.Name@your.org")]

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3'
    }
}

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'handlers': {
#         'file': {
#             'level': 'DEBUG',
#             'class': 'logging.FileHandler',
#             'filename': '/opt/ddosdb.log',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['file'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#     },
# }

# Which email should be used for access requests
ACCESS_REQUEST_EMAIL = ""

# ReCAPTCHA keys for access requests
RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = ""

# Raw path to fingerprint and attack vector data, with trailing slash
# The standard path below is useful when running in development mode
# (Running the django development server)
RAW_PATH = "storage/"

# Hosts that Elasticsearch runs on
ELASTICSEARCH_HOSTS = ["127.0.0.1:9200"]
