#!/bin/bash

# Petri Project Setup Script
# This script helps with initial setup and common development tasks

set -e

echo "🧪 Petri Project Setup"
echo "======================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your configuration."
else
    echo "✅ .env file already exists."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "🐳 Docker is running."

# Build images
echo "🔨 Building Docker images..."
docker-compose build

# Start infrastructure services first
echo "🚀 Starting infrastructure services..."
docker-compose up -d db neo4j redis

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys and preferences"
echo "2. Run 'make dev-up' to start development environment"
echo "3. Access Jupyter at http://localhost:8888 (token: petri_jupyter_token)"
echo "4. Access World API at http://localhost:8000/docs"
echo "5. Access Neo4j browser at http://localhost:7474"
echo ""
echo "Run 'make help' for more commands."
