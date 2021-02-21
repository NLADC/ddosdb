#!/bin/sh

docker-compose up --build --remove-orphans -d

docker-compose exec ddosdb python manage.py collectstatic --noinput
docker-compose exec ddosdb python manage.py migrate --noinput
docker-compose exec ddosdb python manage.py createsuperuser --noinput
./ddosdb.db