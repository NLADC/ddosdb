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
## Running a Dockerized DDoSDB

One of the [options for running a DDoSDB](https://github.com/ddos-clearing-house/ddosdb/blob/master/README.md) is the fully dockerized version. 

This guide assumes you have [Docker](https://www.docker.com/get-started) installed.

## Cloning the repository

Change to the directory where you want to run it from (in this example your home directory) and clone the ddosdb repository there.
```bash
cd ~
git clone https://github.com/ddos-clearing-house/ddosdb
```

## Building the containers

Change into the docker directory of the ddosdb repository.
```
cd ddosdb/docker
```

Start the build script

```
./build.sh
```
The script will ask you for the username, password and e-mail address to use for the superuser.

It will then start downloading and configuring all the images it needs for the whole DDoSDB setup, this can take some time.

At the end it should say:

```
** Finished **

Stop ddosdb by executing 'docker-compose down' in this directory
 'docker-compose up' will restart ddosdb

To reset ddosdb to factory settings: 
 Run 'docker-compose down -v' to delete the data 
 Followed by './build.sh' to rebuild & restart 
```
This means DDoSDB is running daemonized.

You can check if all containers are up by executing `docker ps`, the output should be something like this:

```
CONTAINER ID   IMAGE                                                 COMMAND                  CREATED         STATUS         PORTS                                NAMES
a0de6eafa390   docker_nginx                                          "/docker-entrypoint.…"   6 seconds ago   Up 6 seconds   0.0.0.0:80->80/tcp                   docker_nginx_1
e13aacec74c4   docker_ddosdb                                         "/home/ddosdb/entryp…"   7 seconds ago   Up 6 seconds   8000/tcp                             docker_ddosdb_1
dda6e48f43d5   docker.elastic.co/elasticsearch/elasticsearch:7.8.0   "/tini -- /usr/local…"   7 seconds ago   Up 7 seconds   127.0.0.1:9200->9200/tcp, 9300/tcp   docker_elasticsearch_1
d005eec417c8   postgres:12.0-alpine                                  "docker-entrypoint.s…"   7 seconds ago   Up 7 seconds   5432/tcp                             docker_db_1
```

## Starting, stopping and updating the containers

To stop the containers execute `docker-compose down` from the docker directory.

You can start it again with `docker-compose up -d` or alternatively `docker-compose up` (without -d option)
to keep it running in the foreground (not deamonizing it). 
### Updating

The docker container is built from the local repository itself, so updating to the current version is done by stopping the containers and removing the data, updating the repository and then rebuilding and re-initialising.

```
docker-compose down -v
git pull
./build.sh
```

For minor updates it *may* be enough to update and rebuild (without removing data and re-initialising everything).
In order to do that, simply bring the container down, update the repository and bring the containers back up with an explicit build option:

```
docker-compose down
git pull
docker-compose up --build --remove-orphans -d
```
However, this may result in unpredictable behaviour or crashes when the updates are major.
So using the first approach is recommended. 

## View logging from the container

In some cases it may be desirable to see logging from the various services from within the container.

The most straightforward method is starting the container without daemonizing it:

```
docker-compose up
```
This will show all logging. The containers can be stopped by pressing CTRL+C.

If you want to show all logging from an already running container then you can use this command from the docker directory:
```
docker-compose logs -f
```

If you only want to see the logging from a specific service you can use:

```
docker logs -f docker_ddosdb_1
```

Where `docker_ddosdb_1` is the container name of the ddosdb itself (Use `docker ps` to list them, as mentioned above)

## Acknowledgements

The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/
