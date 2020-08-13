# Deploying DDoSDB for production

- [Prerequisites](#prerequisites)
- [Clone the repository](#clone-the-repository)
- [Elasticsearch](#elasticsearch)
    - [Create a ddosdb index](#create-a-ddosdb-index)
- [PostgreSQL](#postgresql)
- [Django and other modules](#django-and-other-modules)
- [Apache2](#apache2)
    - [Apache2 virtualhost](#apache2-virtualhost)
- [Prepare the ddosdb project](#prepare-the-ddosdb-project)
    - [Copy project to /opt/ddosdb](#copy-project-to-optddosdb)
    - [Create local settings](#create-local-settings)
    - [Do the Django migrations](#do-the-django-migrations)
- [Restart Apache](#restart-apache)



## Prerequisites

We assume (and this is tested on) a debian based setup, although probably any ubuntu based distro will do.
We further assume a user called _ddosdb_ with sudo privileges.

## Clone the repository

```bash
cd ~
git clone https://github.com/ddos-clearing-house/ddosdb
```
## Elasticsearch
```bash
sudo apt-get update
sudo apt-get install -y default-jre-headless
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install -y apt-transport-https
echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
sudo apt-get update && sudo apt-get install -y elasticsearch
sudo -i service elasticsearch start
sudo /bin/systemctl enable elasticsearch.service
```
### Create a ddosdb index
```bash
cd src
sh ddosdb.db
```
## postgreSQL
When asked for a password by one of the commands below, use `ddosdb` or change the line ` 'PASSWORD': 'ddosdb',` in `settings_local.py` later in the Create local settings step.
```bash
# PostgreSQL:
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres createdb ddosdb
sudo -u postgres createuser -P -s ddosdb
```
## Django and other modules
```bash
sudo apt-get install python3 python3-pip libpq-dev
sudo pip3 install demjson nclib django-sslserver psycopg2 psycopg2-binary elasticsearch requests pandas
```

## Apache2
```bash
sudo apt-get install -y apache2 libapache2-mod-wsgi-py3 libapache2-mod-xsendfile
sudo mkdir /opt/ddosdb-static
sudo chown -R ddosdb /opt/ddosdb-static
sudo mkdir /opt/ddosdb-data
sudo chmod 777 /opt/ddosdb-data
sudo chown -R ddosdb /opt/ddosdb-data
sudo mkdir /opt/ddosdb
sudo chown -R ddosdb /opt/ddosdb
```
### Apache2 virtualhost
```bash
sudo bash -c "cat > /etc/apache2/sites-available/000-default.conf" << EOL
<VirtualHost *:80>
Alias /static /opt/ddosdb-static/
<Directory /opt/ddosdb-static/>
    Require all granted
</Directory>

<Directory /opt/ddosdb/website>
    <Files wsgi.py>
        Require all granted
    </Files>

    XSendFile On
    XSendFilePath /opt/ddosdb-data
</Directory>

WSGIDaemonProcess website
WSGIProcessGroup website
WSGIScriptAlias / /opt/ddosdb/website/wsgi.py
</VirtualHost>
EOL
```

## Prepare the ddosdb project

### Copy project to /opt/ddosdb

```bash
cd /opt/ddosdb
cp -R /home/ddosdb/ddosdb/src/ddosdb/. .
```
### Create local settings
```bash
echo -n "SECRET_KEY = '" > /opt/ddosdb/website/settings_local.py
python -c 'import random; print("".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)]), end="")' >> /opt/ddosdb/website/settings_local.py
echo "'" >> /opt/ddosdb/website/settings_local.py
bash -c "cat >> /opt/ddosdb/website/settings_local.py" << EOL
# Which hosts are allowed to access the Web interface
# ALLOWED_HOSTS = ['ddosdb.org', 'localhost', '127.0.0.1']
# This allows all hosts to connect to the Web interface
ALLOWED_HOSTS = ['*']

# Raw path to fingerprint and attack vector data
# pcap and json are stored here
RAW_PATH = "/opt/ddosdb-data/"

# Location where HTML are stored
STATIC_ROOT = '/opt/ddosdb-static/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ddosdb',
        'USER': 'ddosdb',
        'PASSWORD': 'ddosdb',
        'HOST': 'localhost'
    }
}

ELASTICSEARCH_HOSTS = ["127.0.0.1:9200"]

EOL
```

### Do the Django migrations
```bash
python3 /opt/ddosdb/manage.py collectstatic
python3 /opt/ddosdb/manage.py migrate
python3 /opt/ddosdb/manage.py createsuperuser
```
## Restart Apache
```bash
sudo service apache2 restart
```
