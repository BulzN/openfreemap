# Production Deployment

## Docker Compose (Single Host)

```bash
# Configure
cp env.example .env
nano .env  # Set AREA=planet, NGINX_HOST=your.domain

# Deploy
docker compose up -d

# Verify
curl http://localhost:8080/health
```

## Kubernetes

### Local Testing (OrbStack, k3s, minikube)

```bash
docker compose build
kubectl apply -f k8s/local.yaml
curl http://localhost:30080/health
```

### Production (GKE, EKS, AKS, Hetzner)

1. **Push images to registry:**
```bash
docker compose build
docker tag openfreemap-init:latest your-registry/openfreemap-init:latest
docker tag openfreemap-nginx:latest your-registry/openfreemap-nginx:latest
docker push your-registry/openfreemap-init:latest
docker push your-registry/openfreemap-nginx:latest
```

2. **Edit manifests:**
```bash
# k8s/configmap.yaml - set AREA and NGINX_HOST
# k8s/deployment.yaml - update image names
# k8s/service.yaml - change type to LoadBalancer or use Ingress
```

3. **Setup storage** (pick one):
- **Longhorn:** `kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/master/deploy/longhorn.yaml`
- **Ceph:** Install Rook operator
- **NFS:** Configure NFS provisioner
- **Cloud:** Use cloud provider storage class (gp3, pd-ssd, etc.)

4. **Deploy:**
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
# Edit k8s/local.yaml - change storageClassName to your storage
kubectl apply -f k8s/local.yaml
```

5. **Monitor:**
```bash
kubectl get pods -n openfreemap -w
kubectl logs -n openfreemap -l app=openfreemap --all-containers -f
```

## Storage Classes

Edit `k8s/local.yaml` PVC section:

```yaml
# Local/single-node
storageClassName: local-path        # k3s, OrbStack
storageClassName: hostpath          # minikube
storageClassName: standard          # GKE

# Multi-node (ReadWriteMany)
storageClassName: longhorn          # Longhorn
storageClassName: rook-cephfs       # Ceph
storageClassName: nfs-client        # NFS
```

## CDN Setup

### Cloudflare

1. Add DNS: `tiles.yourdomain.com` → Your server IP
2. Cloudflare automatically caches (10-year headers set)
3. Done

### CloudFront

```bash
aws cloudfront create-distribution \
  --origin-domain-name tiles.yourdomain.com \
  --default-cache-behavior "ViewerProtocolPolicy=redirect-to-https"
```

## Scaling

### Docker Compose
Not recommended for production scaling.

### Kubernetes HPA
```bash
kubectl apply -f k8s/deployment.yaml  # Has HPA config
kubectl autoscale deployment openfreemap -n openfreemap --min=2 --max=10 --cpu-percent=70
```

### Manual
```bash
kubectl scale deployment openfreemap -n openfreemap --replicas=5
```

## Security

**Init container requires `privileged: true`** for loop mounting.

For security-sensitive environments:
1. Run init job manually on a trusted node
2. Upload extracted tiles to shared storage
3. Remove init container, mount tiles read-only
4. Scale nginx without privileges

## Monitoring

```bash
# Health check
kubectl exec -n openfreemap deploy/openfreemap -- curl localhost/health

# Logs
kubectl logs -n openfreemap -l app=openfreemap --tail=100

# Resource usage
kubectl top pods -n openfreemap
```

## Troubleshooting

**Init fails with "operation not permitted"**  
Add `securityContext.privileged: true` to init container.

**Nginx returns 404 for tiles**  
Check init completed: `kubectl logs -n openfreemap -l app=openfreemap -c init`

**Out of disk space**  
Planet needs 300GB minimum. Check PVC size.

**Tiles outdated**  
Delete PVC, redeploy to download latest version.

