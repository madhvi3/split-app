# Deployment Guide

This guide walks you through deploying the Expense Splitter Backend to Railway (recommended) or Render.

## 🚂 Railway Deployment (Recommended)

Railway offers the easiest deployment with automatic PostgreSQL database setup.

### Prerequisites
- GitHub account
- Railway account (free tier available)

### Step 1: Prepare Repository
```bash
# 1. Initialize git repository
git init
git add .
git commit -m "Initial commit: Expense Splitter Backend"

# 2. Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/expense-splitter-backend.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Railway
1. Visit [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your expense-splitter-backend repository
6. Railway will automatically:
   - Detect it's a Python app
   - Install dependencies from requirements.txt
   - Start the app with `python app.py`

### Step 3: Add PostgreSQL Database
1. In your Railway project dashboard
2. Click "New" → "Database" → "Add PostgreSQL"
3. Railway will automatically set the `DATABASE_URL` environment variable

### Step 4: Configure Environment Variables
In Railway dashboard → Your service → Variables:
- `DATABASE_URL`: (Auto-set by Railway PostgreSQL)
- `PORT`: 5000 (if not auto-detected)

### Step 5: Deploy and Test
1. Railway will automatically deploy
2. You'll get a public URL like: `https://your-app-name.railway.app`
3. Test the API endpoints and web dashboard

---

## 🎨 Render Deployment (Alternative)

### Step 1: Prepare Repository
Same as Railway Step 1 above.

### Step 2: Create Render Account
1. Visit [render.com](https://render.com)
2. Sign up with GitHub

### Step 3: Create PostgreSQL Database
1. In Render dashboard → "New" → "PostgreSQL"
2. Name: `expense-splitter-db`
3. Note down the connection details

### Step 4: Create Web Service
1. In Render dashboard → "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: expense-splitter-backend
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

### Step 5: Set Environment Variables
In Render service → Environment:
```
DATABASE_URL=postgresql://username:password@hostname:port/database
PORT=5000
```

---

## 🐳 Docker Deployment (Advanced)

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/expensesplitter
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=expensesplitter
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Deploy with: `docker-compose up -d`

---

## ✅ Post-Deployment Checklist

### 1. Test All Endpoints
Visit your deployed URL and test:
- [ ] Web dashboard loads: `GET /`
- [ ] API endpoints work: `GET /expenses`
- [ ] Add expense via web form
- [ ] Settlement calculations: `GET /settlements`
- [ ] Custom splits functionality

### 2. Performance Check
- [ ] Response times < 2 seconds
- [ ] Database connections working
- [ ] No memory leaks under load

### 3. Data Validation
- [ ] Sample data loads correctly
- [ ] Settlement calculations are accurate
- [ ] Custom splits work as expected

---

## 🔧 Troubleshooting

### Common Issues

**App doesn't start:**
```bash
# Check logs in Railway/Render dashboard
# Common issues:
# 1. Missing DATABASE_URL
# 2. Port not set correctly
# 3. Dependencies not installed
```

**Database connection errors:**
```bash
# Verify DATABASE_URL format:
# postgresql://username:password@hostname:port/database

# Test connection manually:
python -c "import os; from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print('Connected successfully!')"
```

**Sample data not loading:**
```bash
# Manually reset sample data via API:
curl -X POST https://your-app.railway.app/admin/reset-sample-data
```

### Performance Optimization

**For production use:**
1. Set `debug=False` in app.py
2. Use gunicorn: `gunicorn app:app`
3. Add error monitoring (Sentry)
4. Implement rate limiting
5. Add caching for analytics endpoints

### Security Considerations

**For production:**
1. Add authentication/authorization
2. Validate all inputs
3. Use HTTPS only
4. Implement CORS properly
5. Add request rate limiting
6. Sanitize database queries

---

## 📊 Monitoring

### Health Check Endpoint
Add to app.py:
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

### Logging
Add proper logging for production:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Analytics
Monitor key metrics:
- Response times
- Error rates
- Database query performance
- User activity patterns

---

## 🚀 Next Steps

After successful deployment:
1. Create comprehensive Postman collection
2. Share public demo URL
3. Document all API endpoints
4. Add monitoring and alerts
5. Plan for scaling and performance optimization