#!/bin/sh

cp env.dev environment.prod
printf "SECRET_KEY = \'%s\'\n" $(./secret_key.py) >> environment.prod
printf "FIELD_ENCRYPTION_KEYS = \"[\'%s\']\"\n" $(./field_encryption_keys.py) >> environment.prod

printf "superuser username:"
read username

stty -echo
printf "superuser password:"
read password
stty echo
printf "\n"

printf "superuser e-mail address:"
read email

if [[ -z "$email" ]]; then
   printf '%s\n' "No e-mail address entered, defaulting to ddosdb@ddosdb.local"
   email="ddosdb@ddosdb.local"
fi

printf "DJANGO_SUPERUSER_USERNAME=%s\n" $username >> environment.prod
printf "DJANGO_SUPERUSER_PASSWORD=%s\n" $password >> environment.prod
printf "DJANGO_SUPERUSER_EMAIL=%s\n" $email >> environment.prod

docker-compose up --build --remove-orphans -d

# Initialize the ddosdb Django App
docker-compose exec ddosdb python manage.py collectstatic --noinput
docker-compose exec ddosdb python manage.py migrate --noinput
docker-compose exec ddosdb python manage.py createsuperuser --noinput

# Create the ddosdb index in Elasticsearch
./ddosdb.db
