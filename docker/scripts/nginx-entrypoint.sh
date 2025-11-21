#!/bin/bash
set -e

echo "OpenFreeMap Nginx"

NGINX_HOST=${NGINX_HOST:-localhost}
TILES_DIR=${TILES_DIR:-/data/tiles}
ASSETS_DIR=${ASSETS_DIR:-/data/assets}

if [ ! -f "/data/.init-complete" ]; then
    echo "Waiting for init..."
    for i in {1..120}; do
        [ -f "/data/.init-complete" ] && break
        sleep 5
    done
    [ -f "/data/.init-complete" ] || { echo "Init timeout"; exit 1; }
fi

cp /etc/nginx/templates/default.conf.template /etc/nginx/conf.d/default.conf
python3 /app/generate-nginx-config.py
nginx -t
echo "Starting nginx"

exec nginx -g 'daemon off;'

