#!/bin/bash

# Check if the secret already exists
if ! kubectl get secret genai-secret >/dev/null 2>&1; then
  echo "Creating genai-secret..."
  kubectl create secret generic genai-secret \
    --from-file=api_key=/users/shrinidhirajagopal/Downloads/GCP_SA_Key.json
else
  echo "genai-secret already exists. Skipping creation."
fi

# Apply Kubernetes deployment and service configurations
kubectl apply -f k8s-deployment.yaml

# Wait for the pods to be ready
echo "Waiting for pods to be ready..."
timeout 15 echo "..."

# Forward port to access the backend service
kubectl port-forward svc/backend-service 8000:80