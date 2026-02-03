# Deployment Guide

This guide provides comprehensive instructions for deploying the E-Commerce Data Warehouse in different environments.

## 🚀 Quick Deployment

### Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Resources**: 4GB RAM, 2GB disk space
- **Network**: Ports 5432, 6379, 8080, 5000 available

### One-Command Deployment

```bash
# Clone and deploy
git clone https://github.com/yourusername/ecommerce-data-warehouse.git
cd ecommerce-data-warehouse
make setup && make up
```

## 🏗️ Environment-Specific Deployments

### Development Environment

```bash
# Setup development environment
cp .env.example .env
make up

# Create Airflow admin user
make airflow-user

# Access services
# - Airflow: http://localhost:8080 (admin/admin)
# - Monitoring: http://localhost:5000
# - PostgreSQL: localhost:5432 (postgres/postgres)
```

### Staging Environment

```bash
# Create staging configuration
cp docker-compose.yml docker-compose.staging.yml

# Update staging-specific settings
# - Use staging database names
# - Configure staging-specific resources
# - Set appropriate log levels

# Deploy to staging
make deploy-staging
```

### Production Environment

```bash
# Create production configuration
cp docker-compose.yml docker-compose.prod.yml

# Update production settings (see Production Configuration section)
# Deploy to production
make deploy-prod
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database Configuration
DB_HOST=postgres
DB_NAME=ecommerce_dw
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PASSWORD=your_redis_password

# Airflow Configuration
AIRFLOW__CORE__FERNET_KEY=your_32_character_fernet_key
AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key

# Security Settings
API_KEY=your_api_key
JWT_SECRET=your_jwt_secret
```

### Production Configuration

For production deployments, update `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    restart: unless-stopped

  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD}
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    restart: unless-stopped

  # Add production-specific configurations for other services
```

## 🐳 Docker Deployment Options

### Single-Node Deployment

```bash
# Standard deployment on single machine
docker-compose up -d

# With resource limits
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Docker Swarm Deployment

```bash
# Initialize Docker Swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml ecommerce-dw

# Scale services
docker service scale ecommerce-dw_etl=2
```

### Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: ecommerce_dw
        - name: POSTGRES_USER
          value: postgres
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

## ☁️ Cloud Deployments

### AWS Deployment

#### Using ECS (Elastic Container Service)

```bash
# Install AWS CLI and ECS CLI
pip install awscli
curl -Lo ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-linux-amd64-latest

# Configure ECS CLI
ecs-cli configure --cluster ecommerce-dw --region us-west-2

# Create ECS cluster
ecs-cli up --keypair your-key-pair --capability-iam --size 2 --instance-type t3.medium

# Deploy services
ecs-cli compose --file docker-compose.yml up
```

#### Using EKS (Elastic Kubernetes Service)

```bash
# Create EKS cluster
eksctl create cluster --name ecommerce-dw --region us-west-2

# Deploy to EKS
kubectl apply -f k8s/
```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and push images
docker build -t gcr.io/your-project/ecommerce-etl ./etl
docker push gcr.io/your-project/ecommerce-etl

# Deploy to Cloud Run
gcloud run deploy ecommerce-etl \
  --image gcr.io/your-project/ecommerce-etl \
  --platform managed \
  --region us-central1
```

#### Using GKE (Google Kubernetes Engine)

```bash
# Create GKE cluster
gcloud container clusters create ecommerce-dw \
  --zone us-central1-a \
  --num-nodes 3

# Deploy to GKE
kubectl apply -f k8s/
```

### Azure Deployment

#### Using Container Instances

```bash
# Create resource group
az group create --name ecommerce-dw --location eastus

# Deploy container group
az container create \
  --resource-group ecommerce-dw \
  --file docker-compose.yml
```

## 🔒 Security Configuration

### SSL/TLS Configuration

```yaml
# nginx-ssl.conf
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://monitoring:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /airflow/ {
        proxy_pass http://airflow-webserver:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Database Security

```sql
-- Create read-only user for monitoring
CREATE USER monitoring_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ecommerce_dw TO monitoring_user;
GRANT USAGE ON SCHEMA public TO monitoring_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

-- Create ETL user with limited permissions
CREATE USER etl_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ecommerce_dw TO etl_user;
GRANT USAGE, CREATE ON SCHEMA public TO etl_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO etl_user;
```

### Network Security

```yaml
# docker-compose.security.yml
version: '3.8'

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  postgres:
    networks:
      - backend
    # Remove external port exposure
    # ports:
    #   - "5432:5432"

  redis:
    networks:
      - backend
    # Remove external port exposure
    # ports:
    #   - "6379:6379"

  nginx:
    image: nginx:alpine
    networks:
      - frontend
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
```

## 📊 Monitoring and Logging

### Production Monitoring

```yaml
# monitoring-stack.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

  alertmanager:
    image: prom/alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

### Centralized Logging

```yaml
# logging-stack.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

## 🔄 Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ecommerce_dw_$DATE.sql"

# Create backup
docker-compose exec postgres pg_dump -U postgres ecommerce_dw > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE.gz s3://your-backup-bucket/

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### Disaster Recovery

```bash
# Recovery procedure
#!/bin/bash

# 1. Stop services
docker-compose down

# 2. Restore database
docker-compose up -d postgres
sleep 30

# 3. Restore from backup
gunzip -c backup_file.sql.gz | docker-compose exec -T postgres psql -U postgres -d ecommerce_dw

# 4. Start all services
docker-compose up -d

# 5. Verify data integrity
make test-data
```

## 🧪 Health Checks and Validation

### Deployment Validation

```bash
# Validate deployment
#!/bin/bash

echo "Validating deployment..."

# Check service health
docker-compose ps

# Test database connection
docker-compose exec postgres pg_isready -U postgres

# Test Redis connection
docker-compose exec redis redis-cli ping

# Test ETL pipeline
make etl-test

# Test data quality
make test-data

# Test monitoring dashboard
curl -f http://localhost:5000/api/health

echo "Deployment validation complete!"
```

### Performance Testing

```bash
# Load testing script
#!/bin/bash

# Test ETL performance
time make etl-run

# Test database query performance
docker-compose exec postgres psql -U postgres -d ecommerce_dw -c "\timing on" -f analytics/monthly_revenue.sql

# Test cache performance
docker-compose exec redis redis-cli --latency-history -i 1

# Test monitoring dashboard response time
ab -n 100 -c 10 http://localhost:5000/
```

## 🚨 Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose logs service_name

# Check resource usage
docker stats

# Check port conflicts
netstat -tulpn | grep :5432
```

#### Database Connection Issues

```bash
# Test connection
docker-compose exec postgres pg_isready -U postgres

# Check configuration
docker-compose exec postgres cat /var/lib/postgresql/data/postgresql.conf

# Reset database
make db-reset
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Analyze slow queries
docker-compose exec postgres psql -U postgres -d ecommerce_dw -c "SELECT * FROM pg_stat_activity;"

# Check cache hit rate
docker-compose exec redis redis-cli info stats
```

## 📞 Support

For deployment issues:

1. **Check Documentation**: Review this guide and README.md
2. **Check Logs**: Use `make logs` to view service logs
3. **Validate Configuration**: Use `make env-check` to verify setup
4. **Run Tests**: Use `make test` to validate functionality
5. **Create Issue**: Open a GitHub issue with deployment details

## 📋 Deployment Checklist

### Pre-Deployment

- [ ] Docker and Docker Compose installed
- [ ] System resources available (4GB RAM, 2GB disk)
- [ ] Network ports available (5432, 6379, 8080, 5000)
- [ ] Environment variables configured
- [ ] SSL certificates obtained (for production)
- [ ] Backup strategy planned

### Deployment

- [ ] Services started successfully
- [ ] Health checks passing
- [ ] Database accessible
- [ ] Airflow UI accessible
- [ ] Monitoring dashboard accessible
- [ ] ETL pipeline runs successfully

### Post-Deployment

- [ ] Data quality checks passing
- [ ] Performance tests completed
- [ ] Monitoring configured
- [ ] Backup scheduled
- [ ] Documentation updated
- [ ] Team trained on operations

---

**Note**: This deployment guide covers various scenarios. Choose the appropriate deployment method based on your infrastructure requirements and constraints.