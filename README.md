<p align="center"><img width=30.5% src="https://github.com/ddos-clearing-house/ddos_dissector/blob/3.0/media/header.png?raw=true"></p>


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
![Python](https://img.shields.io/badge/python-v3.6+-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/ddos-clearing-house/ddosdb)](https://github.com/ddos-clearing-house/ddosdb/issues)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
<img alt="GitHub commits since tagged version" src="https://img.shields.io/github/last-commit/ddos-clearing-house/ddos_dissector">

 <p align="center"><img width=30.5% src="https://github.com/ddos-clearing-house/dddosdb-in-a-box/blob/master/imgs/concordia-logo.png?raw=true"></p>
 <p align="center"><img width=30.5% src="https://github.com/ddos-clearing-house/dddosdb-in-a-box/blob/master/imgs/No-More-DDoS-2-removebg-preview.png?raw=true"></p>


# DDoSDB

## Getting to know DDoSDB components

The heart of DDoSDB is a **Django** Webapp. **MongoDB** is used for storing the fingerprints, with **Mongo Express** you can inspect the fingerprints database and backup/restore it if necessary. **Nginx** is used as webserver front-end (except for the development setup).

The raw .json files and the *pcap* samples are stored locally on disk.

If you don't know what Django is, but would like to understand how DDoSDB is setup, then please checkout the excellent [documentation](https://docs.djangoproject.com/en/) and familiarise yourself a bit with Django by following the [tutorial](https://docs.djangoproject.com/en/3.1/intro/tutorial01/).

## How to start?

You can use two approaches to running a (local) DDoSDB repository:

- Run a fully [dockerized](https://github.com/ddos-clearing-house/ddosdb/blob/master/README_docker.md) version, this is the preferred option.
- Work with Django directly in a [development setup](https://github.com/ddos-clearing-house/ddosdb/blob/master/README_ddosdb.md).

 
For [deployment](https://github.com/ddos-clearing-house/ddosdb/blob/master/deployment.md) you can use the [dockerized](https://github.com/ddos-clearing-house/ddosdb/blob/master/README_docker.md) version and add [Let's Encrypt](https://letsencrypt.org/) cerificates using the script provided. 

## Acknowledgements

The DDoS clearing house can be used by any community of organizations that wishes to collaboratively defend themselves against DDoS attacks. The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/.


 
