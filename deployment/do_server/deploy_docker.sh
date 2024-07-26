#!/bin/bash

docker compose up -d
mkdir -p /opt/star-burger/media/
mkdir -p /opt/star-burger/staticfiles/
mount --bind /var/lib/docker/volumes/do_server_static/_data/ /opt/star-burger/staticfiles/
mount --bind /var/lib/docker/volumes/do_server_media/_data/ /opt/star-burger/media/
cp star-burger.conf /etc/nginx/sites-available
ln -sf /etc/nginx/sites-available/star-burger.conf /etc/nginx/sites-enabled
nginx -s reload