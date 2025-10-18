# 🚀 Gawa Backend - Setup & Deployment Guide

Complete guide to setup, test, and deploy the Gawa backend.

---

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL (production) or SQLite (development)
- Supabase account
- PayHero API credentials
- Git
- Virtual environment (venv)

---

## 🎯 Quick Start (5 minutes)

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/Gawa.git
cd Gawa
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
DEBUG=True
SECRET_KEY=your-secret-key

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-key
SUPABASE_JWT_SECRET=your-jwt-secret

PAYHERO_API_KEY=your-payhero-key
```

### 3. Initialize Database

```bash
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Access API at `http://localhost:8000/api/`
Access admin at `http://localhost:8000/admin/`

---

## 🔧 Configuration

### Supabase Setup

1. **Create Supabase Project:**
   - Go to https://supabase.com
   - Create new project
   - Note project URL and keys

2. **Create Tables (if using Supabase Database):**
   ```sql
   -- Run migrations in Supabase SQL editor
   python manage.py migrate  -- This creates tables
   ```

3. **Get JWT Secret:**
   - Go to Project Settings → API
   - Copy `JWT Secret`

### PayHero Setup

1. **Get API Key:**
   - Register on PayHero dashboard
   - Generate API key in settings
   - Note merchant code and email

2. **Configure Webhook:**
   - Add webhook URL: `https://your-domain.com/api/payhero/webhook/`
   - This receives payment callbacks

### CORS Configuration

Update `.env` for frontend URLs:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## 📱 API Testing

### Using cURL

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "phone_number": "+254712345678"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Create Group (with token from login)
curl -X POST http://localhost:8000/api/groups/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Trip",
    "description": "Beach trip"
  }'
```

### Using Postman

1. Import the Gawa API collection (see `API_COLLECTION.json`)
2. Set environment variables:
   - `BASE_URL`: http://localhost:8000
   - `ACCESS_TOKEN`: Your bearer token
3. Run requests

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Register
response = requests.post(f"{BASE_URL}/auth/register/", json={
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "phone_number": "+254712345678"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/auth/login/", json={
    "email": "test@example.com",
    "password": "password123"
})
token = response.json()['access_token']

# Create Group
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(f"{BASE_URL}/groups/", 
    headers=headers,
    json={"title": "Trip", "description": "Beach trip"}
)
print(response.json())
```

---

## ✅ Running Tests

```bash
# Run all tests
python manage.py test api

# Run specific test class
python manage.py test api.tests.UserModelTests

# Run specific test
python manage.py test api.tests.UserModelTests.test_user_creation

# With verbose output
python manage.py test api -v 2

# With coverage report
pip install coverage
coverage run --source='api' manage.py test api
coverage report
```

---

## 🐳 Docker Deployment

### Build Docker Image

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "gawa_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Build & Run

```bash
docker build -t gawa-backend .
docker run -p 8000:8000 --env-file .env gawa-backend
```

---

## 🚀 Production Deployment

### Option 1: Render

1. **Push to GitHub**

2. **Create on Render:**
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repo
   - Set:
     - Build Command: `pip install -r requirements.txt && python manage.py migrate`
     - Start Command: `gunicorn gawa_backend.wsgi`
     - Environment: Add from `.env`

3. **Set Up Database:**
   - Use Supabase PostgreSQL or Render PostgreSQL

### Option 2: Railway

1. **Deploy:**
   - Connect GitHub repo to Railway
   - Set environment variables
   - Auto-deploys on push

### Option 3: PythonAnywhere

1. **Upload code**
2. **Configure virtual environment**
3. **Set WSGI file**
4. **Update environment variables**

### Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` correctly
- [ ] Use HTTPS only
- [ ] Enable CSRF protection
- [ ] Use environment variables for secrets
- [ ] Configure CORS properly
- [ ] Set up logging
- [ ] Enable rate limiting

---

## 📊 Database Migration

### From SQLite to PostgreSQL

```bash
# Export data from SQLite
python manage.py dumpdata > dump.json

# Update settings.py to use PostgreSQL
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'gawa_db',
#         'USER': 'your_user',
#         'PASSWORD': 'your_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Create fresh database
python manage.py migrate

# Load data
python manage.py loaddata dump.json
```

---

## 🔍 Monitoring & Logging

### Configure Logging

The app logs to:
- Console (development)
- File: `logs/django.log` (production)

Check logs:

```bash
tail -f logs/django.log
```

### Health Check Endpoint (Optional)

Add to `api/urls.py`:

```python
@api_view(['GET'])
def health(request):
    return Response({'status': 'healthy'})

# In urlpatterns:
path('health/', health, name='health'),
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: ModuleNotFoundError: No module named 'api'**
```bash
# Ensure api is in INSTALLED_APPS in settings.py
```

**Issue: Supabase connection fails**
```bash
# Verify SUPABASE_URL and SUPABASE_KEY in .env
# Check firewall/network settings
```

**Issue: PayHero STK not sending**
```bash
# Verify PAYHERO_API_KEY
# Check phone number format
# Ensure merchant account is active
```

**Issue: CORS errors**
```bash
# Add frontend URL to CORS_ALLOWED_ORIGINS in .env
```

### Debug Mode

```bash
# Enable Django debug toolbar
pip install django-debug-toolbar

# Add to settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

---

## 📈 Performance Optimization

### Database Indexing

```python
# In models.py, add indexes
class Expense(models.Model):
    # ...
    class Meta:
        indexes = [
            models.Index(fields=['group', '-date_created']),
        ]
```

### Caching

```bash
pip install django-redis
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Query Optimization

Use `select_related()` and `prefetch_related()`:

```python
# In views.py
groups = Group.objects.select_related('created_by').prefetch_related('members')
```

---

## 🔐 Security

### API Key Management

Store sensitive keys in environment variables, never in code:

```python
# ✅ Good
api_key = os.getenv('PAYHERO_API_KEY')

# ❌ Bad
api_key = 'your-api-key-here'
```

### HTTPS

Always use HTTPS in production:

```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Rate Limiting

```bash
pip install djangorestframework-throttling
```

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    }
}
```

---

## 📝 Maintenance

### Regular Tasks

- [ ] Monitor error logs
- [ ] Update dependencies: `pip list --outdated`
- [ ] Backup database regularly
- [ ] Review credit score calculations
- [ ] Check payment statuses

### Backup Database

```bash
# SQLite
cp db.sqlite3 db.sqlite3.backup

# PostgreSQL
pg_dump gawa_db > backup.sql
```

---

## 📞 Support

For issues:
1. Check logs
2. Review traceback
3. Check `.env` configuration
4. Verify API credentials
5. Check firewall/network

---

**Happy coding! 🎉**
