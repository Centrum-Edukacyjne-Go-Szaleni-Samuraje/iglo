#!/bin/bash

docker-compose -p iglo-$ENVIRONMENT -f repo/deploy/docker-compose.yml --env-file ./.env up -d --no-deps --build web
docker-compose -p iglo-$ENVIRONMENT -f repo/deploy/docker-compose.yml --env-file ./.env up -d --no-deps --build worker
