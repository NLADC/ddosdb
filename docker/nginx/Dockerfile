FROM nginx:1.19.0-alpine

RUN apk add certbot certbot-nginx

RUN mkdir /etc/letsencrypt
RUN mkdir /etc/letsencrypt/www

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
#COPY nginx.conf /etc/nginx/conf.d/ddosdb-localhost.conf

COPY temp/ddosdb-localhost.crt /etc/ssl/certs/.
COPY temp/ddosdb-localhost.key /etc/ssl/private/.
