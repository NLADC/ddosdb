#!/bin/sh

openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/C=EU/ST=N\/A/L=N\/A/O=Concordia/OU=DDoS Clearing House/CN=localhost" -keyout ./ddosdb-localhost.key  -out ./ddosdb-localhost.crt
