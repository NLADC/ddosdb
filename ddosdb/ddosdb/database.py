from django.conf import settings
import pymongo
import pprint
import logging

logger = logging.getLogger(__name__)


class Database(object):
    URI = "mongodb://" + settings.MONGODB
    DATABASE = None

    @staticmethod
    def initialize():
        pp = pprint.PrettyPrinter(indent=4)

        client = pymongo.MongoClient(Database.URI)
        db = client.ddosdb.fingerprints
        #
        # Database.DATABASE.drop_indexes()
        # # Create text index
        db.create_index([
            ('key', 'text'),
            ('tags', 'text'),
            ('one_line_fingerprint', 'text'),
            ('ip_proto', 'text'),
            ('highest_protocol', 'text'),
            ('dns_qry_name', 'text'),
            ('src_ips', 'text'),
            ('submitter', 'text'),
        ], name='text_index')
        logger.info("Database index created")
        logger.debug(db.index_information())

    @staticmethod
    def getDB():
        if not Database.DATABASE:
            client = pymongo.MongoClient(Database.URI)
            Database.DATABASE = client.ddosdb.fingerprints

        return Database.DATABASE
