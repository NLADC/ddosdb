# DDoSDB website

## Getting to know DDoSDB
If you want to get familiar with the DDoSDB setup and the way it works, probably it is easier to start with [DDoSDB-in-a-box](https://github.com/ddos-clearing-house/dddosdb-in-a-box): A Virtual Machine with an up and running DDoSDB instance to play with. 

For a production deployment of DDoSDB, see [deployment.md](https://github.com/ddos-clearing-house/ddosdb/blob/master/src/ddosdb/deployment.md). This is slightly outdated, but can still be used as a general guide.
## DDoSDB components

The heart of DDoSDB is a **Django** Webapp. **Elasticsearch** is used for storing the fingerprints, the raw .json files and the *pcap* samples are stored locally on disk.

If you don't know what Django is, but would like to understand how the DDoSDB website is setup, then please checkout the excellent [documentation](https://docs.djangoproject.com/en/) and familiarise yourself a bit with Django by following the [tutorial](https://docs.djangoproject.com/en/3.1/intro/tutorial01/). 

### Running a DDoSDB for development
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
You will need to create the ddosdb index and upload the mapping. To do this simply run the `ddosdb.db` script in the src directory. 
Whenever you want to delete the ddosdb index, for example because you want to start with an empty database again, use the following command:

```
curl -XDELETE "localhost:9200/ddosdb"
```
Simply re-run the `ddosdb.db` script in the src directory to create a new ddosdb index. 

#### Python
If you have a functioning Python3 running on your system you can use that. But if you don't, or want to avoid interference with your system version of Python, consider using something like [*pyenv*](https://github.com/pyenv/pyenv) to keep the different Python versions and environments nicely contained and separated. 

##### Python packages

When you have a functioning Python3, you can then install the required python packages:

```bash
pip install django-sslserver pandas nclib elasticsearch demjson requests psycopg2-binary
```
Strictly speaking you don't need the last package (psycopg2-binary) - since it is for PostgreSQL support - but you might as well install it for when you want to use PostgreSQL in a production setting.
 
In the `website` directory, copy `settings_local_example.py` to `settings_local.py` and make changes to `settings_local.py` if needed (but it probably isn't).

##### Prepare the Django project

Change to the `src/ddosdb` directory.

Perform the Django migrations:

```
python manage.py migrate
```

Create a superuser for your user management:


```
python manage.py createsuperuser
```

Run the Django development (SSL) server:

```
python manage.py runsslserver
```
If you want to run the project without ssl support (most browsers will complain about the self-signed certificate), replace runsslserver with runserver:
```
python manage.py runserver
```

Go to admin section of the website at [https://localhost:8000/admin](https://localhost:8000/admin) and log in using the credentials you created in the createsuperuser step.
Create some other users you can use for viewing, uploading etc.

Finally visit the start/search page of the ddosdb at [https://localhost:8000/](https://localhost:8000/)


If everything seems to be running you can upload fingerprints to the database using the [ddos_dissector](https://github.com/ddos-clearing-house/ddos_dissector), using one of the user accounts (with upload permissions) that you created previously.

Once you have a number of (example) fingerprints in the ddosdb, you can get an overview of all entries on the [overview page](https://localhost:8000/overview). 
