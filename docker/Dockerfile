# docker exec -it 5e57902b199b /bin/bash
FROM python:3.9-slim

RUN apt-get update && apt-get install -y netcat

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create user
RUN adduser --system --group ddosdb
# create the appropriate directories
ENV HOME=/home/ddosdb

USER ddosdb
WORKDIR /home/ddosdb/

# Create venv and set ENV accordingly
ENV VIRTUAL_ENV=$HOME/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# update pip
RUN pip install --upgrade pip
# install wheel
RUN pip install wheel

COPY requirements.txt $HOME

RUN pip install --requirement requirements.txt

COPY ddosdb $HOME
COPY docker/django/settings_local.py $HOME/website/

# copy entrypoint.sh
COPY docker/django/entrypoint.sh $HOME

RUN mkdir /home/ddosdb/ddosdb-static
RUN mkdir /home/ddosdb/ddosdb-data/

# chown all the files to the ddosdb user
#RUN chown -R ddosdb:ddosdb $HOME

ENTRYPOINT ["/home/ddosdb/entrypoint.sh"]

#WORKDIR /

#EXPOSE 80

#ENV PATH=/usr/sbin:$PATH
#CMD ["nginx", "-g", "daemon off;"]
