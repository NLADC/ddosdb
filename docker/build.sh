#!/usr/bin/env sh

COL='\033[0;37m'
RED='\033[1;31m'
NC='\033[0m' # No Color

cp django/env.dev temp/environment.prod
printf "SECRET_KEY=\'%s\'\n" $(./lib/secret_key.py) >> temp/environment.prod

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

printf "DJANGO_SUPERUSER_USERNAME=%s\n" $username >> temp/environment.prod
printf "DJANGO_SUPERUSER_PASSWORD=%s\n" $password >> temp/environment.prod
printf "DJANGO_SUPERUSER_EMAIL=%s\n" $email >> temp/environment.prod

printf "ME_CONFIG_BASICAUTH_USERNAME=%s\n" $username >> temp/environment.prod
printf "ME_CONFIG_BASICAUTH_PASSWORD=%s\n" $password >> temp/environment.prod

# Generate self-signed certificate for localhost
printf "\nGenerating self-signed certificate for localhost\n"
openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 -subj "/C=EU/ST=N\/A/L=N\/A/O=Concordia/OU=DDoS Clearing House/CN=localhost" -keyout ./temp/ddosdb-localhost.key  -out ./temp/ddosdb-localhost.crt

printf "\n${COL} Building volumes, images, and containers${NC}\n\n"
docker compose build
docker compose up -d

# Initialize the ddosdb Django App
#printf "\n${COL} Collecting Django static files${NC}\n\n"
#docker compose exec ddosdb python manage.py collectstatic --noinput
#
#printf "\n${COL} Applying Django migrations${NC}\n\n"
#docker compose exec ddosdb python manage.py migrate --noinput

#printf "\n${COL} Creating Django superuser${NC}\n\n"
#docker compose exec ddosdb python manage.py createsuperuser --noinput

#printf "\n${COL} Setting up default Celery (beat) tasks ${NC}\n\n"
#docker compose exec ddosdb python manage.py celery

printf "\n\n${COL}** Finished **\n\n"
printf "Stop ddosdb by executing 'docker compose down' in this directory\n"
printf " 'docker compose up' will restart ddosdb\n"
printf " 'docker compose up --build' will rebuild and restart\n"
printf "\nTo reset ddosdb to factory settings: \n"
printf " Run ./clean.sh to bring down the containers and delete all data \n"
printf " Followed by './build.sh' to rebuild & restart ${NC}\n\n"
