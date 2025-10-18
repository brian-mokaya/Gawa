# 📁 Gawa Backend - Project Structure

Complete overview of the Django project structure and file organization.

---

## 🏗️ Directory Layout

```
Gawa/
├── gawa_backend/              # Django project settings
│   ├── __init__.py
│   ├── asgi.py               # ASGI configuration
│   ├── settings.py           # Django settings (environment configured)
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI configuration
│
├── api/                       # Django REST API app
│   ├── migrations/           # Database migrations
│   ├── management/
│   │   └── commands/         # Custom management commands
│   ├── __init__.py
│   ├── admin.py             # Django admin configuration
│   ├── apps.py              # App configuration
│   ├── auth.py              # Supabase JWT authentication
│   ├── models.py            # Database models
│   ├── serializers.py       # DRF serializers
│   ├── urls.py              # API URL routing
│   ├── views.py             # API views/viewsets
│   ├── tests.py             # Unit and integration tests
│   ├── supabase_service.py  # Supabase integration
│   └── payhero_service.py   # PayHero payment integration
│
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── db.sqlite3               # SQLite database (dev only)
├── logs/                    # Application logs
├── README.md                # Project documentation
├── SETUP.md                 # Setup and deployment guide
├── PROJECT_STRUCTURE.md     # This file
└── venv/                    # Virtual environment
```

---

## 📋 Core Files & Their Purposes

### Project Settings (`gawa_backend/`)

| File | Purpose |
|------|---------|
| `settings.py` | Django configuration, installed apps, middleware, database, authentication |
| `urls.py` | Main URL router, includes API app URLs |
| `wsgi.py` | WSGI application for deployment |
| `asgi.py` | ASGI application for async/WebSocket support |

### API App (`api/`)

#### Models (`models.py`)
Defines database tables:
- `User` - User profile with credit score
- `Group` - Expense sharing groups
- `GroupMember` - Many-to-many relationship
- `Expense` - Shared expenses
- `ExpenseParticipant` - Individual expense shares
- `Payment` - Payment transactions
- `Balance` - "Who owes who" tracking
- `SmartSplitSuggestion` - AI split suggestions

#### Serializers (`serializers.py`)
DRF serializers for:
- User data (profile, detailed)
- Groups and members
- Expenses and participants
- Payments and balances
- Input validation (CreateExpense, etc.)

#### Views (`views.py`)
API endpoints:
- **Authentication**: Register, login
- **Users**: Profile, statistics
- **Groups**: CRUD, add members, view balances
- **Expenses**: CRUD, smart split
- **Payments**: Initiate, check status
- **Webhook**: PayHero callbacks

#### Authentication (`auth.py`)
- `SupabaseJWTAuthentication` - Custom JWT authentication
- `get_current_user()` - Helper function

#### Services
- `supabase_service.py` - Supabase Auth integration
- `payhero_service.py` - PayHero payment API

#### Admin (`admin.py`)
Django admin configuration for:
- User management
- Group and member management
- Expense tracking
- Payment monitoring

#### Tests (`tests.py`)
Comprehensive test suite:
- Model tests
- API endpoint tests
- Integration tests
- Workflow tests

---

## 🔄 Data Flow

### User Registration & Login
```
Frontend → Register/Login Endpoint → Supabase Auth Service 
→ Create/Verify User → Return JWT Token
```

### Create Expense
```
Frontend → Create Expense Endpoint → Validate Group/Members 
→ Create Expense Record → Calculate Shares → Update Balances
```

### Initiate Payment
```
Frontend → Initiate Payment Endpoint → Create Payment Record 
→ PayHero STK Push Service → Send to Phone → User Pays
```

### Payment Callback
```
PayHero → Webhook Endpoint → Verify Payment → Update Status 
→ Update Credit Score → Record Transaction
```

---

## 🔑 Key Configuration

### Environment Variables
See `.env.example`:
- Django: `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`
- Supabase: `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET`
- PayHero: `PAYHERO_API_KEY`, `PAYHERO_BASE_URL`
- CORS: `CORS_ALLOWED_ORIGINS`

### Installed Apps (`settings.py`)
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api',
]
```

### Authentication
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api.auth.SupabaseJWTAuthentication',
    ],
}
```

---

## 📡 API Endpoints

### Base URL: `/api/`

#### Authentication
```
POST   /auth/register/     - Register new user
POST   /auth/login/        - Login user
```

#### Users
```
GET    /users/me/          - Get current user profile
GET/PUT /users/profile/    - Get/update profile
```

#### Groups
```
GET    /groups/            - List user's groups
POST   /groups/            - Create group
GET    /groups/{id}/       - Get group details
POST   /groups/{id}/add_member/  - Add member
GET    /groups/{id}/balances/    - View balances
```

#### Expenses
```
GET    /expenses/          - List expenses
POST   /expenses/          - Create expense
GET    /expenses/{id}/     - Get expense details
POST   /expenses/{id}/settle/    - Mark as settled
```

#### Payments
```
GET    /payments/          - List payments
POST   /payments/initiate/ - Start STK push
GET    /payments/{id}/status/    - Check status
```

#### Other
```
POST   /ai/smart-split/    - Generate split suggestions
POST   /payhero/webhook/   - Payment webhook
```

---

## 🗄️ Database Schema

### Users Table
```sql
id (PK, String)
name (String)
email (Email, Unique)
phone_number (String, Unique)
credit_score (Integer, 0-1000)
total_payments (Decimal)
on_time_payments (Integer)
total_late_payments (Integer)
created_at (DateTime)
updated_at (DateTime)
```

### Groups Table
```sql
id (PK, Auto)
title (String)
description (Text)
created_by (FK → User)
created_at (DateTime)
updated_at (DateTime)
```

### Expenses Table
```sql
id (PK, Auto)
group_id (FK → Group)
title (String)
description (Text)
total_amount (Decimal)
paid_by (FK → User)
split_type (Choice: equal/custom/itemized)
settled (Boolean)
date_created (DateTime)
updated_at (DateTime)
```

### Payments Table
```sql
id (PK, Auto)
expense_participant_id (FK)
expense_id (FK)
payer_id (FK → User)
payee_id (FK → User)
amount (Decimal)
status (Choice: pending/initiated/success/failed)
transaction_id (String)
payhero_transaction_id (String)
created_at (DateTime)
updated_at (DateTime)
completed_at (DateTime)
```

---

## 🔐 Authentication Flow

1. **User registers/logs in** with email & password
2. **Supabase Auth** creates JWT token
3. **Frontend stores** JWT token
4. **Each API request** includes `Authorization: Bearer {token}`
5. **SupabaseJWTAuthentication** verifies token
6. **User object** attached to request

---

## 🧪 Testing

### Run Tests
```bash
python manage.py test api              # All tests
python manage.py test api.tests.UserModelTests  # Specific class
python manage.py test api -v 2         # Verbose output
```

### Test Coverage
```bash
coverage run --source='api' manage.py test api
coverage report
coverage html  # Generate HTML report
```

---

## 🚀 Deployment Considerations

### Before Production
- [ ] Set `DEBUG = False`
- [ ] Use strong `SECRET_KEY`
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Configure `SECURE_SSL_REDIRECT = True`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up error logging/monitoring
- [ ] Configure CORS for frontend domain
- [ ] Test PayHero webhook integration

### Production Checklist
- [ ] Environment variables set correctly
- [ ] Database backed up
- [ ] Static files collected
- [ ] Migrations run successfully
- [ ] Admin interface accessible
- [ ] API endpoints responding
- [ ] Health check endpoint working
- [ ] Logs being recorded

---

## 📚 Dependencies

Key packages:
- **Django** - Web framework
- **djangorestframework** - REST API
- **supabase-py** - Supabase client
- **requests** - HTTP client (PayHero)
- **python-dotenv** - Environment variables
- **django-cors-headers** - CORS support

See `requirements.txt` for complete list.

---

## 🛠️ Development Commands

```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Shell for testing
python manage.py shell

# Run tests
python manage.py test api

# Collect static files
python manage.py collectstatic

# Check project
python manage.py check
```

---

## 📞 Support

For help:
1. Check README.md for overview
2. Check SETUP.md for setup instructions
3. Review PROJECT_STRUCTURE.md (this file)
4. Check code comments and docstrings
5. Review test files for usage examples

---

**Last Updated:** October 18, 2025
**Version:** 1.0.0
