FROM nginx:1.19.0-alpine

RUN apk add --no-cache certbot certbot-nginx tini

RUN mkdir /etc/letsencrypt
RUN mkdir /etc/letsencrypt/www

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# copy cron start script (by default cron does not start on nginx-alpine image)
COPY nginx/42-crond-start.sh /docker-entrypoint.d/.

# Periodic check for Let's Encrypt certificate renewal.
# Does nothing if no LE certificates are present
COPY nginx/certbot-renew /etc/periodic/daily/.

COPY temp/ddosdb-localhost.crt /etc/ssl/certs/.
COPY temp/ddosdb-localhost.key /etc/ssl/private/.

# tini is used because the normal start with docker-entrypoint.sh makes nginx PID 1,
# meaning signals (SIGHUP!) aren't received properly
# See https://hynek.me/articles/docker-signals/
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/docker-entrypoint.sh", "nginx-debug", "-g", "daemon off;"]
