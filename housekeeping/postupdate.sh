cp -R /home/ddosdb/.ddosdb/ddosdb/ddosdb/. /opt/ddosdb/.
python3 /opt/ddosdb/manage.py collectstatic
sudo systemctl restart apache2.service
