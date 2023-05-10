import json

from django.core.management.base import BaseCommand, CommandError
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean and initialize (celery (beat) powered) synchronization tasks'

    def handle(self, *args, **kwargs):
        try:
            # put startup code here
            logger.info("manage.py initsync command")
            # importing model classes
            from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

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

            logger.info("Creating the default ddosdb push/pull sync and cleanup tasks")
            IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
            IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.SECONDS)
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1, period=IntervalSchedule.HOURS)
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1, period=IntervalSchedule.DAYS)

            # Create Pull sync(s) if needed
            p_task, created = PeriodicTask.objects.get_or_create(
                name='Remote pull sync',  # Description
                task='ddosdb.tasks.pull_sync',  # name of task.
                defaults={'interval': schedule}
            )
            if created:
                logger.info("Pull sync task created")
            else:
                logger.info("Pull sync task already exists")
            logger.info("with scheduled interval of: {}".format(p_task.interval))

            # Create Push sync if needed
            p_task, created = PeriodicTask.objects.get_or_create(
                name='Remote push sync',  # Description
                task='ddosdb.tasks.push_sync',  # name of task.
                defaults={'interval': schedule}
            )
            if created:
                logger.info("Push sync task created")
            else:
                logger.info("Push sync task already exists")
            logger.info("with scheduled interval of: {}".format(p_task.interval))

            # Create MISP pull sync(s) if needed
            p_task, created = PeriodicTask.objects.get_or_create(
                name='MISP pull sync',  # Description
                task='ddosdb.tasks.misp_pull_sync',  # name of task.
                defaults={'interval': schedule}
            )
            if created:
                logger.info("MISP pull sync task created")
            else:
                logger.info("MISP pull sync task already exists")
            logger.info("with scheduled interval of: {}".format(p_task.interval))

            # Create MISP push sync if needed
            p_task, created = PeriodicTask.objects.get_or_create(
                name='MISP push sync',  # Description
                task='ddosdb.tasks.misp_push_sync',  # name of task.
                defaults={'interval': schedule}
            )
            if created:
                logger.info("MISP push sync task created")
            else:
                logger.info("MISP push sync task already exists")
            logger.info("with scheduled interval of: {}".format(p_task.interval))

            # Create clearing up schedule (check once a day for fingerprints
            # older than X days (730 days default)
            p_task, created = PeriodicTask.objects.get_or_create(
                name='Old fingerprint cleanup',  # Description
                task='ddosdb.tasks.fingerprint_cleanup',  # name of task.
                defaults={'interval': schedule},
                kwargs=json.dumps({"days": 730})
            )
            if created:
                logger.info("Task for old fingerprint cleanup created")
            else:
                logger.info("Task for old fingerprint cleanup already exists")
            logger.info("with scheduled interval of: {}".format(p_task.interval))

            # PeriodicTask.objects.get_or_create(
            #     interval=schedule,
            #     name='Remote push sync',  # Description
            #     task='ddosdb.tasks.push_sync',  # name of task.
            # )

            # Delete all backup cleaning tasks and create a new one
            # logger.info("Deleting all celery.backend_cleanup tasks")
            # PeriodicTask.objects.filter(task='celery.backend_cleanup').delete()

            # schedule, created = IntervalSchedule.objects.get_or_create(
            #     every=5, period=IntervalSchedule.MINUTES)
            #
            # pt = PeriodicTask.objects.get_or_create(
            #     interval=schedule,
            #     name='Cleanup task',  # Description must be unique
            #     task='celery.backend_cleanup',  # name of task.
            # )

            # logger.info("Created celery.backend_cleanup task : {}".format(pt))
        except:
            raise CommandError('Initalization failed.')
