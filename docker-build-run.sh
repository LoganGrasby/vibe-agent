#!/bin/bash

# Docker build and run script for vibe-agent

set -e  # Exit on any error

# Configuration
IMAGE_NAME="vibe-agent"
CONTAINER_NAME="vibe-agent-container"

echo "🐳 Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME .

echo "🧹 Stopping and removing existing container if it exists"
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "🚀 Running Docker container: $CONTAINER_NAME"
docker run \
    --name $CONTAINER_NAME \
    --rm \
    $IMAGE_NAME

echo "📋 Container status:"
docker ps -f name=$CONTAINER_NAME

echo "📝 To view logs, run: docker logs -f $CONTAINER_NAME"
echo "🛑 To stop the container, run: docker stop $CONTAINER_NAME"
echo "🗑️  To remove the container, run: docker rm $CONTAINER_NAME"
