<div style="text-align: center; vertical-align: center">
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/NLADC/dissector/main/media/logo-CONCORDIA.png" style="width: 30%; padding-right: 3%" alt="Concordia logo">
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/NLADC/dissector/main/media/header.png" style="width: 25%; padding-right: 3%" alt="DDoS Clearing House logo">
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<img src="https://raw.githubusercontent.com/NLADC/dissector/main/media/nomoreddos.svg#gh-light-mode-only" style="width: 30%; padding-right: 3%" alt="NoMoreDDoS logo">
<img src="https://raw.githubusercontent.com/NLADC/dissector/main/media/nomoreddos-light.png#gh-dark-mode-only" style="width: 30%; padding-right: 3%" alt="NoMoreDDoS logo">
</div>

<br/>

<div style="content-align: center;">

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
[![GitHub Issues](https://img.shields.io/github/issues/nladc/dissector)](https://github.com/nladc/dissector/issues)
![Contributions welcome](https://img.shields.io/badge/contributions-welcome-orange.svg)
[![License](https://img.shields.io/badge/license-AGPL-blue.svg)](https://opensource.org/licenses/AGPL)
![Last commit](https://img.shields.io/github/last-commit/nladc/ddosdb)
</div>
 

# DDoSDB

## Getting to know DDoSDB components

The heart of DDoSDB is a **Django** Webapp. **MongoDB** is used for storing the fingerprints, with **Mongo Express** you can inspect the fingerprints database and backup/restore it if necessary. **Nginx** is used as webserver front-end (except for the development setup).

The raw .json files and the *pcap* samples are stored locally on disk.

If you don't know what Django is, but would like to understand how DDoSDB is setup, then please checkout the excellent [documentation](https://docs.djangoproject.com/en/) and familiarise yourself a bit with Django by following the [tutorial](https://docs.djangoproject.com/en/3.1/intro/tutorial01/).

## How to start?

You can use two approaches to running a (local) DDoSDB repository:

- Run a fully [dockerized](README_docker.md) version, this is the preferred option.
- Work with Django directly in a [development setup](README_ddosdb.md).

 
For [deployment](https://github.com/ddos-clearing-house/ddosdb/blob/master/deployment.md) you can use the [dockerized](https://github.com/ddos-clearing-house/ddosdb/blob/master/README_docker.md) version and add [Let's Encrypt](https://letsencrypt.org/) cerificates using the script provided. 

## Acknowledgements

The DDoS clearing house can be used by any community of organizations that wishes to collaboratively defend themselves against DDoS attacks. The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/.


 
