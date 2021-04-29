#!/bin.bash
python app.py db init&&
python app.py db migrate&&
python app.py db upgrade
docker-compose -f docker-compose.yml scale redis-slave=2
docker-compose -f docker-compose.yml scale sentinel=3
docker-compose -f docker-compose.yml scale application=3
gunicorn application.wsgi:application -c gunicorn.conf.py

