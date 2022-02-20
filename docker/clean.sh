#!/usr/bin/env sh

COL='\033[0;37m'
RED='\033[1;31m'
NC='\033[0m' # No Color


printf "${RED}%s\n ${NC}"  " " \
  "**** This will delete ALL data! ****" \
  "" \
  "This includes already stored fingerprints, certificates, as well as all configured user names and passwords." \

printf "${RED}\n Are you ** REALLY REALLY ** sure you want to do this? [y/N]:${NC}"

read doclean

printf "\n\n"

if [ x"$doclean" = x"y" ]
then
  docker-compose down -v
  docker-compose stop
  docker image rm docker_nginx ddosdb/ddosdb
fi

printf "\n"
