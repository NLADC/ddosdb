FROM python:3.11-slim

RUN apt-get update && apt-get install -y netcat-traditional

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
# downgrade setuptools to <58 to support 2to3 builds (for demjson 2.2.4 on Mac)
RUN pip install --upgrade setuptools==57.5.0

COPY requirements.txt $HOME

RUN pip install --requirement requirements.txt

COPY --chown=ddosdb:ddosdb ddosdb $HOME
COPY --chown=ddosdb:ddosdb docker/django/settings_local.py $HOME/website/

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
