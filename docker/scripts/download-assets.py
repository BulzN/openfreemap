#!/usr/bin/env python3
"""
Downloads OpenFreeMap assets (fonts, styles, sprites)
Supports configurable CDN URL via ASSETS_CDN_URL environment variable
"""
import os
import subprocess
import sys
from pathlib import Path
import requests


def download_file(url, output_path):
    """Download a file using aria2c"""
    print(f"Downloading: {url}")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        'aria2c',
        '--max-connection-per-server=8',
        '--split=8',
        '--min-split-size=1M',
        '--file-allocation=none',
        '--console-log-level=warn',
        '--summary-interval=5',
        '--download-result=hide',
        '-d', str(output_path.parent),
        '-o', output_path.name,
        url
    ]
    subprocess.run(cmd, check=True)


def extract_tar_gz(archive_path, output_dir):
    """Extract a tar.gz archive"""
    print(f"Extracting: {archive_path}")
    subprocess.run([
        'tar',
        '-xzf',
        str(archive_path),
        '-C',
        str(output_dir)
    ], check=True)


def download_asset(asset_name, assets_dir='/data/assets'):
    """Download and extract an asset"""
    assets_dir = Path(assets_dir)
    asset_dir = assets_dir / asset_name
    asset_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded
    ofm_dir = asset_dir / 'ofm'
    if ofm_dir.exists() and any(ofm_dir.iterdir()):
        print(f"Asset {asset_name} already exists, skipping")
        return True
    
    url = f'https://assets.openfreemap.com/{asset_name}/ofm.tar.gz'
    archive_path = asset_dir / 'ofm.tar.gz'
    
    try:
        download_file(url, archive_path)
        extract_tar_gz(archive_path, asset_dir)
        archive_path.unlink()  # Clean up archive
        print(f"Successfully downloaded asset: {asset_name}")
        return True
    except Exception as e:
        print(f"Error downloading {asset_name}: {e}")
        return False


def download_sprites(assets_dir='/data/assets'):
    """Download all sprite versions"""
    assets_dir = Path(assets_dir)
    sprites_dir = assets_dir / 'sprites'
    sprites_dir.mkdir(parents=True, exist_ok=True)
    
    print("Fetching sprite versions...")
    
    # Use configured CDN URL or default
    cdn_url = os.getenv('ASSETS_CDN_URL', 'https://assets.openfreemap.com')
    
    try:
        response = requests.get(f'{cdn_url}/files.txt', timeout=30)
        response.raise_for_status()
        
        # Find all sprite archives
        sprites_remote = [
            line for line in response.text.splitlines()
            if line.startswith('sprites/') and line.endswith('.tar.gz')
        ]
        
        for sprite_path in sprites_remote:
            sprite_name = sprite_path.split('/')[1].replace('.tar.gz', '')
            sprite_version_dir = sprites_dir / sprite_name
            
            if sprite_version_dir.exists() and any(sprite_version_dir.iterdir()):
                print(f"Sprite version {sprite_name} already exists, skipping")
                continue
            
            url = f'{cdn_url}/sprites/{sprite_name}.tar.gz'
            temp_archive = sprites_dir / 'temp.tar.gz'
            
            try:
                download_file(url, temp_archive)
                extract_tar_gz(temp_archive, sprites_dir)
                temp_archive.unlink()
                print(f"Downloaded sprite version: {sprite_name}")
            except Exception as e:
                print(f"Error downloading sprite {sprite_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error downloading sprites: {e}")
        return False


def download_all_assets(assets_dir='/data/assets'):
    """Download all required assets"""
    print("Downloading OpenFreeMap assets...")
    
    assets = ['fonts', 'styles', 'natural_earth']
    success = True
    
    for asset in assets:
        if not download_asset(asset, assets_dir):
            success = False
    
    if not download_sprites(assets_dir):
        success = False
    
    return success


if __name__ == '__main__':
    assets_dir = os.getenv('ASSETS_DIR', '/data/assets')
    
    print(f"Assets directory: {assets_dir}")
    
    if not download_all_assets(assets_dir):
        print("Failed to download all assets")
        sys.exit(1)
    
    print("Successfully downloaded all assets")

