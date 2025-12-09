#!/bin/bash
# Deploy DCMX testnet to Kubernetes

set -e

NAMESPACE=${NAMESPACE:-dcmx-testnet}
ENVIRONMENT=${ENVIRONMENT:-staging}

echo "Deploying DCMX to Kubernetes..."
echo "Namespace: $NAMESPACE"
echo "Environment: $ENVIRONMENT"

# Create namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secrets from .env file
if [ -f ".env" ]; then
    echo "Creating secrets from .env..."
    kubectl create secret generic dcmx-config \
        --from-env-file=.env \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "ERROR: .env file not found"
    exit 1
fi

# Apply Kubernetes manifests
echo "Applying Kubernetes manifests..."
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/pvc.yml
kubectl apply -f k8s/dcmx-statefulset.yml
kubectl apply -f k8s/compliance-deployment.yml
kubectl apply -f k8s/postgres-statefulset.yml
kubectl apply -f k8s/redis-deployment.yml
kubectl apply -f k8s/prometheus-deployment.yml
kubectl apply -f k8s/grafana-deployment.yml
kubectl apply -f k8s/jaeger-deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/ingress.yml
kubectl apply -f k8s/hpa.yml

# Wait for rollout
echo "Waiting for deployments to be ready..."
kubectl rollout status statefulset/dcmx-node --namespace=$NAMESPACE --timeout=5m
kubectl rollout status deployment/compliance-monitor --namespace=$NAMESPACE --timeout=5m

echo "✓ Testnet deployed successfully!"
echo ""
echo "Access points:"
echo "  - DCMX Nodes: http://dcmx.localhost"
echo "  - Prometheus: http://prometheus.localhost"
echo "  - Grafana: http://grafana.localhost"
echo "  - Jaeger: http://jaeger.localhost"
echo ""
echo "Get logs:"
echo "  kubectl logs -n $NAMESPACE deployment/compliance-monitor -f"
echo "  kubectl logs -n $NAMESPACE statefulset/dcmx-node -f"
