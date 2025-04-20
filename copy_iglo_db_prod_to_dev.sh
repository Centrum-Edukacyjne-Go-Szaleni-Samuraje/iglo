#!/bin/bash
set -eu

docker exec iglo-staging_db_1 pg_dump    -Fc -U postgres > iglo_dumps/iglo-staging_db_1.$(date +%Y%m%d).pg_dump
docker exec iglo-production_db_1 pg_dump -Fc -U postgres > iglo_dumps/iglo-production_db_1.$(date +%Y%m%d).pg_dump
cat iglo_dumps/iglo-production_db_1.$(date +%Y%m%d).pg_dump | docker exec -i iglo-staging_db_1 pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges --disable-triggers --no-acl
