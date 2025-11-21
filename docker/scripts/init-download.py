#!/usr/bin/env python3
"""
Downloads Btrfs images from OpenFreeMap CDN
Supports configurable CDN URL via BTRFS_CDN_URL environment variable
"""
import os
import subprocess
import sys
from pathlib import Path
import requests


def get_remote_file_size(url):
    """Get the size of a remote file"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=30)
        if response.status_code == 200:
            return int(response.headers.get('content-length', 0))
    except Exception as e:
        print(f"Error getting file size: {e}")
    return 0


def download_file_aria2(url, output_path):
    """Download file using aria2c for better performance"""
    print(f"Downloading: {url}")
    cmd = [
        'aria2c',
        '--max-connection-per-server=16',
        '--split=16',
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


def get_latest_version(area='planet'):
    """Fetch the latest version for an area"""
    # Use configured CDN URL or default
    cdn_url = os.getenv('BTRFS_CDN_URL', 'https://btrfs.openfreemap.com')
    url = f'{cdn_url}/files.txt'
    print(f"Fetching available versions for {area}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse files.txt to find versions
        lines = response.text.strip().split('\n')
        versions = []
        
        for line in lines:
            if f'areas/{area}/' in line and 'tiles.btrfs.gz' in line:
                # Extract version from path like: areas/planet/20240101_120000_pt/tiles.btrfs.gz
                parts = line.split('/')
                if len(parts) >= 4:
                    version = parts[2]
                    versions.append(version)
        
        if not versions:
            print(f"No versions found for {area}")
            return None
            
        # Return the latest version (assuming sorted)
        latest = sorted(versions)[-1]
        print(f"Latest version for {area}: {latest}")
        return latest
        
    except Exception as e:
        print(f"Error fetching versions: {e}")
        return None


def download_area(area, version='latest', output_dir='/data/btrfs'):
    """Download and extract Btrfs image for an area"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get latest version if needed
    if version == 'latest':
        version = get_latest_version(area)
        if not version:
            print(f"Failed to determine latest version for {area}")
            return False
    
    area_version_dir = output_dir / area / version
    btrfs_file = area_version_dir / 'tiles.btrfs'
    
    # Skip if already exists
    if btrfs_file.exists():
        print(f"Btrfs file already exists: {btrfs_file}")
        return True
    
    # Create temp directory
    temp_dir = output_dir / '_tmp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Use configured CDN URL or default
    cdn_url = os.getenv('BTRFS_CDN_URL', 'https://btrfs.openfreemap.com')
    url = f'{cdn_url}/areas/{area}/{version}/tiles.btrfs.gz'
    compressed_file = temp_dir / 'tiles.btrfs.gz'
    
    print(f"Downloading {area} {version}...")
    print(f"URL: {url}")
    
    # Check available disk space
    stat = os.statvfs(temp_dir)
    free_space = stat.f_bavail * stat.f_frsize
    
    file_size = get_remote_file_size(url)
    if file_size == 0:
        print("Warning: Could not determine remote file size")
    else:
        # Need 3x space: compressed + uncompressed + safety margin
        needed_space = file_size * 3
        free_gb = free_space / (1024**3)
        needed_gb = needed_space / (1024**3)
        
        print(f"Disk space check: {free_gb:.1f}GB free, {needed_gb:.1f}GB needed")
        
        if free_space < needed_space:
            print(f"ERROR: Not enough disk space")
            print(f"  Free: {free_gb:.1f}GB")
            print(f"  Needed: {needed_gb:.1f}GB")
            return False
    
    # Download the compressed file
    download_file_aria2(url, compressed_file)
    
    # Decompress
    print("Decompressing...")
    subprocess.run(['unpigz', str(compressed_file)], check=True)
    
    # Move to final location
    area_version_dir.mkdir(parents=True, exist_ok=True)
    decompressed_file = temp_dir / 'tiles.btrfs'
    decompressed_file.rename(btrfs_file)
    
    # Clean up temp
    subprocess.run(['rm', '-rf', str(temp_dir)], check=True)
    
    print(f"Successfully downloaded and extracted: {btrfs_file}")
    return True


if __name__ == '__main__':
    import sys
    
    area = os.getenv('AREA', 'planet')
    version = os.getenv('VERSION', 'latest')
    output_dir = os.getenv('BTRFS_DIR', '/data/btrfs')
    
    print(f"Downloading area: {area}, version: {version}")
    success = download_area(area, version, output_dir)
    
    if not success:
        sys.exit(1)

