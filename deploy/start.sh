#!/usr/bin/env sh

docker run -d --name iglo -p 9999:9999 -e DEBUG=false -v `pwd`/data:/data iglo
