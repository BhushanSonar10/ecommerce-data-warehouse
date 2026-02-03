#!/bin/bash

# E-Commerce Data Warehouse Setup Script
# This script sets up and runs the complete data warehouse pipeline

echo "=========================================="
echo "E-Commerce Data Warehouse Setup"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories if they don't exist
echo "📁 Creating project directories..."
mkdir -p data sql etl analytics

echo "🏗️  Building and starting containers..."
docker-compose up --build

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "🎉 Your data warehouse is now running!"
echo ""
echo "📊 Access Information:"
echo "   Database: localhost:5432"
echo "   Database Name: ecommerce_dw"
echo "   Username: postgres"
echo "   Password: postgres"
echo ""
echo "📈 Next Steps:"
echo "   1. Connect to PostgreSQL using your favorite client"
echo "   2. Run queries from the analytics/ folder"
echo "   3. Explore the data model and create your own analyses"
echo ""
echo "🔍 To view ETL logs:"
echo "   docker logs ecommerce_etl"
echo ""
echo "🛑 To stop the services:"
echo "   docker-compose down"
echo ""