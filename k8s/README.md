# Kubernetes Deployment Guide

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Helm (optional)

## Quick Deploy

```bash
# Create namespace
kubectl apply -f deployment.yaml

# Verify deployment
kubectl get pods -n devscout
kubectl get services -n devscout

# Check logs
kubectl logs -f deployment/fastapi -n devscout
```

## Configuration

### Secrets
Update `devscout-secrets` with production values:
```bash
kubectl create secret generic devscout-secrets \
  --from-literal=POSTGRES_PASSWORD=your-password \
  --from-literal=JWT_SECRET_KEY=your-secret-key \
  -n devscout
```

### Ingress
Update `devscout-ingress` with your domain:
- Replace `api.devscout.com` with your domain
- Install cert-manager for SSL

## Scaling

Manual scaling:
```bash
kubectl scale deployment fastapi --replicas=5 -n devscout
```

Auto-scaling is configured via HPA (3-10 replicas).

## Monitoring

```bash
# Get HPA status
kubectl get hpa -n devscout

# Get resource usage
kubectl top pods -n devscout
```
