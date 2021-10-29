#!/bin/bash

cd repo
git pull
cd ..
docker-compose -p iglo-$ENVIRONMENT -f repo/deploy/docker-compose.yml up -d --no-deps --build web
