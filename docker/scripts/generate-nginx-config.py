#!/usr/bin/env python3
"""
Generates nginx configuration blocks for serving tiles
"""
import os
import json
from pathlib import Path


def generate_tile_locations(tiles_dir='/data/tiles', domain='localhost'):
    """Generate nginx location blocks for all tile versions"""
    tiles_dir = Path(tiles_dir)
    
    if not tiles_dir.exists():
        print(f"Tiles directory not found: {tiles_dir}")
        return []
    
    configs = []
    
    # Find all tile directories
    for area_dir in sorted(tiles_dir.iterdir()):
        if not area_dir.is_dir():
            continue
        
        area = area_dir.name
        
        for version_dir in sorted(area_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            
            version = version_dir.name
            tiles_path = version_dir / 'tiles'
            metadata_path = version_dir / 'metadata.json'
            tilejson_path = version_dir / 'tilejson.json'
            
            if not tiles_path.exists() or not metadata_path.exists():
                continue
            
            # Update TileJSON with correct domain
            if tilejson_path.exists():
                try:
                    with open(tilejson_path, 'r') as f:
                        tilejson = json.load(f)
                    
                    # Update tiles URL
                    protocol = 'https' if domain != 'localhost' else 'http'
                    tilejson['tiles'] = [f'{protocol}://{domain}/{area}/{version}/{{z}}/{{x}}/{{y}}.pbf']
                    
                    with open(tilejson_path, 'w') as f:
                        json.dump(tilejson, f, separators=(',', ':'))
                except Exception as e:
                    print(f"Error updating TileJSON: {e}")
            
            # Generate location block for this version
            config = f"""# Specific version: {area}/{version}
location = /{area}/{version} {{
    alias {tilejson_path};
    expires 1w;
    default_type application/json;
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header Cache-Control public;
    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header x-ofm-debug 'specific JSON {area} {version}';
}}

location ^~ /{area}/{version}/ {{
    alias {tiles_path}/;
    try_files $uri @empty_tile;
    add_header Content-Encoding gzip;
    expires 10y;
    
    types {{
        application/vnd.mapbox-vector-tile pbf;
    }}
    
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header Cache-Control public;
    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header x-ofm-debug 'specific PBF {area} {version}';
}}
"""
            configs.append((area, version, config))
    
    return configs


def generate_latest_redirects(tiles_dir='/data/tiles'):
    """Generate redirects for /area to latest version"""
    tiles_dir = Path(tiles_dir)
    configs = []
    
    for area_dir in sorted(tiles_dir.iterdir()):
        if not area_dir.is_dir():
            continue
        
        area = area_dir.name
        
        # Find latest version (assuming sorted order)
        versions = sorted([v.name for v in area_dir.iterdir() if v.is_dir()])
        if not versions:
            continue
        
        latest_version = versions[-1]
        latest_path = area_dir / latest_version
        tiles_path = latest_path / 'tiles'
        tilejson_path = latest_path / 'tilejson.json'
        
        if not tiles_path.exists() or not tilejson_path.exists():
            continue
        
        # Generate latest location blocks  
        config = f"""# Latest version redirect: {area} -> {latest_version}
location = /{area} {{
    alias {tilejson_path};
    expires 1d;
    default_type application/json;
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header Cache-Control public;
    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header x-ofm-debug 'latest JSON {area}';
}}

# Wildcard version support for {area}
location ~ ^/{area}/([^/]+)$ {{
    root {latest_path};
    try_files /tilejson.json =404;
    expires 1w;
    default_type application/json;
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header Cache-Control public;
    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header x-ofm-debug 'wildcard JSON {area}';
}}

location ~ ^/{area}/([^/]+)/(.+)$ {{
    root {tiles_path}/;
    try_files /$2 @empty_tile;
    add_header Content-Encoding gzip;
    expires 10y;
    
    types {{
        application/vnd.mapbox-vector-tile pbf;
    }}
    
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header Cache-Control public;
    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header x-ofm-debug 'wildcard PBF {area}';
}}
"""
        configs.append((area, config))
    
    return configs


def main():
    tiles_dir = os.getenv('TILES_DIR', '/data/tiles')
    domain = os.getenv('NGINX_HOST', 'localhost')
    output_dir = Path('/etc/nginx/includes')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating nginx configuration...")
    print(f"  Tiles directory: {tiles_dir}")
    print(f"  Domain: {domain}")
    
    # Generate specific version configs
    version_configs = generate_tile_locations(tiles_dir, domain)
    
    if version_configs:
        config_content = '\n'.join(config for _, _, config in version_configs)
        output_file = output_dir / 'tiles-versions.conf'
        
        with open(output_file, 'w') as f:
            f.write(config_content)
        
        print(f"  Generated version configs: {len(version_configs)} versions")
        for area, version, _ in version_configs:
            print(f"    - {area}/{version}")
    
    # Generate latest redirects
    latest_configs = generate_latest_redirects(tiles_dir)
    
    if latest_configs:
        config_content = '\n'.join(config for _, config in latest_configs)
        output_file = output_dir / 'tiles-latest.conf'
        
        with open(output_file, 'w') as f:
            f.write(config_content)
        
        print(f"  Generated latest configs: {len(latest_configs)} areas")
        for area, _ in latest_configs:
            print(f"    - {area}")
    
    print("Configuration generation complete")


if __name__ == '__main__':
    main()

