# Mental Health Companion

Welcome to the Mental Health Companion! This project provides a supportive and empathetic chatbot designed to assist users with their mental health and well-being.

## Features

- Provides empathetic and supportive responses to user inputs.
- Maintains a conversation context to keep the dialogue coherent.
- Avoids answering technical, mathematical, or unrelated questions.
- Simple and relaxing web-based user interface.

## Project Structure
```
└── 📁Mental-Health-App
    └── 📁frontend
        └── background.jpg
        └── Dockerfile
        └── index.html
        └── package-lock.json
        └── package.json
    └── 📁monitoring
        └── 📁grafana
            └── 📁dashboards
                └── mental-health-mlops.json
            └── 📁provisioning
                └── 📁dashboards
                    └── dashboard.yml
                └── 📁datasources
                    └── prometheus.yml
        └── alert_rules.yml
        └── alertmanager.yml
        └── prometheus.yml
    └── .gitignore
    └── agent.py
    └── app.py
    └── docker-compose.yml
    └── Dockerfile
    └── enterprise_monitoring.py
    └── k8s-grafana-dashboard.yaml
    └── k8s-grafana-jaeger.yaml
    └── k8s-mental-health-app.yaml
    └── k8s-monitoring-stack.yaml
    └── k8s-prometheus.yaml
    └── kube-delete.sh
    └── README.md
    └── requirements.txt
    └── universal-deploy.sh
    └── vertex_ai.py
```

## Setup and Installation

### Prerequisites

- Python 3.7 or higher
- FastAPI
- Uvicorn
- Pydantic
- Google Generative AI
- Docker Desktop (with Kubernetes enabled)

---

## Running the Application with Docker

### Build and Run the Docker Image

1. Open Docker Desktop and go to **Settings** > **Resources** > **File Sharing**.

2. Add the directory where your GCP service account key is present (e.g., `/path/to/your/service/account/key.json`).

3. To build and run the app in Docker containers:
```sh
./universal-deploy docker
```
4. Access the application at:
   **http://localhost:8000**
   **Grafana: http://localhost:3001 (admin/admin123)**

5.  To shut down the containers:
```sh
docker compose down
```

---

## Running the Application with Kubernetes

### Starting Kubernetes Cluster from Docker Desktop
1. Open Docker Desktop and go to **Settings** > **Kubernetes**.
2. Enable Kubernetes by toggling the switch.
3. Apply the changes and wait for Kubernetes to start.

### Deploying to Kubernetes
1. To deploy the pods and start services, run
```sh
./universal-deploy kubernetes
```

4. Access the application:
   - App: http://localhost:8080
   - Grafana: http://localhost:3001 (admin/admin123)
   - Prometheus: http://localhost:9090

5. Free up resources:
```sh
./kube-delete.sh
```

---

## Environment Variables

### Setting Up Google Cloud Credentials
1. Open your terminal and edit your shell profile:
   ```sh
   nano ~/.bash_profile
   ```

2. Add the following line:
   ```sh
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/GCP_SA_Key.json"
   ```
      ```sh
   export GOOGLE_CLOUD_PROJECT="<name of Google Cloud project>"
   ```
   Please verify if the LLM being used in the app is still valid. Use the latest stable version from https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions

3. Save and reload the profile:
   ```sh
   source ~/.bash_profile
   ```

---

## Running the Application Locally

### Start the FastAPI server
Run the following to start the application:
```sh
./universal-deploy.sh local
```

Open your web browser and navigate to **http://localhost:8000** to access the Mental Health Companion UI.

---

## Usage
Type your feelings or thoughts into the input box and click "Send".
The chatbot will respond with empathetic and supportive messages.
Type 'exit' to end the conversation and then close the webpage.

---

## Monitoring and Metrics
These are available at the moment when deploying via Docker alone

### Grafana (Dashboards)
- **URL**: http://localhost:3001
- **Login**: admin / admin123
- **Dashboard**: "Mental Health Companion - MLOps Dashboard"

### Prometheus (Metrics)
- **URL**: http://localhost:9090
- **Targets**: http://localhost:9090/targets
- **Graph**: http://localhost:9090/graph

### Alertmanager (Alerts)
- **URL**: http://localhost:9093
- **Alerts**: http://localhost:9093/#/alerts

### System Monitoring
- **Node Exporter**: http://localhost:9100/metrics
- **cAdvisor**: http://localhost:8080

---

## Metrics Reference & Queries

### HTTP Request Metrics
- **Total Requests**: `mental_health_requests_total`
- **Request Rate**: `rate(mental_health_requests_total[5m])`
- **Requests by Status Code**: `mental_health_requests_total by (status_code)`
- **Success Rate**: `(sum(rate(mental_health_requests_total{status_code="200"}[5m])) / sum(rate(mental_health_requests_total[5m]))) * 100`
- **Error Rate**: `sum(rate(mental_health_requests_total{status_code=~"4..|5.."}[5m]))`

### Response Time Metrics
- **Median Response Time**: `histogram_quantile(0.50, rate(mental_health_request_duration_seconds_bucket[5m]))`
- **95th Percentile Response Time**: `histogram_quantile(0.95, rate(mental_health_request_duration_seconds_bucket[5m]))`
- **Slow Requests (>2 seconds)**: `histogram_quantile(0.95, rate(mental_health_request_duration_seconds_bucket[5m])) > 2`

### AI Model Performance Metrics
- **AI Requests per Second**: `rate(mental_health_ai_requests_total[5m])`
- **AI Success Rate**: `rate(mental_health_ai_requests_total{status="success"}[5m]) / rate(mental_health_ai_requests_total[5m])`
- **AI Latency**: `rate(mental_health_ai_latency_seconds_sum[5m]) / rate(mental_health_ai_latency_seconds_count[5m])`

### User Session Metrics
- **Active Sessions**: `mental_health_active_sessions`
- **Session Growth Rate**: `deriv(mental_health_active_sessions[10m])`

### Error Tracking Metrics
- **Error Rate**: `rate(mental_health_errors_total[5m])`
- **Errors by Type**: `sum(rate(mental_health_errors_total[5m])) by (error_type)`
- **Critical Errors**: `rate(mental_health_errors_total{severity="critical"}[5m])`

### System Resource Metrics
- **Memory Usage**: `mental_health_system_resources{resource_type="memory_percent"}`
- **CPU Usage**: `mental_health_system_resources{resource_type="cpu_percent"}`
- **High Resource Usage Alert**: `mental_health_system_resources{resource_type="memory_percent"} > 80`

---

## Test Commands for Metrics Generation

### Generate Traffic
```bash
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/mental-health \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Test request $i for metrics\", \"session_id\": \"session-$i\"}" &
done
```

### Health Checks
```bash
curl http://localhost:8000/health
```

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

### Debug Trace
```bash
curl http://localhost:8000/debug/trace
```

### Test Jaeger Trace (Recommended)
```bash
curl http://localhost:8000/test-trace
```
This endpoint creates nested spans to verify Jaeger tracing is working properly.