# Smart Microgrid Manager Pro - Deployment Guide

## 🚀 Quick Deployment Options

### Option 1: Streamlit Community Cloud (Free & Recommended)

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Smart Microgrid Manager Pro"
   git remote add origin https://github.com/YOUR_USERNAME/smart-microgrid-manager.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Community Cloud**
   - Go to https://share.streamlit.io
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository and branch
   - Set the main file path as `app.py`
   - Click "Deploy!"

### Option 2: Heroku

1. **Install Heroku CLI** and login
   ```bash
   brew install heroku/brew/heroku  # macOS
   heroku login
   ```

2. **Create and deploy**
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

3. **Open your app**
   ```bash
   heroku open
   ```

### Option 3: Docker Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8501
   
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and run**
   ```bash
   docker build -t microgrid-manager .
   docker run -p 8501:8501 microgrid-manager
   ```

### Option 4: AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   eb init
   ```

2. **Deploy**
   ```bash
   eb create microgrid-env
   eb open
   ```

### Option 5: Google Cloud Run

1. **Deploy using Cloud Run**
   ```bash
   gcloud run deploy microgrid-manager --source .
   ```

---

## 📋 Pre-deployment Checklist

- [ ] Update `requirements.txt` with all dependencies
- [ ] Test the app locally: `streamlit run app.py`
- [ ] Set proper session secret keys in environment variables
- [ ] Configure database backup strategy (SQLite → PostgreSQL for production)
- [ ] Set up SSL/HTTPS certificate

## 🔧 Environment Variables

Create a `.env` file for production:

```env
# Authentication
SECRET_KEY=your-super-secret-key-here

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/microgrid

# Weather API (optional)
OPENWEATHERMAP_API_KEY=your-api-key

# Session Settings
SESSION_TIMEOUT_MINUTES=30
```

## 🐳 Docker Compose (for local production)

```yaml
version: '3.8'

services:
  microgrid-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SECRET_KEY=your-secret-key
    volumes:
      - .:/app
    restart: unless-stopped
```

## 📊 Production Database Setup

For production, replace SQLite with PostgreSQL:

1. **Install PostgreSQL adapter**
   ```bash
   pip install psycopg2-binary
   ```

2. **Update database.py** to use PostgreSQL connection string

3. **Run migrations**
   ```bash
   heroku pg:psql
   ```

---

## 🔒 Security Considerations

- **Change default passwords** for admin/user accounts
- **Enable HTTPS** on your deployment platform
- **Set up authentication** middleware
- **Regular security updates** for dependencies
- **Database encryption** at rest

## 📈 Monitoring & Logging

- Enable application logging
- Set up error tracking (Sentry)
- Monitor performance metrics

---

## 💰 Cost Estimates

| Platform | Free Tier | Paid Tier |
|----------|-----------|-----------|
| Streamlit Cloud | ✅ Free | N/A |
| Heroku | 550 hrs/month | $7+/month |
| AWS | 750 hrs/month | $5+/month |
| Google Cloud | Free tier available | $6+/month |

---

## 🆘 Troubleshooting

### App won't start
```bash
# Check logs
streamlit run app.py 2>&1 | head -50
```

### Missing dependencies
```bash
pip install -r requirements.txt
```

### Port already in use
```bash
lsof -i :8501
kill -9 <PID>
```

---

## 📞 Support

For deployment issues, refer to:
- [Streamlit Documentation](https://docs.streamlit.io)
- [Heroku Dev Center](https://devcenter.heroku.com)
- [Docker Documentation](https://docs.docker.com)

