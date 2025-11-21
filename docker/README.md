# OpenFreeMap - Containerized Deployment

Containerized tile server for OpenFreeMap, serving vector tiles without privileged loop mounts.

## What This Is

Self-hostable map tile server based on OpenStreetMap data. Serves vector tiles (`.pbf`) and includes a test viewer.

**What works:**
- Docker Compose (single host)
- Kubernetes (tested on OrbStack, works on any K8s)
- Monaco test dataset (13MB)
- Full planet dataset (60GB compressed, 200GB extracted)

## Quick Start

### Docker Compose

```bash
# 1. Configure
cp env.example .env
# Edit AREA= to "monaco" or "planet"

# 2. Deploy
docker compose up -d

# 3. Test
open http://localhost:8080
```

### Kubernetes

```bash
# 1. Build images
docker compose build

# 2. Deploy (adjust AREA in k8s/local.yaml if needed)
kubectl apply -f k8s/local.yaml

# 3. Test
open http://localhost:30080
```

## Storage Requirements

- Monaco: 1GB
- Planet: 300GB minimum

## Production Considerations

**Storage:** Use distributed storage for multi-node deployments:
- Kubernetes: Longhorn, Ceph, NFS with ReadWriteMany
- Docker Swarm: GlusterFS, Ceph, NFS volumes
- Single node: Local volumes work fine

**Scaling:** Nginx pods are stateless, scale horizontally. Tile data is read-only after init.

**Init Container:** Requires `privileged: true` for loop mounting Btrfs images. For security-sensitive environments, pre-extract tiles and mount as read-only volume.

## Architecture

```
Init Container (runs once):
  1. Download Btrfs tile image
  2. Loop-mount and extract to /data/tiles
  3. Download assets (fonts, sprites, styles)

Nginx Container (scales horizontally):
  1. Generate config based on available tiles
  2. Serve tiles, assets, and test viewer
```

## Configuration

Edit `env.example` or K8s ConfigMap:

```bash
AREA=monaco              # or "planet"
VERSION=latest           # or specific version
NGINX_HOST=localhost     # your domain for production
```

## Health Check

```bash
bash scripts/health-check.sh http://localhost:8080
```

## File Structure

```
docker/
├── Dockerfile.init           # Init container (download/extract)
├── Dockerfile.nginx          # Nginx serving container
├── docker-compose.yml        # Single-host deployment
├── k8s/
│   ├── local.yaml           # Local K8s (OrbStack tested)
│   ├── deployment.yaml      # Production deployment
│   ├── service.yaml         # K8s service
│   ├── configmap.yaml       # Configuration
│   ├── init-job.yaml        # Standalone init job
│   └── namespace.yaml       # Namespace definition
├── nginx/
│   ├── nginx.conf           # Main config
│   ├── default.conf.template # Server block template
│   └── index.html           # Test viewer
└── scripts/
    ├── init-entrypoint.sh        # Init orchestration
    ├── init-download.py          # Download Btrfs images
    ├── extract-btrfs.py          # Extract tiles
    ├── download-assets.py        # Download fonts/sprites/styles
    ├── nginx-entrypoint.sh       # Nginx startup
    ├── generate-nginx-config.py  # Dynamic location blocks
    └── health-check.sh           # Health verification
```

## Implementation Choices

This implementation prioritizes:
- **Stateless serving:** Nginx reads from shared volume, no local state
- **Standard containers:** No privileged mode for serving (only init)
- **Cloud-native:** Designed for Kubernetes, works with Docker Compose

You choose:
- Storage backend (Longhorn/Ceph/NFS/local)
- Orchestration (K8s/Swarm/Compose)
- Scaling strategy (HPA/manual/fixed)

## Differences from Original OpenFreeMap

Original: Loop-mounts Btrfs directly, requires `CAP_SYS_ADMIN`, runs on bare metal  
This: Extracts tiles to regular filesystem, container-friendly, cloud-ready

Trade-off: Uses more disk (extracted vs compressed) for deployment flexibility.

## CDN Integration

Put Cloudflare/CloudFront in front:
- Tiles have 10-year cache headers
- CORS enabled
- TileJSON includes domain substitution

## License

Same as OpenFreeMap parent project.
