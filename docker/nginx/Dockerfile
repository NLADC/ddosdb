FROM nginx:1.19.0-alpine

RUN apk add certbot certbot-nginx

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY ddosdb-localhost.crt /etc/ssl/certs/.
COPY ddosdb-localhost.key /etc/ssl/private/.
