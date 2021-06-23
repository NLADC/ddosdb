#!/bin/sh

if [-v POSTGRES_DB ]
then
  echo "Waiting for postgres... ($SQL_HOST:$SQL_PORT)"
  while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 1
  done
  echo "PostgreSQL started"
fi
exec "$@"