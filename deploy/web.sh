#!/bin/bash

../deploy/wait-for-it.sh -t 60 db:5432
./manage.py collectstatic --noinput
./manage.py migrate --noinput
uwsgi --http :$VIRTUAL_PORT --module iglo.wsgi --static-map /static=/data/static --static-map /media=/data/media --master --processes 4
