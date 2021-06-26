import os
from django.apps import AppConfig
import logging
import celery

logger = logging.getLogger(__name__)


class DdosdbConfig(AppConfig):
    name = 'ddosdb'

    def ready(self):
        logger.info("DddosdbConfig.ready()")
        # print("DddosdbConfig.ready()")

        # importing model classes
        from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
        #        import django_celery_beat.models as cb
        intervals = IntervalSchedule.objects.all()
        i = 0
        for iv in intervals:
            i += 1
            logger.info("Interval {}: {}".format(i, iv))

        periodic_tasks = PeriodicTask.objects.all()
        i = 0
        for pt in periodic_tasks:
            i += 1
            logger.info("Periodic Task {}: {}".format(i, pt))

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=30, period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.get_or_create(
            interval=schedule,
            name='Debug task',  # Description
            task='ddosdb.celery.debug_task',  # name of task.
        )

        # Delete all backup cleaning tasks and create a new one
        logger.info("Deleting all celery.backend_cleanup tasks")
        PeriodicTask.objects.filter(task='celery.backend_cleanup').delete()

        schedule, created = IntervalSchedule.objects.get_or_create(
            every=5, period=IntervalSchedule.MINUTES)

        pt = PeriodicTask.objects.get_or_create(
            interval=schedule,
            name='Cleanup task',  # Description must be unique
            task='celery.backend_cleanup',  # name of task.
        )
        logger.info("Created celery.backend_cleanup task : {}".format(pt))


