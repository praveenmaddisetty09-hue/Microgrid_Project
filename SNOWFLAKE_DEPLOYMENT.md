# Snowflake Deployment Guide - Step by Step

## Overview

This guide provides a complete step-by-step process to deploy your Smart Microgrid Manager Pro application with Snowflake data warehouse integration.

---

## Prerequisites

Before starting, ensure you have:

- [ ] **Snowflake Account** (Trial or Production)
- [ ] **Python 3.11+** installed locally
- [ ] **Git** installed
- [ ] **Docker & Docker Compose** (for containerized deployment)
- [ ] **AWS/GCP/Azure account** (optional, for cloud deployment)

---

## Step 1: Create Snowflake Account & Warehouse

### 1.1 Sign Up for Snowflake

1. Go to [https://signup.snowflake.com/](https://signup.snowflake.com/)
2. Fill in your details:
   - **Account Name**: Choose a unique name (e.g., `xy12345` - Snowflake's format)
   - **Email**: Business email recommended
   - **Password**: Strong password
3. Verify your email and log in to Snowflake UI

### 1.2 Create a Virtual Warehouse

In Snowflake's Worksheets tab, run:

```sql
-- Create a warehouse for your app
CREATE WAREHOUSE IF NOT EXISTS MICROGRID_WH 
WITH WAREHOUSE_SIZE = 'X-SMALL' 
AUTO_SUSPEND = 300 
AUTO_RESUME = TRUE;

-- Create a dedicated database
CREATE DATABASE IF NOT EXISTS MICROGRID_DB;

-- Create a schema
CREATE SCHEMA IF NOT EXISTS MICROGRID_DB.PUBLIC;

-- Grant access to your user (replace with your username)
GRANT ALL PRIVILEGES ON DATABASE MICROGRID_DB TO YOUR_USERNAME;
GRANT ALL PRIVILEGES ON SCHEMA MICROGRID_DB.PUBLIC TO YOUR_USERNAME;
GRANT ALL PRIVILEGES ON WAREHOUSE MICROGRID_WH TO YOUR_USERNAME;
```

---

## Step 2: Configure Environment Variables

### 2.1 Create Environment File

Create a `.env` file in your project root:

```env
# Snowflake Configuration (REQUIRED)
SNOWFLAKE_ACCOUNT=your_account_identifier  # e.g., xy12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=MICROGRID_WH
SNOWFLAKE_DATABASE=MICROGRID_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=ACCOUNTADMIN  # Optional: specify role if needed

# Application Settings
SECRET_KEY=your-super-secret-key-min-32-chars

# Weather API (Optional)
OPENWEATHERMAP_API_KEY=your_api_key

# Session Settings
SESSION_TIMEOUT_MINUTES=30
```

### 2.2 Get Your Account Identifier

1. Log in to Snowflake
2. Click on your username in top-right corner
3. Go to **Account** → **Account Identifier**
4. Format: `xxxxxxx.region.cloudprovider` (e.g., `xy12345.us-east-1.aws`)

---

## Step 3: Install Dependencies

### 3.1 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install Snowflake-specific dependencies
pip install snowflake-connector-python>=3.0.0
pip install snowflake-snowpark-python>=1.0.0

# Install all project dependencies
pip install -r requirements.txt
```

### 3.2 Verify Installation

```bash
python -c "import snowflake.connector; print('✅ Snowflake connector installed!')"
python -c "import snowflake.snowpark; print('✅ Snowpark installed!')"
```

---

## Step 4: Test Snowflake Connection Locally

### 4.1 Create Test Script

```python
# test_snowflake_connection.py
import os
from snowflake_db import SnowflakeMicrogridDB, SnowflakeConfig

def test_connection():
    print("🧪 Testing Snowflake Connection...")
    
    # Method 1: From environment variables
    try:
        config = SnowflakeConfig.from_env()
        db = SnowflakeMicrogridDB(config)
        
        if db.connected:
            print("✅ Successfully connected to Snowflake!")
            
            # Initialize schema
            print("📦 Creating schema...")
            db.initialize_schema()
            print("✅ Schema created!")
            
            # Get dashboard summary
            summary = db.get_dashboard_summary(hub_id=1)
            print(f"📊 Dashboard Summary: {summary}")
            
            db.close()
            return True
        else:
            print("❌ Connection failed - check environment variables")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

### 4.2 Run Test

```bash
python test_snowflake_connection.py
```

Expected output:
```
🧪 Testing Snowflake Connection...
✅ Successfully connected to Snowflake!
📦 Creating schema...
✅ Schema created!
📊 Dashboard Summary: {...}
```

---

## Step 5: Initialize Snowflake Schema

### 5.1 Run Schema Initialization

```bash
# The schema is automatically created when connecting
# Or manually run:
python -c "
from snowflake_db import get_snowflake_db
db = get_snowflake_db()
db.initialize_schema()
db.populate_time_dimension()  # Populate time dimension
print('✅ Schema initialized!')
"
```

### 5.2 Verify Tables Created

In Snowflake UI, run:

```sql
-- List all tables
SHOW TABLES IN SCHEMA MICROGRID_DB.PUBLIC;

-- Check dimension tables
SELECT * FROM DIM_HUBS;
SELECT * FROM DIM_ENERGY_SOURCES;
SELECT * FROM DIM_TIME LIMIT 10;

-- Verify views
SHOW VIEWS IN SCHEMA MICROGRID_DB.PUBLIC;
```

---

## Step 6: Deploy with Docker

### 6.1 Update Dockerfile for Snowflake

Your existing `Dockerfile` already includes all necessary dependencies. No changes needed!

### 6.2 Create Production Docker Compose

```yaml
# docker-compose.snowflake.yml
version: '3.8'

services:
  microgrid-app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: microgrid-snowflake
    ports:
      - "8501:8501"
    environment:
      - TZ=UTC
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
      
      # Snowflake Environment Variables
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
      - SNOWFLAKE_PASSWORD=${SNOWFLAKE_PASSWORD}
      - SNOWFLAKE_WAREHOUSE=${SNOWFLAKE_WAREHOUSE}
      - SNOWFLAKE_DATABASE=${SNOWFLAKE_DATABASE}
      - SNOWFLAKE_SCHEMA=${SNOWFLAKE_SCHEMA}
      - SNOWFLAKE_ROLE=${SNOWFLAKE_ROLE}
      
      # Application Settings
      - SECRET_KEY=${SECRET_KEY}
      - SESSION_TIMEOUT_MINUTES=30
    volumes:
      - ./models:/app/models
      - ./users.json:/app/users.json
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - microgrid-network

  nginx:
    image: nginx:alpine
    container_name: microgrid-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - microgrid-app
    restart: unless-stopped
    networks:
      - microgrid-network

networks:
  microgrid-network:
    driver: bridge
```

### 6.3 Build and Run

```bash
# Build the image
docker-compose -f docker-compose.snowflake.yml build

# Run the container
docker-compose -f docker-compose.snowflake.yml up -d

# Check logs
docker-compose -f docker-compose.snowflake.yml logs -f
```

### 6.4 Access Application

Open browser to: `http://localhost:8501`

---

## Step 7: Deploy to Cloud Platforms

### Option A: AWS ECS with Fargate

```bash
# 1. Install AWS CLI
brew install awscli

# 2. Configure credentials
aws configure

# 3. Create ECR repository
aws ecr create-repository --repository-name microgrid-manager

# 4. Build and push image
docker build -t microgrid-manager .
docker tag microgrid-manager:latest YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/microgrid-manager:latest
aws ecr get-login-password | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.REGION.amazonaws.com
docker push YOUR_AWS_ACCOUNT.dkr.ecr.REGION.amazonaws.com/microgrid-manager:latest

# 5. Create ECS cluster and service
# (Use AWS Console or Terraform)
```

### Option B: Google Cloud Run

```bash
# 1. Install gcloud CLI
brew install google-cloud-sdk

# 2. Configure project
gcloud init
gcloud auth configure-docker

# 3. Build and deploy
gcloud run deploy microgrid-manager \
  --image gcr.io/PROJECT_ID/microgrid-manager \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SNOWFLAKE_ACCOUNT=xxx,SNOWFLAKE_USER=xxx
```

### Option C: Azure Container Instances

```bash
# 1. Install Azure CLI
brew install azure-cli

# 2. Login
az login

# 3. Create container instance
az container create \
  --resource-group myResourceGroup \
  --name microgrid-container \
  --image myregistry.azurecr.io/microgrid-manager:latest \
  --dns-name-label microgrid-manager \
  --ports 8501 \
  --environment-variables \
    SNOWFLAKE_ACCOUNT=xxx \
    SNOWFLAKE_USER=xxx \
    SNOWFLAKE_PASSWORD=xxx
```

---

## Step 8: Configure CI/CD with GitHub Actions

### 8.1 Update GitHub Workflow

Create `.github/workflows/snowflake-deploy.yml`:

```yaml
name: Snowflake Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Test Snowflake Connection
        env:
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
          SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
          SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
          SNOWFLAKE_DATABASE: ${{ secrets.SNOWFLAKE_DATABASE }}
        run: |
          python -c "
          from snowflake_db import SnowflakeConfig, SnowflakeMicrogridDB
          config = SnowflakeConfig.from_env()
          db = SnowflakeMicrogridDB(config)
          print('✅ Snowflake connected:', db.connected)
          "
      
      - name: Build and Push Docker Image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
      
      - name: Deploy to Cloud Run
        if: github.ref == 'refs/heads/main'
        run: |
          gcloud run deploy microgrid-manager \
            --image ghcr.io/${{ github.repository }}:${{ github.sha }} \
            --region us-central1 \
            --platform managed \
            --set-env-vars SNOWFLAKE_ACCOUNT=${{ secrets.SNOWFLAKE_ACCOUNT }},SNOWFLAKE_USER=${{ secrets.SNOWFLAKE_USER }}
```

### 8.2 Add GitHub Secrets

In GitHub repository settings, add these secrets:

| Secret Name | Value |
|-------------|-------|
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account ID |
| `SNOWFLAKE_USER` | Your Snowflake username |
| `SNOWFLAKE_PASSWORD` | Your Snowflake password |
| `SNOWFLAKE_WAREHOUSE` | MICROGRID_WH |
| `SNOWFLAKE_DATABASE` | MICROGRID_DB |

---

## Step 9: Production Checklist

### 9.1 Snowflake Security

```sql
-- Create dedicated user for application
CREATE USER MICROGRID_APP_USER 
  PASSWORD = 'StrongPassword123!' 
  DEFAULT_WAREHOUSE = MICROGRID_WH 
  DEFAULT_NAMESPACE = MICROGRID_DB.PUBLIC;

-- Grant minimal required privileges
GRANT USAGE ON DATABASE MICROGRID_DB TO MICROGRID_APP_USER;
GRANT USAGE ON SCHEMA MICROGRID_DB.PUBLIC TO MICROGRID_APP_USER;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA MICROGRID_DB.PUBLIC TO MICROGRID_APP_USER;

-- Enable MFA for production users
ALTER USER YOUR_USERNAME SET MFA_AUTHENTICATION = TRUE;
```

### 9.2 Network Security

1. **Configure Snowflake Network Policy**:
```sql
CREATE NETWORK POLICY ALLOW_APP_SERVERS
  ALLOWED_IP_LIST = ('YOUR_SERVER_IP/32');

ALTER DATABASE MICROGRID_DB SET NETWORK_POLICY = ALLOW_APP_SERVERS;
```

2. **Use Private Connectivity** (AWS PrivateLink / Azure Private Link)

### 9.3 Data Encryption

```sql
-- Enable encryption at rest (default in Snowflake)
-- Verify encryption status
SHOW DATABASES;

-- Use customer-managed keys for enhanced security
ALTER DATABASE MICROGRID_DB SET ENABLE_READ_COMMITTED_ISOLATION = TRUE;
```

---

## Step 10: Monitoring & Maintenance

### 10.1 Create Monitoring Views

```sql
-- Usage monitoring view
CREATE OR REPLACE VIEW V_USAGE_METRICS AS
SELECT 
  WAREHOUSE_NAME,
  START_TIME,
  END_TIME,
  CREDITS_USED,
  EXECUTION_TIME_SECONDS
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE START_TIME >= DATEADD(DAY, -30, CURRENT_TIMESTAMP());

-- Query performance view
CREATE OR REPLACE VIEW V_QUERY_PERFORMANCE AS
SELECT 
  QUERY_TEXT,
  EXECUTION_TIME,
  TOTAL_ELAPSED_TIME,
  ROWS_PRODUCED,
  START_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME >= DATEADD(HOUR, -24, CURRENT_TIMESTAMP())
ORDER BY EXECUTION_TIME DESC
LIMIT 100;
```

### 10.2 Set Up Alerts

```sql
-- Create alert for unusual activity
CREATE ALERT IF NOT EXISTS ALERT_UNUSUAL_COST
  WAREHOUSE = MICROGRID_WH
  SCHEDULE = '1 HOUR'
  IF (
    SELECT COUNT(*) > 100 
    FROM V_USAGE_METRICS 
    WHERE CREDITS_USED > 10
  ) THEN
    SYSTEM$SEND_EMAIL(
      'alert@yourcompany.com',
      'Unusual Snowflake Cost Detected',
      'Check Snowflake usage - credits exceed threshold'
    );
```

---

## Troubleshooting

### Common Issues

#### 1. "Account identifier not found"
```
✅ Fix: Ensure SNOWFLAKE_ACCOUNT format is correct (e.g., xy12345.us-east-1.aws)
```

#### 2. "Authentication failed"
```
✅ Fix: 
   - Verify username/password
   - Check if SSO is enabled (use authenticator='externalbrowser')
   - Ensure user has proper grants
```

#### 3. "Warehouse not found"
```
✅ Fix: 
   - Verify WAREHOUSE name exists
   - Ensure user has USAGE privilege on warehouse
```

#### 4. "Connection timeout"
```
✅ Fix:
   - Check firewall rules
   - Verify network policy allows your IP
   - Try using private connectivity
```

### Debug Commands

```bash
# Test connection manually
python -c "
import snowflake.connector
conn = snowflake.connector.connect(
    account='your_account',
    user='your_user',
    password='your_password',
    warehouse='MICROGRID_WH',
    database='MICROGRID_DB',
    schema='PUBLIC'
)
print('✅ Connected!')
print('Tables:', conn.cursor().execute('SHOW TABLES').fetchall())
conn.close()
"

# Check logs
docker logs microgrid-snowflake
```

---

## Cost Optimization Tips

| Optimization | Action |
|--------------|--------|
| Auto-suspend | Set `AUTO_SUSPEND = 300` (5 min idle) |
| Right-size | Start with `X-SMALL`, scale as needed |
| Cache results | Use Snowflake's result cache |
| Partition data | Use clustering keys on large tables |
| Use views | Minimize data duplication |

---

## Quick Reference Commands

```bash
# Local testing
python snowflake_db.py

# Docker deployment
docker-compose -f docker-compose.snowflake.yml up -d

# Check connection
python -c "from snowflake_db import get_snowflake_db; db = get_snowflake_db(); print('✅ Connected' if db.connected else '❌ Failed')"

# View logs
docker logs microgrid-snowflake -f

# Stop services
docker-compose -f docker-compose.snowflake.yml down

# Update schema
python -c "from snowflake_db import get_snowflake_db; db = get_snowflake_db(); db.initialize_schema()"
```

---

## Support Resources

- [Snowflake Documentation](https://docs.snowflake.com)
- [Snowflake Connector Python](https://docs.snowflake.com/en/user-guide/python-connector)
- [Snowpark Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud)
- [Docker Documentation](https://docs.docker.com)

---

**🎉 Congratulations! Your Smart Microgrid Manager Pro is now deployed with Snowflake!**

