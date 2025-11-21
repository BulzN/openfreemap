#!/usr/bin/env python3
"""
Extracts tiles from Btrfs image to regular filesystem
This allows Docker containers to serve tiles without privileged mode
"""
import os
import subprocess
import shutil
import sys
import tempfile
from pathlib import Path


def mount_btrfs(btrfs_file, mount_point):
    """Mount a Btrfs image using loop device"""
    mount_point = Path(mount_point)
    mount_point.mkdir(parents=True, exist_ok=True)
    
    print(f"Mounting {btrfs_file} to {mount_point}")
    
    # Find available loop device
    result = subprocess.run(
        ['losetup', '-f'],
        capture_output=True,
        text=True,
        check=True
    )
    loop_device = result.stdout.strip()
    
    # Setup loop device
    subprocess.run(
        ['losetup', loop_device, str(btrfs_file)],
        check=True
    )
    
    # Mount the filesystem
    subprocess.run(
        ['mount', '-t', 'btrfs', '-o', 'ro', loop_device, str(mount_point)],
        check=True
    )
    
    return loop_device, mount_point


def unmount_btrfs(mount_point, loop_device):
    """Unmount Btrfs and cleanup loop device"""
    print(f"Unmounting {mount_point}")
    
    try:
        subprocess.run(['umount', str(mount_point)], check=True)
        subprocess.run(['losetup', '-d', loop_device], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Error during unmount: {e}")


def extract_tiles(btrfs_file, output_dir, area, version):
    """Extract tiles from Btrfs image to regular filesystem"""
    btrfs_file = Path(btrfs_file)
    output_dir = Path(output_dir)
    
    if not btrfs_file.exists():
        print(f"Error: Btrfs file not found: {btrfs_file}")
        return False
    
    # Create output directory
    tiles_output = output_dir / area / version
    
    # Check if already extracted
    if tiles_output.exists() and (tiles_output / 'tiles').exists():
        print(f"Tiles already extracted to {tiles_output}")
        return True
    
    print(f"Extracting tiles from {btrfs_file} to {tiles_output}")
    
    # Create temporary mount point
    with tempfile.TemporaryDirectory() as temp_mount:
        loop_device = None
        
        try:
            # Mount the Btrfs image
            loop_device, mount_point = mount_btrfs(btrfs_file, temp_mount)
            
            # Check mount was successful
            tiles_dir = Path(mount_point) / 'tiles'
            metadata_file = Path(mount_point) / 'metadata.json'
            
            if not tiles_dir.exists():
                print(f"Error: tiles directory not found in Btrfs image")
                return False
            
            # Create output directory
            tiles_output.mkdir(parents=True, exist_ok=True)
            
            # Copy tiles using rsync for efficiency
            # Note: We use rsync instead of cp because it handles hardlinks better
            print(f"Copying tiles... This may take a while for planet data.")
            print(f"Source: {tiles_dir}")
            print(f"Destination: {tiles_output / 'tiles'}")
            
            # For large datasets, we use rsync with compression
            subprocess.run([
                'rsync',
                '-a',  # archive mode
                '--info=progress2',  # show progress
                str(tiles_dir) + '/',
                str(tiles_output / 'tiles') + '/'
            ], check=True)
            
            # Copy metadata
            if metadata_file.exists():
                shutil.copy2(metadata_file, tiles_output / 'metadata.json')
                print(f"Copied metadata.json")
            
            print(f"Successfully extracted tiles to {tiles_output}")
            return True
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            return False
            
        finally:
            # Cleanup: unmount and remove loop device
            if loop_device:
                unmount_btrfs(temp_mount, loop_device)
    
    return False


def extract_all_areas(btrfs_dir='/data/btrfs', tiles_dir='/data/tiles'):
    """Extract all downloaded Btrfs images"""
    btrfs_dir = Path(btrfs_dir)
    
    if not btrfs_dir.exists():
        print(f"No Btrfs directory found: {btrfs_dir}")
        return False
    
    success = True
    
    # Find all Btrfs files
    for area_dir in btrfs_dir.iterdir():
        if not area_dir.is_dir() or area_dir.name.startswith('_'):
            continue
        
        area = area_dir.name
        
        for version_dir in area_dir.iterdir():
            if not version_dir.is_dir():
                continue
            
            version = version_dir.name
            btrfs_file = version_dir / 'tiles.btrfs'
            
            if btrfs_file.exists():
                print(f"\n{'='*60}")
                print(f"Processing {area}/{version}")
                print(f"{'='*60}")
                
                if not extract_tiles(btrfs_file, tiles_dir, area, version):
                    success = False
    
    return success


if __name__ == '__main__':
    # Check if running as root (needed for loop mount)
    if os.geteuid() != 0:
        print("Error: This script must be run as root (for loop mounting)")
        sys.exit(1)
    
    btrfs_dir = os.getenv('BTRFS_DIR', '/data/btrfs')
    tiles_dir = os.getenv('TILES_DIR', '/data/tiles')
    
    print("Starting tile extraction...")
    print(f"Btrfs source: {btrfs_dir}")
    print(f"Tiles output: {tiles_dir}")
    
    success = extract_all_areas(btrfs_dir, tiles_dir)
    
    if not success:
        print("\nExtraction completed with errors")
        sys.exit(1)
    
    print("\nExtraction completed successfully")

