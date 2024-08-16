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
## Running a Dockerized DDoSDB

The best [option](https://github.com/ddos-clearing-house/ddosdb/blob/master/README.md) for running a DDoSDB is the fully dockerized version. 

For this guide to work you have to have the [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

## Install docker

Install the docker engine and docker-compose, following the instructions at [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/) and [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/) respectively.

Especially on Linux ___DO NOT___ install docker and docker-compose from your distributions repository, they are too old and **will not work** for this project. 
Just follow the instructions from the [docker website](https://docs.docker.com/engine/install/#server). 

This guide assumes you can run docker as a non-root user (without using sudo), so follow the [post-install instructions](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) for this as well. 

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

This username and password are also used for the Mongo Express interface.

It will then start downloading and configuring all the images it needs for the whole DDoSDB setup, this can take some time.

At the end it should say:

```
** Finished **

Stop ddosdb by executing 'docker-compose down' in this directory
 'docker-compose up' will restart ddosdb
 'docker-compose up --build' will rebuild and restart

To reset ddosdb to factory settings: 
 Run ./clean.sh to bring down the containers and delete all data 
 Followed by './build.sh' to rebuild & restart 
```
This means DDoSDB is running daemonized (in the background).

You can check if all containers are up by executing `docker ps`, the output should look like this:

```
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS         PORTS                                                                      NAMES
8990495a1123   docker_nginx           "/sbin/tini -- /dock…"   2 minutes ago   Up 2 minutes   0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp   ddosdb_nginx
ba78353fb07e   docker_ddosdb          "/home/ddosdb/entryp…"   2 minutes ago   Up 2 minutes   8000/tcp                                                                   ddosdb_ddosdb
3b833033adeb   mongo-express          "tini -- /docker-ent…"   2 minutes ago   Up 2 minutes   127.0.0.1:8081->8081/tcp                                                   ddosdb_mongo_express
c06a03c7f6dd   mongo                  "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes   27017/tcp                                                                  ddosdb_mongo
56893e373bd8   postgres:12.0-alpine   "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes   5432/tcp                                                                   ddosdb_db

```

## Starting, stopping and updating the containers

To stop the containers execute `docker-compose down` from the docker directory.

You can start it again with `docker-compose up -d` or alternatively `docker-compose up` (without -d option)
to keep it running in the foreground (not deamonizing it). 
### Updating

The docker container is built from the local repository itself, so updating to the current version is done by stopping the containers, updating the repository and then rebuilding and restarting.

```
docker-compose down
git pull
docker-compose up --build --remove-orphans -d
```
This will keep all settings and already stored fingerprints intact. 
With major changes this may cause problems however. So if you do encounter an issue, the first thing to try 
is to delete all images and volumes and start building from scratch. This can be done by executing the `clean.sh` script. Running this script brings down all containers and then removes all images and volumes of ddosdb.

```
./clean.sh
./build.sh
```


You can enable and use Mongo Express to export the database and importing it back again after the update if needed. 

To enable Mongo Express uncomment the relevant lines in the docker-compose.yml file and restarting the containers.

Please note that Mongo Express is bound to the 127.0.0.1 (localhost) address, meaning you can only access it on the DDoSDB machine itself (for safety reasons) at http://localhost:8081. The username and password are the superuser ones you specified in the first step. 

If - for some reason - updating this way fails, then one final (nuclear) option to try is to remove all images (intermediate and otherwise) as well as all volumes from docker.

**WARNING** : *The docker prune command executed with the options below, removes **all** images and **all** volumes from your sytem! <br/> Not just the ones related with ddosdb!*

So if you have other docker projects, make sure any relevant data is **saved** before you do this!
```
# Method of last resort!

docker-compose down
docker system prune -a --volumes
./build.sh
```


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
docker logs -f ddosdb_ddosdb
```

Where `ddosdb_ddosdb` is the container name of the ddosdb itself (Use `docker ps` to list them, as mentioned above)

## Using podman instead of docker
Podman is a drop-in replacement for docker. Do make sure that the podman machine is rootful! This is needed because of the use of privileged ports (80 and 443) by ddosb. Simply replace 'docker' with 'podman' for all commands listed above. 

To build ddosdb using podman add podman as an argument to the build script:
```
./build.sh podman
```


## Acknowledgements

The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/
