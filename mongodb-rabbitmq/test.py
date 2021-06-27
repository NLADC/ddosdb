#!/usr/bin/env python3

from pymongo import MongoClient
# pprint library is used to make the output look more pretty
from pprint import pprint


# connect to MongoDB, change the << MONGODB URL >> to reflect your own connection string
client = MongoClient('mongodb://127.0.0.1:27017')
db=client['ddosdb']

pprint(db.list_collection_names())
# Issue the serverStatus command and print the results
#serverStatusResult=db.command("serverStatus")
#pprint(serverStatusResult)
