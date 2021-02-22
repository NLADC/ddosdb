# docker exec -it 5e57902b199b /bin/bash
FROM python:3.8.3-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY docker/requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

#COPY docker/ddosdb.conf /etc/nginx/conf.d/
#COPY docker/index.html /usr/share/nginx/html/
#RUN mkdir -p /home/ddosdb
#RUN addgroup -S ddosdb && adduser -S ddosdb -G ddosdb
RUN adduser --system --group ddosdb
# create the appropriate directories
ENV HOME=/home/ddosdb

COPY ddosdb /home/ddosdb/
COPY docker/settings_local.py /home/ddosdb/website/

# copy entrypoint.sh
COPY docker/entrypoint.sh /home/ddosdb/

RUN mkdir /home/ddosdb/ddosdb-static
RUN mkdir /home/ddosdb/ddosdb-data/

# chown all the files to the ddosdb user
RUN chown -R ddosdb:ddosdb $HOME

USER ddosdb

WORKDIR /home/ddosdb/


ENTRYPOINT ["/home/ddosdb/entrypoint.sh"]

#WORKDIR /

#EXPOSE 80

#ENV PATH=/usr/sbin:$PATH
#CMD ["nginx", "-g", "daemon off;"]
