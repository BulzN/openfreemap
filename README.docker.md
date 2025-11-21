# OpenFreeMap - Docker & Kubernetes Implementation

A containerized deployment solution for [OpenFreeMap](https://github.com/hyperknot/openfreemap), supporting Docker Compose and Kubernetes.

> **Note:** This is a community-maintained Docker implementation. For the official OpenFreeMap project (Docker-free by design), visit [hyperknot/openfreemap](https://github.com/hyperknot/openfreemap).

## What This Provides

Self-hostable map tile server based on OpenStreetMap data, packaged for container orchestration platforms.

**Supported Platforms:**
- Docker Compose (single host)
- Kubernetes (local & production)
- Tested with Monaco test dataset (13MB) and full planet dataset (60GB compressed)

## Quick Start

### Docker Compose

```bash
cd docker

# Configure
cp env.example .env
# Edit AREA= to "monaco" or "planet"

# Deploy
docker compose up -d

# Test
open http://localhost:8080
```

### Kubernetes (Local)

```bash
cd docker

# Build images
docker compose build

# Deploy
kubectl apply -f k8s/local.yaml

# Test
open http://localhost:30080
```

## Documentation

- **[Quick Start Guide](docker/README.md)** - Getting started with Docker/K8s
- **[Production Deployment](docker/DEPLOY.md)** - Production setup, scaling, CDN integration
- **[Original Project](https://github.com/hyperknot/openfreemap)** - Upstream OpenFreeMap documentation

## Storage Requirements

- Monaco test dataset: ~1GB
- Planet (full world): ~300GB

## Architecture

```
Init Container (runs once):
  ├─ Download Btrfs tile image
  ├─ Loop-mount and extract to /data/tiles
  └─ Download assets (fonts, sprites, styles)

Nginx Container (horizontally scalable):
  ├─ Generate config based on available tiles
  └─ Serve tiles, assets, and test viewer
```

## Production Considerations

### Storage
For multi-node deployments, use distributed storage:
- **Kubernetes:** Longhorn, Ceph (via Rook), NFS with ReadWriteMany
- **Docker Swarm:** GlusterFS, Ceph, NFS volumes
- **Single node:** Local volumes work fine

### Security
Init container requires `privileged: true` for loop mounting Btrfs images. For security-sensitive environments, pre-extract tiles on a trusted system and mount as read-only volume.

### Scaling
Nginx containers are stateless and scale horizontally. Tile data is read-only after initialization.

## Implementation Differences

| Aspect | Original OpenFreeMap | This Implementation |
|--------|---------------------|---------------------|
| Deployment | Bare metal / VMs | Containers (Docker/K8s) |
| Btrfs handling | Direct loop mount | Extract to filesystem |
| Privileges | `CAP_SYS_ADMIN` on host | Privileged init container only |
| Disk usage | Compressed Btrfs images | Extracted files (larger) |
| Trade-off | Disk-efficient | Container-friendly |

## CDN Integration

Works out-of-the-box with CDNs:
- Tiles have 10-year cache headers
- CORS enabled for cross-origin requests
- Compatible with Cloudflare, CloudFront, Fastly, etc.

## Contributing

This is a community project. Issues and PRs welcome!

For the core OpenFreeMap functionality, contribute to the [upstream project](https://github.com/hyperknot/openfreemap).

## License

Same as OpenFreeMap parent project - see [LICENSE.md](LICENSE.md)

## Acknowledgments

Built on top of [OpenFreeMap](https://github.com/hyperknot/openfreemap) by [@hyperknot](https://github.com/hyperknot).

Inspired by the need for a container-native deployment option for cloud and Kubernetes environments.

