#!/bin/bash

./manage.py collectstatic --noinput
./manage.py migrate --noinput
uwsgi --http :$VIRTUAL_PORT --module iglo.wsgi
