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

This guide assumes you have the [Docker Engine](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

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

Install docker engine:

See instructions: https://docs.docker.com/engine/install/ubuntu/

Start the build script

```
./build.sh
```
The script will ask you for the username, password and e-mail address to use for the superuser. The username and password are also used for the Mongo Express interface.

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


You can use Mongo Express to export the database and importing it back again after the update if needed. Please note that Mongo Express is bound to the 127.0.0.1 (localhost) address, meaning you can only access it on the DDoSDB machine itself (for safety reasons) at http://localhost:8081. The username and password are the superuser ones you specified in the first step. 
<p align="center"></p><img width=50% src="https://github.com/ddos-clearing-house/dddosdb-in-a-box/blob/master/imgs/mongo-express.png?raw=true"></p>

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

## Acknowledgements

The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/
