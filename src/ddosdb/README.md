# DDoSDB website

## Components making up DDoSDB

DDoSDB runs on a combination of Apache 2.4 with wsgi, Django 2.2, Elasticsearch and PostgreSQL. 
The main entry point is the Apache server, which forwards the request to the Django server. 
Elasticsearch manages the fingerprint querying, and PostgreSQL handles the authentication and logging.
For the downloading of the fingerprints/attack vectors, X-Sendfile is used. X-Sendfile is an Apache mod 
(though also available for Nginx) for serving static files. 
This means that Django does not have to handle those files, which should save quite some CPU and memory.

## Installation
The following installation is based on a fresh copy of Ubuntu Server 18.04.

```bash
# Elasticsearch:
sudo apt-get update
sudo apt-get install -y default-jre-headless
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install -y apt-transport-https
echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
sudo apt-get update && sudo apt-get install -y elasticsearch
sudo -i service elasticsearch start
sudo /bin/systemctl enable elasticsearch.service
curl -XPUT "localhost:9200/ddosdb"
curl -XPUT -H "Content-Type: application/json" "localhost:9200/ddosdb/_mappings" --data-binary @ << EOL
{
  "ddosdb" : {
    "mappings" : {
      "_doc" : {
        "properties" : {
          "additional" : {
            "properties" : {
              "dns_query" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "dns_type" : {
                "type" : "integer"
              },
              "fragmentation" : {
                "type" : "boolean"
              },
              "icmp_type" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              },
              "tcp_flag" : {
                "type" : "text",
                "fields" : {
                  "keyword" : {
                    "type" : "keyword",
                    "ignore_above" : 256
                  }
                }
              }
            }
          },
          "dst_ports" : {
            "type" : "integer"
          },
          "duration_sec" : {
            "type" : "float"
          },
          "file_type" : {
            "type" : "keyword"
          },
          "key" : {
            "type" : "keyword"
          },
          "protocol" : {
            "type" : "keyword"
          },
          "src_ips" : {
            "properties" : {
              "as" : {
                "type" : "text"
              },
              "cc" : {
                "type" : "text"
              },
              "ip" : {
                "type" : "ip"
              }
            }
          },
          "src_ports" : {
            "type" : "integer"
          },
          "start_time" : {
            "type" : "text",
            "fields" : {
              "keyword" : {
                "type" : "keyword",
                "ignore_above" : 256
              }
            }
          },
          "start_timestamp" : {
            "type" : "float"
          }
        }
      }
    }
  }
}
EOL

# PostgreSQL:
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres createdb ddosdb
sudo -u postgres createuser -P -s ddosdb

# Django:
sudo apt-get install python3 python3-pip libpq-dev 
sudo pip3 install demjson nclib django psycopg2 psycopg2-binary elasticsearch requests

# Apache:
sudo apt-get install -y apache2 libapache2-mod-wsgi-py3 libapache2-mod-xsendfile
sudo mkdir /opt/ddosdb-static
sudo chown -R ddosdb /opt/ddosdb-static
sudo mkdir /opt/ddosdb-data
sudo chmod 777 /opt/ddosdb-data
sudo chown -R ddosdb /opt/ddosdb-data
sudo mkdir /opt/ddosdb
sudo chown -R ddosdb /opt/ddosdb-static

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

git clone https://github.com/Koenvh1/ddosdb-website.git /opt/ddosdb

# In /opt/ddosdb/website/settings_local.example.py
# Change ALLOWED_HOSTS, DATABASES, ACCESS_REQUEST_EMAIL, RAW_PATH, DEBUG
# And rename the file to settings_local.py

python3 /opt/ddosdb/manage.py collectstatic
python3 /opt/ddosdb/manage.py migrate
python3 /opt/ddosdb/manage.py createsuperuser

sudo service apache2 restart
```
