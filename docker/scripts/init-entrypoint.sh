#!/bin/bash
set -e

echo "OpenFreeMap Init"

AREA=${AREA:-planet}
VERSION=${VERSION:-latest}
SKIP_DOWNLOAD=${SKIP_DOWNLOAD:-false}
SKIP_EXTRACT=${SKIP_EXTRACT:-false}
SKIP_ASSETS=${SKIP_ASSETS:-false}
BTRFS_DIR=${BTRFS_DIR:-/data/btrfs}
TILES_DIR=${TILES_DIR:-/data/tiles}
ASSETS_DIR=${ASSETS_DIR:-/data/assets}

echo "Config: area=$AREA version=$VERSION"

if [ "$SKIP_DOWNLOAD" != "true" ]; then
    echo "Downloading Btrfs image..."
    python3 /app/init-download.py
fi

if [ "$SKIP_EXTRACT" != "true" ]; then
    echo "Extracting tiles..."
    command -v rsync &> /dev/null || apt-get update && apt-get install -y rsync
    python3 /app/extract-btrfs.py
fi

if [ "$SKIP_ASSETS" != "true" ]; then
    echo "Downloading assets..."
    python3 /app/download-assets.py
fi

echo "Generating TileJSON..."
for area_dir in "$TILES_DIR"/*; do
    [ -d "$area_dir" ] || continue
    area=$(basename "$area_dir")
    
    for version_dir in "$area_dir"/*; do
        [ -d "$version_dir" ] || continue
        version=$(basename "$version_dir")
        metadata_file="$version_dir/metadata.json"
        
        if [ -f "$metadata_file" ]; then
            tilejson_file="$version_dir/tilejson.json"
            python3 /app/scripts/metadata_to_tilejson.py --minify \
                "$metadata_file" "$tilejson_file" "http://localhost/$area/$version"
        fi
    done
done

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > /data/.init-complete
echo "Init complete"

