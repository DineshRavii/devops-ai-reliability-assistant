# Metrics App

**Docker Hub:** https://hub.docker.com/r/dineshravii/metrics-app

## Building (on Mac with Apple Silicon)
```bash
# Build for AMD64 (KodeKloud compatibility)
docker build --platform linux/amd64 -t dineshravii/metrics-app:v1 .

# Push
docker push dineshravii/metrics-app:v1
```

## Deploying (in KodeKloud)
```bash
# Deploy
kubectl apply -f app-deployment.yaml

# Check
kubectl get pods -l app=metrics-app
kubectl logs -l app=metrics-app

# Test
kubectl port-forward svc/metrics-app-service 8080:80
curl localhost:8080/metrics
```

## Endpoints

- `/` - Home
- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/slow` - 1-3s latency
- `/heavy` - CPU intensive
- `/error` - Returns 500

## Metrics

- `app_requests_total{endpoint, method, status}`
- `app_request_duration_seconds{endpoint}`
- `app_active_requests`
- `app_errors_total{endpoint}`
- `app_info{version, env}`