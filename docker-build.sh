#!/bin/bash
# Build backend image
docker build -t mental-health-backend:local .

# Build frontend image
docker build -t mental-health-frontend:local -f frontend/Dockerfile .

# Do docker compose up
docker compose up --build