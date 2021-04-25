#!/usr/bin/env sh

COL='\033[0;37m'
RED='\033[1;31m'
NC='\033[0m' # No Color

printf "${COL}\n Are you sure you want to restore certificates and NGINX configurations? [y/N]:${NC}"
read restore

if [ x"$restore" = x"y" ]
then
  # Copy NGINX conf files
  docker cp etc/conf.d/ ddosdb_nginx:/etc/nginx/.

  # Copy Let's Encrypt settings and certificates
  docker cp etc/letsencrypt/ ddosdb_nginx:/etc/.
fi

