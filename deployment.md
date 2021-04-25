
<p align="center"><img width=30.5% src="https://github.com/ddos-clearing-house/ddos_dissector/blob/3.0/media/header.png?raw=true"></p>




&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![Python](https://img.shields.io/badge/python-v3.6+-blue.svg)
[![Build Status](https://api.travis-ci.com/joaoceron/new_dissector.svg?token=8TMUECLCUVrxas7wXfVY&branch=master)](https://travis-ci.com/github/joaoceron/new_dissector)
[![GitHub Issues](https://img.shields.io/github/issues/ddos-clearing-house/ddos_dissector)](https://github.com/ddos-clearing-house/ddos_dissector/issues)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
<img alt="GitHub commits since tagged version" src="https://img.shields.io/github/last-commit/ddos-clearing-house/ddos_dissector">

 <p align="center"><img width=30.5% src="https://github.com/ddos-clearing-house/dddosdb-in-a-box/blob/master/imgs/concordia-logo.png?raw=true"></p>
 <p align="center"><img width=30.5% src="https://github.com/ddos-clearing-house/dddosdb-in-a-box/blob/master/imgs/No-More-DDoS-2-removebg-preview.png?raw=true"></p>

# DDoSDB

## Production deployment with Let's Encrypt certificates

### Prerequisites
Deployment of DDoSDB is simply the dockerized version with [Let's Encrypt](https://letsencrypt.org/) certificates on top.
So for deployment first follow the steps as outlined by the 
[dockerized](https://github.com/ddos-clearing-house/ddosdb/blob/master/README_docker.md)
instructions.

For requesting and renewing certificates ddosdb uses [certbot](https://certbot.eff.org/) with the [HTTP-01](https://letsencrypt.org/docs/challenge-types/) challenge.
This means that your ddosdb installation has to have:
1. Ports 80 (http) and 443 (https) reachable from the internet
2. A DNS record that points to that machine (no point in requesting a certificate otherwise).

Both are needed *before* you can get a Let's Encrypt certificate.


Requesting and installing a certificate is done with the `./letsencrypt.sh` script, in the same directory (docker) as the build script.

### Testing the waters
The letsencrypt script will ask you the domain name for which it has to request a certificate. This domain should (of course) resolve to the machine running DDoSDB.

It will then ask you for your e-mail address. This is used by Let's Encrypt to send expiration e-mails. If you don't specify an e-mail address (just press return) the script will assume you want to get a test certificate. If you did specify an e-mail address then the script will ask you if you want to request a production certificate. The default is No (meaning it will request a test certificate).

You can do this the first time you run the script, just to check that everything is working.
The output should look like this (but then with coloured text):
```
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Plugins selected: Authenticator webroot, Installer None
Obtaining a new certificate
Performing the following challenges:
http-01 challenge for ddosdb.mooo.com
Using the webroot path /etc/letsencrypt/www for all unmatched domains.
Waiting for verification...
Cleaning up challenges
IMPORTANT NOTES:
 - Congratulations! Your certificate and chain have been saved at:
   /etc/letsencrypt/live/ddosdb.mooo.com/fullchain.pem
   Your key file has been saved at:
   /etc/letsencrypt/live/ddosdb.mooo.com/privkey.pem
   Your cert will expire on 2021-07-24. To obtain a new or tweaked
   version of this certificate in the future, simply run certbot
   again. To non-interactively renew *all* of your certificates, run
   "certbot renew"

 Creating nginx configuration for ddosdb.mooo.com

 Copying to nginx container and verifying 

nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

 Everything OK. Instructing nginx to reload it's configuration to let the changes take effect

2021/04/25 18:36:07 [notice] 148#148: signal process started

 All done. You should now be able to reach ddosdb at https://ddosdb.mooo.com
 
 Because this certificate is a test certificate, your browser will tell you this site is not trusted and not secure.
 You will probably have to tell it somehow to go to this site anyway and ignore this warning. 
 How to do that depends on your browser and is beyond the scope of this guide.
  
 For uploads by ddos_dissector you can add an -n option to ignore certificate verification. 

```

This shows that everything is working as it should. So go ahead:

### Taking the plunge

Simply re-run the `./letsencrypt.sh` script, but this time do provide an e-mail address and answer 'y' when asked if you want a production certificate. That's all!

Please note you can request certificates for more than one domain, as long as all those domains point to this machine.

### Certificate renewal
Once a day the system checks if the certiicate(s) need to be renewed. This happens automatically when the expiration date is fewer than 30 days away.

### Updating DDoSDB (with certificates installed)
If you need to update the system then you can simply re-run the `./letsencrypt.sh` script afterwards to get a new certificate. Just make sure you don't exceed the [rate limit](https://letsencrypt.org/docs/rate-limits/) for requesting production certificates! (This is very unlikely to happen for test certificates, since those rate limits are much much higher). 

If you want to keep the same certificates (for example because you are close to the rate limit), then simply run the `backup.sh` script before running the update and the `restore.sh` script afterwards. The former will simply copy all Let's Encrypt data and nginx configurations from docker to local disk, the latter will copy it back again. 

## Acknowledgements

The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/
