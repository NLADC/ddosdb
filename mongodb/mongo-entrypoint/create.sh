#!/usr/bin/env bash
# echo "Creating mongo users..."
# mongo admin --host localhost -u admin -p adminadmin --eval \
# " db.createUser({user: 'ddosdb', pwd: 'ddosdbddosdb', roles: [{role: 'userAdminAnyDatabase', db: 'admin'}], mechanisms:['SCRAM-SHA-1']});"
# #" use ddosdb ;" \
# mongo ddosdb --host localhost -u ddosdb -p ddosdbddosdb --eval \
# " db.createUser({user: 'ddosdb', pwd: 'ddosdbddosdb', roles: [{role: 'readWrite', db: 'ddosdb'}], mechanisms:['SCRAM-SHA-1']});"
# echo "Mongo users created."
#
# #db.createUser({user: 'ddosdb', pwd: 'ddosdbddosdb', roles: [{role: 'readWrite', db: 'ddosdb'}], mechanisms:['SCRAM-SHA-1']});
