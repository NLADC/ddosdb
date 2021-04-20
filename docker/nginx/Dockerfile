FROM nginx:1.19.0-alpine

RUN apk add certbot certbot-nginx

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY ddosdb-localhost.crt /etc/ssl/certs/.
COPY ddosdb-localhost.key /etc/ssl/private/.

# openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 -subj "/C=EU/ST=N\/A/L=N\/A/O=Concordia/OU=DDoS Clearing House/CN=localhost" -keyout ./nginx-selfsigned.key  -out ./nginx-selfsigned.crt
