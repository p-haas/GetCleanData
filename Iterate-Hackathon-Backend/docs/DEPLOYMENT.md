# Deployment Guide

This guide covers deploying the Iterate Data Quality Analysis Platform backend to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Production Checklist](#production-checklist)
7. [Monitoring & Logging](#monitoring--logging)
8. [Scaling Considerations](#scaling-considerations)

---

## Prerequisites

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB (10GB for datasets, 10GB for system)
- Python: 3.11+

**Recommended**:
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB SSD
- Python: 3.11 or 3.12

### External Dependencies

1. **MongoDB**
   - Version: 4.4+
   - Purpose: Chat history storage
   - Options: Local, Atlas (cloud), AWS DocumentDB

2. **Anthropic API**
   - API Key with Claude 4.5 Haiku access
   - Rate limits: Check your plan (Standard: 50 requests/min)

3. **(Optional) PostgreSQL**
   - Version: 14+
   - Purpose: Vector embeddings for semantic search
   - With pgvector extension

---

## Environment Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# ============================================================
# REQUIRED CONFIGURATION
# ============================================================

# Anthropic API (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# MongoDB (REQUIRED)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=iterate_chat_history
MONGODB_COLLECTION_NAME=messages

# ============================================================
# OPTIONAL CONFIGURATION
# ============================================================

# Model Selection
CLAUDE_MODEL=claude-haiku-4-5-20251001
CLAUDE_CODE_EXEC_MODEL=claude-haiku-4-5-20251001

# Agent Tuning
AGENT_TIMEOUT_SECONDS=30.0
AGENT_MAX_RETRIES=2
AGENT_MAX_DATASET_ROWS=100000
AGENT_SAMPLE_ROWS=1000
AGENT_ENABLED=true

# Server Settings
PORT=8000
HOST=0.0.0.0
WORKERS=4
LOG_LEVEL=info

# CORS (Update for your frontend)
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.com
```

### MongoDB Setup

#### Option 1: Local MongoDB
```bash
# Install MongoDB (macOS)
brew install mongodb-community@7.0

# Start service
brew services start mongodb-community@7.0

# Verify connection
mongosh mongodb://localhost:27017
```

#### Option 2: MongoDB Atlas (Cloud)
1. Create account at https://www.mongodb.com/atlas
2. Create free cluster (M0 tier)
3. Create database user
4. Whitelist your IP
5. Get connection string:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
   ```

#### Option 3: Docker MongoDB
```bash
docker run -d \
  --name iterate-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password \
  -v iterate_mongo_data:/data/db \
  mongo:7.0

MONGODB_URI=mongodb://admin:password@localhost:27017/
```

### PostgreSQL Setup (Optional)

Only needed for vector embeddings feature:

```bash
# Install PostgreSQL with pgvector
docker run -d \
  --name iterate-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -v iterate_pg_data:/var/lib/postgresql/data \
  ankane/pgvector:latest

# Add to .env
POSTGRES_URI=postgresql://postgres:password@localhost:5432/iterate
```

---

## Local Development

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd Iterate-Hackathon-Backend

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 5. Start server
uvicorn app.main:app --reload --port 8000
```

### Development Server Options

**Basic**:
```bash
uvicorn app.main:app --reload
```

**Custom Port**:
```bash
uvicorn app.main:app --reload --port 8080
```

**All Interfaces** (accessible from network):
```bash
uvicorn app.main:app --reload --host 0.0.0.0
```

**With Logs**:
```bash
uvicorn app.main:app --reload --log-level debug
```

---

## Docker Deployment

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY .env .env

# Create data directories
RUN mkdir -p /app/data /app/scripts

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - MONGODB_URI=mongodb://mongo:27017
      - MONGODB_DB_NAME=iterate_chat
      - MONGODB_COLLECTION_NAME=messages
    volumes:
      - ./data:/app/data
      - ./scripts:/app/scripts
    depends_on:
      - mongo
    restart: unless-stopped

  mongo:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped

volumes:
  mongo_data:
```

### Build and Run

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## Cloud Deployment

### AWS EC2

#### 1. Launch EC2 Instance
- Instance Type: `t3.medium` (2 vCPU, 4GB RAM)
- AMI: Ubuntu 22.04 LTS
- Storage: 50GB GP3
- Security Group: Allow ports 22 (SSH), 8000 (API)

#### 2. Install Dependencies
```bash
# SSH into instance
ssh ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Docker (for MongoDB)
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker ubuntu
```

#### 3. Deploy Application
```bash
# Clone repository
git clone <repository-url>
cd Iterate-Hackathon-Backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
nano .env  # Add your credentials

# Start MongoDB
docker run -d \
  --name mongo \
  -p 27017:27017 \
  -v mongo_data:/data/db \
  mongo:7.0

# Start application with systemd (production)
sudo nano /etc/systemd/system/iterate-backend.service
```

**Systemd Service File**:
```ini
[Unit]
Description=Iterate Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Iterate-Hackathon-Backend
Environment="PATH=/home/ubuntu/Iterate-Hackathon-Backend/venv/bin"
ExecStart=/home/ubuntu/Iterate-Hackathon-Backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start iterate-backend
sudo systemctl enable iterate-backend

# Check status
sudo systemctl status iterate-backend
```

#### 4. Set Up Nginx Reverse Proxy

```bash
# Install nginx
sudo apt install nginx -y

# Create configuration
sudo nano /etc/nginx/sites-available/iterate-backend
```

**Nginx Config**:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/iterate-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

### Azure App Service

#### 1. Create App Service
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Create resource group
az group create --name iterate-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name iterate-plan \
  --resource-group iterate-rg \
  --sku B2 \
  --is-linux

# Create web app
az webapp create \
  --name iterate-backend \
  --resource-group iterate-rg \
  --plan iterate-plan \
  --runtime "PYTHON:3.11"
```

#### 2. Configure Environment
```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group iterate-rg \
  --name iterate-backend \
  --settings \
    ANTHROPIC_API_KEY="sk-ant-xxx" \
    MONGODB_URI="mongodb+srv://..." \
    CLAUDE_MODEL="claude-haiku-4-5-20251001"
```

#### 3. Deploy Application
```bash
# Deploy from local Git
az webapp deployment source config-local-git \
  --name iterate-backend \
  --resource-group iterate-rg

# Push code
git remote add azure <deployment-url>
git push azure main
```

### Google Cloud Run

#### 1. Build Container
```bash
# Install gcloud CLI
# See: https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set project
gcloud config set project your-project-id

# Build image
gcloud builds submit --tag gcr.io/your-project-id/iterate-backend
```

#### 2. Deploy to Cloud Run
```bash
gcloud run deploy iterate-backend \
  --image gcr.io/your-project-id/iterate-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-xxx,MONGODB_URI=mongodb+srv://...
```

---

## Production Checklist

### Security

- [ ] **API Key Protection**
  - Store `ANTHROPIC_API_KEY` in environment, never in code
  - Use secret management (AWS Secrets Manager, Azure Key Vault)
  
- [ ] **CORS Configuration**
  - Update `ALLOWED_ORIGINS` to only include your frontend domain
  - Remove `http://localhost` from production
  
- [ ] **Rate Limiting**
  - Implement at reverse proxy level (nginx, Cloudflare)
  - Suggested limits:
    - Upload: 10 requests/hour per IP
    - Analysis: 5 requests/hour per dataset
    - Chat: 60 requests/minute per session
  
- [ ] **Input Validation**
  - File size limits enforced
  - File type validation (CSV/Excel only)
  - Sanitize user inputs
  
- [ ] **HTTPS Only**
  - Enable SSL/TLS certificate
  - Redirect HTTP to HTTPS
  - Set `Secure` flag on cookies (if using)

### Performance

- [ ] **Database Optimization**
  - MongoDB indexes on `session_id`, `timestamp`
  - Connection pooling configured
  - Regular backups scheduled
  
- [ ] **Caching**
  - Redis for dataset metadata
  - Cache dataset understanding results
  - Cache analysis results (keyed by user_instructions hash)
  
- [ ] **File Storage**
  - Use object storage (S3, Azure Blob) for large datasets
  - Implement cleanup policy (delete after 30 days)
  
- [ ] **Workers**
  - Set `--workers` based on CPU count (2x cores)
  - Use `--worker-class uvicorn.workers.UvicornWorker` for Gunicorn

### Monitoring

- [ ] **Logging**
  - Centralized logging (CloudWatch, Stackdriver)
  - Log levels: INFO in production, DEBUG in staging
  - Structured JSON logs
  
- [ ] **Metrics**
  - API response times
  - Agent call success/failure rates
  - Dataset upload sizes
  - Error rates by endpoint
  
- [ ] **Alerting**
  - Alert on error rate >5%
  - Alert on agent timeout rate >10%
  - Alert on disk usage >80%
  
- [ ] **Health Checks**
  - Implement `/health` endpoint
  - Check MongoDB connectivity
  - Check Anthropic API connectivity

### Reliability

- [ ] **Backups**
  - Daily MongoDB backups
  - Dataset files backup to S3/Azure Blob
  - 30-day retention policy
  
- [ ] **Disaster Recovery**
  - Document restore procedures
  - Test backups monthly
  - RTO: 4 hours, RPO: 24 hours
  
- [ ] **High Availability**
  - Multi-instance deployment (load balanced)
  - MongoDB replica set (3 nodes)
  - Auto-scaling based on CPU/memory

---

## Monitoring & Logging

### Application Logging

**Configure logging** in `app/main.py`:

```python
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/iterate/app.log')
    ]
)

# Agent-specific logging
logger = logging.getLogger("iterate")
logger.setLevel(logging.INFO)
```

### Structured Logging (JSON)

```python
import json
import logging

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
```

### Health Check Endpoint

Add to `app/main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    
    # Check MongoDB
    try:
        from .db import get_mongo_client
        client = get_mongo_client()
        client.admin.command('ping')
        mongo_status = "healthy"
    except Exception as e:
        mongo_status = f"unhealthy: {e}"
    
    # Check Anthropic API
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        # Quick ping (no actual call to save costs)
        anthropic_status = "healthy"
    except Exception as e:
        anthropic_status = f"unhealthy: {e}"
    
    status = {
        "status": "healthy" if mongo_status == "healthy" else "degraded",
        "mongodb": mongo_status,
        "anthropic": anthropic_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return status
```

### Prometheus Metrics (Optional)

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

Access metrics at `http://localhost:8000/metrics`

---

## Scaling Considerations

### Vertical Scaling

**When to scale up**:
- CPU usage consistently >70%
- Memory usage >80%
- Response times >2 seconds

**Instance sizes**:
- Small (10-50 users): 2 vCPU, 4GB RAM
- Medium (50-200 users): 4 vCPU, 8GB RAM
- Large (200-500 users): 8 vCPU, 16GB RAM

### Horizontal Scaling

**Load Balancing**:
```nginx
upstream backend {
    server backend1.example.com:8000;
    server backend2.example.com:8000;
    server backend3.example.com:8000;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

**Sticky Sessions** (for chat):
```nginx
upstream backend {
    ip_hash;  # Route same IP to same server
    server backend1:8000;
    server backend2:8000;
}
```

### Database Scaling

**MongoDB Sharding**:
- Shard by `session_id` for chat history
- Shard by `dataset_id` for analysis results
- Use MongoDB Atlas auto-sharding

**Read Replicas**:
- Primary for writes
- Replicas for read-heavy queries

---

## Troubleshooting

### Common Issues

**1. Agent Timeouts**
```
Error: Agent call timed out after 30 seconds
```

**Solution**:
- Increase `AGENT_TIMEOUT_SECONDS` in .env
- Check Anthropic API status
- Reduce `AGENT_SAMPLE_ROWS` for faster code execution

**2. MongoDB Connection Errors**
```
Error: Connection refused to MongoDB
```

**Solution**:
- Verify MongoDB is running: `docker ps` or `brew services list`
- Check `MONGODB_URI` in .env
- Ensure network connectivity

**3. Out of Memory**
```
Error: Process killed (OOM)
```

**Solution**:
- Reduce `AGENT_SAMPLE_ROWS`
- Increase instance RAM
- Implement pagination for large datasets

**4. File Upload Failures**
```
Error: File too large
```

**Solution**:
- Increase nginx `client_max_body_size`
- Adjust FastAPI `File` size limit
- Use streaming uploads for large files

---

## Rollback Procedure

If deployment fails:

```bash
# Docker deployment
docker-compose down
docker-compose up -d --build  # Rebuild from previous commit

# Systemd deployment
sudo systemctl stop iterate-backend
cd /home/ubuntu/Iterate-Hackathon-Backend
git checkout <previous-commit>
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start iterate-backend
```

---

**Deployment Guide Version**: 1.0  
**Last Updated**: 2025-11-16  
**Maintainer**: Backend Team
