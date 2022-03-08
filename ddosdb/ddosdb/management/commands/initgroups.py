from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission, Group

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean and initialize (celery (beat) powered) synchronization tasks'

    def handle(self, *args, **kwargs):
        try:
            # put startup code here
            logger.info("manage.py initgroups command: Creating default groups with useful permissions")

            def_groups = {
                # Admins can do everything
                '*admin': ['*'],

                "*manager": [
                    "add_clockedschedule",
                    "add_crontabschedule",
                    "add_ddostoken",
                    "add_fingerprint",
                    "add_intervalschedule",
                    "add_misp",
                    "add_periodictask",
                    "add_periodictasks",
                    "add_query",
                    "add_remoteddosdb",
                    "add_solarschedule",
                    "change_clockedschedule",
                    "change_crontabschedule",
                    "change_ddostoken",
                    "change_fingerprint",
                    "change_intervalschedule",
                    "change_misp",
                    "change_periodictask",
                    "change_periodictasks",
                    "change_query",
                    "change_remoteddosdb",
                    "change_solarschedule",
                    "delete_clockedschedule",
                    "delete_crontabschedule",
                    "delete_ddostoken",
                    "delete_fingerprint",
                    "delete_intervalschedule",
                    "delete_misp",
                    "delete_periodictask",
                    "delete_periodictasks",
                    "delete_query",
                    "delete_remoteddosdb",
                    "delete_solarschedule",
                    "edit_comment_fingerprint",
                    "edit_sync_fingerprint",
                    "upload_fingerprint",
                    "view_chordcounter",
                    "view_clockedschedule",
                    "view_crontabschedule",
                    "view_ddostoken",
                    "view_fingerprint",
                    "view_groupresult",
                    "view_intervalschedule",
                    "view_misp",
                    "view_nonsync_fingerprint",
                    "view_periodictask",
                    "view_periodictasks",
                    "view_query",
                    "view_remoteddosdb",
                    "view_solarschedule",
                    "view_taskresult",
                    'view_own_token',
                    'add_own_token',
                    'delete_own_token',
                ],

                # Remote viewers only see/retrieve fingerprints that have 'shareable' set to True
                # Or their own (possible if they are an uploader as well)
                '*viewer (other organisation)': [
                    'view_fingerprint',
                    'view_own_token',
                ],
                # local viewers (of the own organisation) can also see fingerprints not set to 'shareable'
                '*viewer (own organisation)': [
                    'view_fingerprint',
                    'view_nonsync_fingerprint',
                    'view_own_token',
                ],
                # Uploaders can upload/add fingerprints (obvs!) and view tokens
                '*uploader': [
                    'upload_fingerprint',
                    'add_fingerprint',
                    'view_own_token',
                ],
                # Combine above with this one to be able to add/delete tokens
                '*token creator': [
                    'view_own_token',
                    'add_own_token',
                    'delete_own_token',
                ],
                # Ability to execute queries
                '*queries': [
                    'add_query',
                    'view_query',
                    'change_query',
                    'delete_query',
                ],
                # Ability to do everything with fingerprints
                '*fingerprints': [
                    'add_fingerprint',
                    'change_fingerprint',
                    'delete_fingerprint',
                    'edit_comment_fingerprint',
                    'edit_sync_fingerprint',
                    'upload_fingerprint',
                    'view_fingerprint',
                    'view_nonsync_fingerprint',
                ],
            }

            for grp, prms in def_groups.items():
                logger.info("Group '{}' with permissions: {}".format(grp, prms))
                group, created = Group.objects.get_or_create(name=grp)
                for prm in prms:
                    if prm == '*':
                        group.permissions.set(Permission.objects.all())
                    else:
                        group.permissions.add(Permission.objects.get(codename=prm))
        except:
            raise CommandError('Initalization failed.')
