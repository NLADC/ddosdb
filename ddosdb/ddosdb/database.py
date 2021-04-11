from django.conf import settings
import pymongo

class Database(object):
   URI =  "mongodb://"+settings.MONGODB
   DATABASE = None

   @staticmethod
   def initialize():
       client = pymongo.MongoClient(Database.URI)
       Database.DATABASE = client.ddosdb.fingerprints

   @staticmethod
   def getDB():
        return Database.DATABASE
