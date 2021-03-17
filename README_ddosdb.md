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
While for a production deployment you'll need a decent (wsgi capable) webserver - such as *Apache* or *Nginx* - as a front-end, an SQL database - PostgreSQL or MySQL - for user management and logging, and of course a production capable *Elasticsearch*; the requirements for a development or test setup are a lot less demanding. 

#### Web server
For development the Django development server suffices, no need for a front-end webserver. Rather than a full-fledged SQL database the built-in support for sqlite3 will work just fine. 

#### Elasticsearch
An elasticsearch is still needed of course, but a single node dockerized version will do. A `docker-compose.yml` is provided in the `src/elasticsearch` directory. If you have docker installed then running `docker-compose up -d` in that directory should pull the right elasticsearch image and start it.
You can check if it is running by pointing a browser towards [http://localhost:9200/](http://localhost:9200/), which should show something like this:

```
{
  "name" : "et_xckp",
  "cluster_name" : "docker-cluster",
  "cluster_uuid" : "8df7oJzJQeuoL0og4f12Sw",
  "version" : {
    "number" : "6.8.11",
    "build_flavor" : "default",
    "build_type" : "docker",
    "build_hash" : "00bf386",
    "build_date" : "2020-07-09T19:08:08.940669Z",
    "build_snapshot" : false,
    "lucene_version" : "7.7.3",
    "minimum_wire_compatibility_version" : "5.6.0",
    "minimum_index_compatibility_version" : "5.0.0"
  },
  "tagline" : "You Know, for Search"
}

```
You will need to create the ddosdb index and upload the mapping. To do this simply run the `ddosdb.db` script in the housekeeping directory. 
Whenever you want to delete the ddosdb index - for example because you want to start with an empty database again - simply re-run the `ddosdb.db` script in the housekeeping directory; since it deletes any existing ddosdb index before creating a new one. 

#### Python
If you have a functioning Python3 running on your system you can use that. But if you don't, or want to avoid interference with your system version of Python, consider using something like [*pyenv*](https://github.com/pyenv/pyenv) to keep the different Python versions and environments nicely contained and separated. 

##### Python packages

When you have a functioning Python3, you can then install the required python packages:

```bash
pip install django-sslserver pandas nclib elasticsearch demjson requests django-debug-toolbar django-searchable-encrypted-fields psycopg2-binary
```
Strictly speaking you don't need the last package (psycopg2-binary) - since it is for PostgreSQL support - but you might as well install it for when you want to use PostgreSQL in a production setting.
 
In the `website` directory, copy `settings_local_example.py` to `settings_local.py` and make changes to `settings_local.py` if needed (but it probably isn't).

#### Prepare the Django project

Change to the `ddosdb` directory.

Perform the Django migrations:

```
python manage.py migrate
```

Create a superuser for your user management:


```
python manage.py createsuperuser
```

#### Running the Django development server

Run the Django development (SSL) server by issuing the following command:

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

Finally visit the start/search page of the ddosdb at [https://localhost:8000/](https://localhost:8000/)

If everything seems to be running you can upload fingerprints to the database using the [ddos_dissector](https://github.com/ddos-clearing-house/ddos_dissector), using one of the user accounts (with upload permissions) that you created.

Once you have a number of (example) fingerprints in the ddosdb, you can get an overview of all entries on the [overview page](https://localhost:8000/overview). 

## Acknowledgements

The development of the clearing house was partly funded by the European Union’s Horizon 2020 Research and Innovation program under Grant Agreement No 830927. It will be used by the Dutch National Anti-DDoS Coalition, a self-funded public-private initiative to collaboratively protect Dutch organizations and the wider Internet community from DDoS attacks. Websites: https://www.concordia-h2020.eu/ and https://www.nomoreddos.org/en/
