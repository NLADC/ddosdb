#!/usr/bin/env sh

COL='\033[0;37m'
RED='\033[1;31m'
NC='\033[0m' # No Color

printf "${COL}%s\n ${NC}"  " " \
  "This will set up the local ddosdb for production use by getting a let's encrypt certificate for the domain you specify " \
  "Let's Encrypt does a check at that domain using http, so make sure that port 80 (http) and 443 (https) are reachable " \
  "from the internet and that the domain you specify points to this machine!" \
  " "

while
  printf "${COL}Fully qualified domain name for this dddosdb:${NC}"
  read fqdn
  [ -z "$fqdn" ]
do :; done

export DDOSDB_FQDN=$fqdn


printf "${COL}%s\n ${NC}"  " " \
  "For production use you need to specify a valid e-mail address, which Let's Encrypt can use for sending notification e-mails " \
  "about impending expirations or revocation of certificates. It is also used for account recovery. " \
  "" \
  "If you leave the e-mail address empty at the next question then automatically only test certificates will be requested. " \
  "Otherwise you can choose whether you want production or test certificates (the latter being the default). " \
  " "

printf "${COL}\n e-mail address for Let's Encrypt notifications [none]:${NC}"
read le_email

testcert="--test-cert"

if [ -n "$le_email" ]
then
  printf "${COL}\n Request production certificates? [N/y]:${NC}"
  read prodcert
  if [ "$prodcert" == 'y' ]
  then
    testcert=""
    printf "${COL}\n You chose production certificates!${NC}"
  else
    printf "${COL}\n You chose test certificates!${NC}"
  fi
fi

CERT="test"
if [ -z "$testcert" ]
then
  CERT="production"
fi

printf "${COL}\n Instructing certbot to get a new (${NC}$CERT${COL}) certificate for ${NC}$DDOSDB_FQDN\n\n"

# See if we can generate the certificate using certbot in the nginx container
if [ -z "$le_email" ]
then
#  printf "no mail\n"
  docker exec ddosdb_nginx \
    certbot certonly --test-cert --webroot -w /etc/letsencrypt/www/ -n --agree-tos \
    --no-eff-email --register-unsafely-without-email --rsa-key-size 4096 -d $DDOSDB_FQDN
else
#  printf "mail $le_email \n"
  docker exec ddosdb_nginx \
    certbot certonly $testcert --webroot -w /etc/letsencrypt/www/ -n --agree-tos \
    --email $le_email --no-eff-email --rsa-key-size 4096 -d $DDOSDB_FQDN
fi

if [ $? -ne 0 ]
then
  printf " \n\n${RED}Some error occurred. Aborting!${NC}\n"
  exit 1
#else
#  printf " Everything went swimmingly\n"
fi

printf "${COL}\n Creating nginx configuration for $DDOSDB_FQDN\n${NC}"

# Create new conf for nginx based on the FQDN
envsubst \$DDOSDB_FQDN <nginx/nginx-conf.template >temp/$DDOSDB_FQDN.conf

printf "${COL}\n Copying to nginx container and verifying \n\n${NC}"

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

printf "${COL}\n Everything OK. Restarting nginx container to let the changes take effect\n\n${NC}"

# Finally send SIGHUP to NGINX to reload
# (In this case simply restart container)
docker restart ddosdb_nginx

printf "${COL}\n All done. You should now be able to reach ddosdb at https://$DDOSDB_FQDN\n\n${NC}"
