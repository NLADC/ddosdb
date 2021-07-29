from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class DdosdbConfig(AppConfig):
    name = 'ddosdb'

    # def ready(self):
    #     logger.info("DddosdbConfig.ready()")

