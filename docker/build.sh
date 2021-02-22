#!/bin/sh

COL='\033[1;35m'
RED='\033[1;31m'
NC='\033[0m' # No Color

cp env.dev environment.prod
printf "SECRET_KEY = \'%s\'\n" $(./secret_key.py) >> environment.prod
printf "FIELD_ENCRYPTION_KEYS = \"[\'%s\']\"\n" $(./field_encryption_keys.py) >> environment.prod

while
  printf "${COL}superuser username:${NC}"
  read username
  [ -z "$username" ]
do :; done

stty -echo
while
  printf "${COL}superuser password:${NC}"
  read password
  printf "\n"
  [ -z "$password" ]
do :; done

while
  printf "${COL}superuser password (repeat):${NC}"
  read password1
  printf "\n"
  [ -z "$password1" ]
do :; done

stty echo

if [ "$password" != "$password1" ]
then
  printf "\n${RED}Passwords do not match${NC}\n\n"
  exit 1
fi

printf "\n"

printf "${COL}superuser e-mail address [ddosdb@ddosdb.local]:${NC}"
read email

if [ -z "$email" ]
then
   printf "\n${COL}No e-mail address entered, defaulting to ${NC}ddosdb@ddosdb.local\n"
   email="ddosdb@ddosdb.local"
fi

printf "DJANGO_SUPERUSER_USERNAME=%s\n" $username >> environment.prod
printf "DJANGO_SUPERUSER_PASSWORD=%s\n" $password >> environment.prod
printf "DJANGO_SUPERUSER_EMAIL=%s\n" $email >> environment.prod

printf "\n${COL} Building volumes, images, and containers${NC}\n\n"
docker-compose up --build --remove-orphans -d

# Initialize the ddosdb Django App
printf "\n${COL} Collecting Django static files${NC}\n\n"
docker-compose exec ddosdb python manage.py collectstatic --noinput

printf "\n${COL} Applying Django migrations${NC}\n\n"
docker-compose exec ddosdb python manage.py migrate --noinput

printf "\n${COL} Creating Django superuser${NC}\n\n"
docker-compose exec ddosdb python manage.py createsuperuser --noinput

# Create the ddosdb index in Elasticsearch
printf "\n${COL} Initializing Elasticsearch${NC}\n\n"
./ddosdb.db

printf "\n\n${COL}** Finished **\n\n"
printf "Stop ddosdb by executing 'docker-compose down' in this directory\n"
printf " 'docker-compose up' will restart ddosdb\n"
printf "\nTo reset ddosdb to factory settings: \n"
printf " Run 'docker-compose down -v' to delete the data \n"
printf " Followed by './build.sh' to rebuild & restart ${NC}\n\n"
