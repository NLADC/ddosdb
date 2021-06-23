#!/bin/sh

echo "Waiting for postgres... ($SQL_HOST:$SQL_PORT)"

while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 1
done

echo "PostgreSQL started"

exec "$@"