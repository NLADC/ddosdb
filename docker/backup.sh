#!/usr/bin/env sh

now="$(date +'%Y%m%d%H%M')"

mkdir "backup_${now}"
mkdir "backup_${now}/nginx"

# Copy NGINX conf files
docker cp ddosdb_nginx:/etc/nginx/conf.d/ "backup_${now}/nginx/".

# Copy Let's Encrypt settings and certificates
docker cp ddosdb_nginx:/etc/letsencrypt/ "backup_${now}/nginx/".

# Dump DDoS-DB postgres database with users
docker exec ddosdb_db pg_dump -h localhost -U ddosdb -F c -b -f "/tmp/postgres_backup.sql"
docker cp ddosdb_db:/tmp/postgres_backup.sql "backup_${now}"

# Dump MongoDB with fingerprints
docker exec ddosdb_mongo mongodump > /dev/null 2> /dev/null
docker cp ddosdb_mongo:/dump "backup_${now}/mongodb"
