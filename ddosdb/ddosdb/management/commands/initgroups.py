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
                # Remote viewers only see/retrieve fingerprints with 'shareable' set to True
                # Or their own (possible if they are an uploader as well)
                '*viewer (other organisation)': ['view_fingerprint',
                                      'view_multitoken',
                                      ],
                # local viewers (of the own organisation) can also see fingerprints not set to 'shareable'
                '*viewer (own organisation)': ['view_fingerprint',
                                     'view_nonsync_fingerprint',
                                     ],
                # Uploaders can upload/add fingerprints (obvs!)
                '*uploader': ['upload_fingerprint',
                               'add_fingerprint',
                               'view_multitoken',
                               ],
                # Combine above with this one to be able to add/delete tokens
                '*token creator': ['upload_fingerprint',
                                    'view_multitoken',
                                    'add_multitoken',
                                    'delete_multitoken',
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
