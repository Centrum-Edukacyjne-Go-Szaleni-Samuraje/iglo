#!/usr/bin/env sh

./manage.py collectstatic --noinput
./manage.py migrate --noinput
uwsgi --http :9999 --module iglo.wsgi


