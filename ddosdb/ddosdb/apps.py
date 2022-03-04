from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig
import logging

logger = logging.getLogger(__name__)


class DdosdbConfig(AppConfig):
    name = 'ddosdb'

    # def ready(self):
    #     logger.info("DddosdbConfig.ready()")


class DdosdbAdminConfig(AdminConfig):
    default_site = 'ddosdb.adminsite.MyAdminSite'

    # def ready(self):
    #     logger.info("DddosdbConfig.ready()")
