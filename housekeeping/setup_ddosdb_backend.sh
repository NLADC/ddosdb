# Installation process

# basic setup
#su -
#apt-get update
#apt-get install -y sudo git
#adduser ddosdb
#echo "ddosdb     ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
#su - ddosdb

# download repo
#mkdir .ddosdb
#cd .ddosdb
#git clone https://github.com/ddos-clearing-house/ddosdb

# Elasticsearch:
sudo apt-get install -y gnupg default-jre-headless
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install -y apt-transport-https
echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
sudo apt-get update && sudo apt-get install -y elasticsearch curl
sudo -i service elasticsearch start
sudo /bin/systemctl enable elasticsearch.service
printf "Waiting for Elasticsearch to come online..."
until $(curl --output /dev/null --silent --head --fail http://localhost:9200); do
    printf '.'
    sleep 5
done
# config database
sh ddosdb.db

# PostgreSQL:
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres createdb ddosdb
sudo -u postgres createuser -s ddosdb
sudo -u postgres psql -c "alter user ddosdb with encrypted password 'ddosdb';"

# Django:
sudo apt-get install -y python3 python3-pip libpq-dev
sudo pip3 install demjson nclib django psycopg2 psycopg2-binary elasticsearch requests pandas semver

# Apache:
sudo apt-get install -y apache2 libapache2-mod-wsgi-py3 libapache2-mod-xsendfile
sudo mkdir /opt/ddosdb-static
sudo chown -R ddosdb /opt/ddosdb-static
sudo mkdir /opt/ddosdb-data
sudo chmod 755 /opt/ddosdb-data
sudo chown -R ddosdb /opt/ddosdb-data
sudo mkdir /opt/ddosdb
sudo chown -R ddosdb /opt/ddosdb

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

#sudo git clone https://github.com/Koenvh1/ddosdb-website.git /opt/ddosdb
#sudo apt-get install -y unzip
#sudo chown -R ddosdb /opt/ddosdb
#cd /opt/ddosdb
cp -R ~/.ddosdb/ddosdb/ddosdb/. /opt/ddosdb/.

# Edit /opt/ddosdb/website/settings.py
sudo cp /opt/ddosdb/website/settings_local.example.py /opt/ddosdb/website/settings_local.py
sudo printf "\nSTATIC_ROOT = \"/opt/ddosdb-static/\"\n\n" >> /opt/ddosdb/website/settings_local.py
sudo tee -a /opt/ddosdb/website/settings_local.py << EOL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ddosdb',
        'USER': 'ddosdb',
        'PASSWORD': 'ddosdb',
        'HOST': 'localhost'
    }
}
EOL

#sudo nano /opt/ddosdb/website/settings_local.py

sudo python3 /opt/ddosdb/manage.py collectstatic
sudo python3 /opt/ddosdb/manage.py migrate
echo "Setting up the initial user for DDoSDB..."
sudo python3 /opt/ddosdb/manage.py createsuperuser

sudo touch /opt/ddosdb.log
sudo chmod 777 /opt/ddosdb.log

sudo chown ddosdb /opt/ddosdb.log

#sudo service apache2 restart
sudo systemctl restart apache2.service
echo "DDoSDB setup done."
