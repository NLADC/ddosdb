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

## Running a DDoSDB for development
While for a production deployment you'll need a decent (wsgi capable) webserver - such as *Apache* or *Nginx* - as a front-end, an SQL database - PostgreSQL - for user management and logging, and of course a production capable *MongoDB* and *RabbitMQ*; the requirements for a development or test setup are a lot less demanding. 

#### Python
If you have a functioning Python3 running on your system you can use that. But in order to avoid interference with your system version of Python, create a virtual environment.
```
python3 -m venv .venv
source .venv/bin/activate
```

##### Python packages

When you have a functioning Python3, you can then install the required python packages:

```bash
pip install -r requirements.txt
```
 
In the `website` directory, copy `settings_local_example.py` to `settings_local.py` and make changes to `settings_local.py` if needed (but it probably isn't).

#### MongoDB and RabbitMQ
DDoSDB needs instances of MongoDB and RabbitMQ to function, but a single node dockerized version will do for both. A `docker-compose.yml` is provided in the `mongodb-rabbitmq` directory. If you have docker installed then running `docker-compose up -d` in that directory will pull the right Mongo, Mongo Express and RabbitMQ images and start them.
You can check if it is running by pointing a browser towards [http://localhost:8081/](http://localhost:8081/), which should popup a dialog box asking for a username and password. Entering user `ddosdb` and password `ddosdbddosdb` will show the Mongo Express interface:

<p align="center"></p><img width=50% src="https://github.com/ddos-clearing-house/dddosdb-in-a-box/blob/master/imgs/mongo-express.png?raw=true"></p>

The ddosdb database is created at startup of the Django development server.
Whenever you want to delete the ddosdb database - for example because you want to start with an empty database again - simply delete the database using Mongo Express and restart Django.

#### Prepare the Django project

Once you have MongoDB and RabbitMQ up and running, change to the `ddosdb` directory.

Perform the Django migrations:

```
python manage.py migrate
```

Create a superuser for your user management:


```
python manage.py createsuperuser
```

#### Optional preparations

*Group permissions*

Permissions can be managed in Django by assigning permissions to users directly. 
A better way to do this is to assign permissions to groups, rather than users. 
Users can then be added to those groups and inherit the permissions of the groups they are assigned to.
A reasonable collection of default groups can be created by the following command.

```
python manage.py initgroups
```

*Periodic tasks*

For synchonization between DDoSDB instances periodic tasks are used. See also the section below on Celery worker and Celery beat.
In case you need this in a development setup, use the following command to create a default synchronization schedule of once a day.

```
python manage.py initsync
```
Next to 'every day', this also creates intervals for 'every hour', 'every minute' and 'every 15 seconds'.
The admin interface of Django can be used to adjust the periodic tasks to one of these alternative intervals.

#### Web server
For development the Django development server suffices, no need for a front-end webserver. Rather than a full-fledged SQL database the built-in support for sqlite3 will work just fine. 

#### Celery worker and Celery beat
DDoSDB uses Celery to carry out periodic tasks, hence the need for RabbitMQ (used as the message broker for Celery).
You can run DDoSDB without Celery worker and beat just fine if you don't need synchronization of fingerprints between different DDoSDB instances (very likely for development). But if you do then you need to start Celery beat and worker. Open a new terminal window and activate the Python virtual environment as described above. Then move to the directory containing the `manage.py` file (`cd ddosdb` from the base directory). 

Start Celery beat and worker with the following command:
``` 
celery -A ddosdb worker -B -l info
```

#### Running the Django development server

Run the Django development (SSL) server by issuing the following command in the same directory:

```
python manage.py runsslserver --settings=website.settings-dev
```
If you want to run the project without ssl support (most browsers will complain about the self-signed certificate), replace runsslserver with runserver:
```
python manage.py runserver --settings=website.settings-dev
```
In both cases the `--settings=website.settings-dev` argument ensures that the development settings are used from the `website/settings-dev.py` file rather than the standard `website/settings.py`, which contains the settings for deployment.

#### Creating additional users

Go to admin section of the website at [https://localhost:8000/admin](https://localhost:8000/admin) and log in using the credentials you created in the createsuperuser step. Create some other users you can use for viewing, uploading etc.
The admin section can also be reached by clicking the cog wheel icon at the right of the banner at the top of every page.

Finally, visit the start/search page of the ddosdb at [https://localhost:8000/](https://localhost:8000/)

If everything seems to be running you can upload fingerprints to the database using the [ddos_dissector](https://github.com/ddos-clearing-house/ddos_dissector), using one of the user accounts (with upload permissions) that you created.

Once you have a number of (example) fingerprints in the ddosdb, you can get an overview of all entries on the [overview page](https://localhost:8000/overview). 

## Acknowledgements

The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/
