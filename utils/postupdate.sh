sudo pip3 install django-searchable-encrypted-fields
cp -R /home/ddosdb/.ddosdb/ddosdb/ddosdb/. /opt/ddosdb/.
python3 /opt/ddosdb/manage.py collectstatic --noinput
python3 /opt/ddosdb/manage.py makemigrations
python3 /opt/ddosdb/manage.py migrate
sudo systemctl restart apache2.service
