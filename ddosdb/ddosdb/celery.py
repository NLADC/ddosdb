from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

app = Celery('ddosdb')
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')


# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(name='ddosdb.celery.debug_task', bind=True)
def debug_task(self):
    logger.info('debug_task:{}'.format(self.request))
    print('Request: {0!r}'.format(self.request))
    return 'Request: {0!r}'.format(self.request)
