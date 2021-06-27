# docker exec -it 5e57902b199b /bin/bash
FROM python:3.9-slim

RUN apt-get update && apt-get install -y netcat

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip

COPY requirements.txt docker/temp/
RUN pip install --requirement docker/temp/requirements.txt

RUN adduser --system --group ddosdb
# create the appropriate directories
ENV HOME=/home/ddosdb

COPY ddosdb /home/ddosdb/
COPY docker/django/settings_local.py /home/ddosdb/website/

# copy entrypoint.sh
COPY docker/django/entrypoint.sh /home/ddosdb/

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
