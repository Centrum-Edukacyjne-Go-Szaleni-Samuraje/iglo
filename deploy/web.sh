#!/bin/bash

./manage.py collectstatic --noinput
./manage.py migrate --noinput
uwsgi --socket :$VIRTUAL_PORT --module iglo.wsgi
