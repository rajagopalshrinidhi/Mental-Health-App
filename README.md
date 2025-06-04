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
        └── package.json
    └── .gitignore
    └── agent.py
    └── app.py
    └── docker-build.sh
    └── docker-compose.yml
    └── Dockerfile
    └── k8s-deployment.yaml
    └── kube-delete.sh
    └── kube-deploy.sh
    └── README.md
    └── requirements.txt
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
./docker-build.sh
```
4. Access the application at:
   **http://localhost:8000**

5.  To shut down the containers, hit ctrl+c/cmd+c and then run:
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
./kube-deploy.sh
```

4. Access the application:
   - App: **http://127.0.0.1:8000**

5. Free up resources - Hit ctrl+c/cmd+c and then:
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

3. Save and reload the profile:
   ```sh
   source ~/.bash_profile
   ```

---

## Running the Application Locally

### Start the FastAPI server
Run the following to start the application:
```sh
python app.py
```

Open your web browser and navigate to **http://localhost:8000** to access the Mental Health Companion UI.

---

## Usage
Type your feelings or thoughts into the input box and click "Send".
The chatbot will respond with empathetic and supportive messages.
Type 'exit' to end the conversation and then close the webpage.

---