#!/bin/bash

cd repo
git pull
cd ..
docker-compose -p iglo-$ENVIRONMENT -f repo/deploy/docker-compose.yml --env-file ./.env up -d --no-deps
