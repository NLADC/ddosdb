#!/usr/bin/env sh

printf "${COL}\n Are you aure you want to restore certificates and NGINX configurations? [N/y]:${NC}"
read restore

if [ x"$restore" = x"y" ]
then
  # Copy NGINX conf files
  docker cp etc/conf.d/ ddosdb_nginx:/etc/nginx/.

  # Copy Let's Encrypt settings and certificates
  docker cp etc/letsencrypt/ ddosdb_nginx:/etc/.
fi

