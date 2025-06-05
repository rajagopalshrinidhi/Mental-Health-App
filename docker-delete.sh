#!/bin/bash

docker compose down --volumes --remove-orphans

# This script deletes all Docker containers, images, and volumes.
docker rmi -f $(docker images -aq)