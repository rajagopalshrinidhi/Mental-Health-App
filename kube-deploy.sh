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
timeout=60  # Timeout in seconds
interval=5  # Check interval in seconds
elapsed=0

while true; do
    pod_status=$(kubectl get pods -l app=mental-health-app -o jsonpath='{.items[0].status.phase}')  
    if [[ "$pod_status" == "Running" ]]; then
    echo "Backend pod is running. Proceeding with port-forward..."
    break
  fi
  if (( elapsed >= timeout )); then
    echo "Timeout reached. Backend pod is still not running."
    exit 1
  fi
  echo "Pod status: $pod_status. Retrying in $interval seconds..."
  sleep $interval
  (( elapsed += interval ))
done

# Forward port to access the backend service
kubectl port-forward svc/backend-service 8000:80