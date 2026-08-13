# Kubernetes Assets

These manifests deploy the RideSphere application tier only:

- `backend-deployment.yaml`
- `backend-service.yaml`
- `frontend-deployment.yaml`
- `frontend-service.yaml`
- `configmap.yaml`
- `secret-example.yaml`
- `ingress.yaml`
- `hpa.yaml`

PostgreSQL, MongoDB, and Redis are intentionally not deployed as Kubernetes pods here. The Kubernetes manifests assume managed services or externally reachable instances.

## Images

The manifests default to local image names:

- `ridesphere-backend:local`
- `ridesphere-frontend:local`

For real environments, replace those tags with images from your registry such as Azure Container Registry.

## Secret Handling

Do not apply `secret-example.yaml` directly in production.

Use it as documentation only, then create a real secret:

```bash
kubectl create secret generic ridesphere-secrets \
  --from-literal=DATABASE_URL='postgresql+psycopg://...' \
  --from-literal=MONGODB_URL='mongodb://...' \
  --from-literal=REDIS_URL='redis://...' \
  --from-literal=CELERY_BROKER_URL='redis://...' \
  --from-literal=CELERY_RESULT_BACKEND='redis://...' \
  --from-literal=JWT_SECRET_KEY='replace-with-a-long-random-secret'
```

## Local Kubernetes Testing

One workable local flow on Docker Desktop Kubernetes is:

1. Build the images:

```bash
docker build -t ridesphere-backend:local ./backend
docker build -t ridesphere-frontend:local ./frontend
```

2. Start local dependency services outside Kubernetes:

```bash
docker compose up -d postgres mongodb redis
```

3. Create the runtime secret with host-reachable connection strings. On Docker Desktop for Windows and macOS, `host.docker.internal` is usually appropriate:

```bash
kubectl create secret generic ridesphere-secrets \
  --from-literal=DATABASE_URL='postgresql+psycopg://ridesphere:ridesphere_local_password@host.docker.internal:5432/ridesphere' \
  --from-literal=MONGODB_URL='mongodb://host.docker.internal:27017' \
  --from-literal=REDIS_URL='redis://host.docker.internal:6379/0' \
  --from-literal=CELERY_BROKER_URL='redis://host.docker.internal:6379/0' \
  --from-literal=CELERY_RESULT_BACKEND='redis://host.docker.internal:6379/1' \
  --from-literal=JWT_SECRET_KEY='ridesphere-local-jwt-secret-change-me'
```

4. Apply the manifests:

```bash
kubectl apply -f infrastructure/kubernetes/configmap.yaml
kubectl apply -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/backend-service.yaml
kubectl apply -f infrastructure/kubernetes/frontend-deployment.yaml
kubectl apply -f infrastructure/kubernetes/frontend-service.yaml
kubectl apply -f infrastructure/kubernetes/ingress.yaml
kubectl apply -f infrastructure/kubernetes/hpa.yaml
```

5. If you do not have an ingress controller locally, use port-forwarding instead:

```bash
kubectl port-forward svc/ridesphere-frontend 3000:80
kubectl port-forward svc/ridesphere-backend 8000:8000
```

## Validation

Client-side validation can be run without deploying:

```bash
kubectl apply --dry-run=client -f infrastructure/kubernetes/configmap.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/secret-example.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/backend-deployment.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/backend-service.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/frontend-deployment.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/frontend-service.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/ingress.yaml
kubectl apply --dry-run=client -f infrastructure/kubernetes/hpa.yaml
```
