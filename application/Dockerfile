#python version
FROM pypy:3.7

# maintainer information
MAINTAINER glltch@yeah.net

# specify working directory
WORKDIR  /application

# copy the host file to the corresponding location of the container environment
COPY gunicorn.conf.py /etc/gunicorn.conf.py
COPY requirements.txt /application

# install dependencies
RUN pip3 install  -r requirements.txt

COPY . /application

# specify python enviroment variables
ENV PYTHONUNBUFFERED 1
ENV SPIDER=/application





