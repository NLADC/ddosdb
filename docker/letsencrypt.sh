#!/bin/sh

COL='\033[1;35m'
RED='\033[1;31m'
NC='\033[0m' # No Color

printf "%s\n " \
  "This will set up the local ddosdb for production use by getting a let's encrypt certificate for the domain you specify " \
  "Let's Encrypt does a check at that domain using http, so make sure " \
  "that port 80 (http) and 443 (https) are reachable from the internet " \
  "and that the domain you specify points to this machine! "

while
  printf "${COL}Fully qualified domain name for this dddosdb:${NC}"
  read fqdn
  [ -z "$fqdn" ]
do :; done

export DDOSDB_FQDN=$fqdn
echo $DDOSDB_FQDN

printf "${COL}e-mail address Let's Encrypt can send warnings too [none]:${NC}"
read le_email


# See if we can generate the certificate using certbot in the nginx container
if [ -z "$le_email" ]
then
#  printf "no mail\n"
  docker exec ddosdb_nginx \
    certbot certonly --test-cert --webroot -w /etc/letsencrypt/www/ -n --agree-tos \
    --no-eff-email --rsa-key-size 4096 -d $DDOSDB_FQDN
else
#  printf "mail $le_email \n"
  docker exec ddosdb_nginx \
    certbot certonly --test-cert --webroot -w /etc/letsencrypt/www/ -n --agree-tos \
    --email $le_email --rsa-key-size 4096 -d $DDOSDB_FQDN
fi

if [ $? -ne 0 ]
then
  printf " \n\n${RED}Some error occurred. Aborting!${NC}\n"
  exit 1
#else
#  printf " Everything went swimmingly\n"
fi

# Create new conf for nginx based on the FQDN
envsubst \$DDOSDB_FQDN <nginx/nginx-conf.template >temp/$DDOSDB_FQDN.conf

# Copy the conf file into the container
docker cp temp/$DDOSDB_FQDN.conf ddosdb_nginx:/etc/nginx/conf.d/.

if [ $? -ne 0 ]
then
  printf " \n\n${RED}Error copying NGINX configuration for $DDOSDB_FQDN to the ddosdb_nginx container. Aborting!${NC}\n"
  exit 2
#else
#  printf " Everything went swimmingly\n"
fi

# Test if configuration is OK.
# If not: remove the file from the container again
docker exec ddosdb_nginx nginx -t
if [ $? -ne 0 ]
then
  printf " \n\n${RED}Error in the NGINX configuration for $DDOSDB_FQDN.\n"
  printf " Removing and aborting!${NC}\n"
  docker exec ddosdb_nginx rm /etc/nginx/conf.d/$DDOSDB_FQDN.conf
  exit 3
#else
#  printf " Everything went swimmingly\n"
fi

# Finally send SIGHUP to NGINX to reload
# (In this case simply restart container)
docker restart ddosdb_nginx