#!/bin/bash

docker compose up -d
mkdir -p media
mkdir -p static
mount --bind /var/lib/docker/volumes/do_server_static/_data/ /opt/star-burger/static/
mount --bind /var/lib/docker/volumes/do_server_media/_data/ /opt/star-burger/media/
cp starburger_docker.conf /etc/nginx/sites-available
ln -sf /etc/nginx/sites-available/starburger_docker.conf /etc/nginx/sites-enabled
nginx -s reload