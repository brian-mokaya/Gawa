# ⚡ Gawa Backend - Quick Start Guide

Get the Gawa backend up and running in 5 minutes!

---

## 🚀 Quick Start (5 Minutes)

### 1. Clone & Setup (2 min)

```bash
git clone https://github.com/your-username/Gawa.git
cd Gawa
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure (1 min)

```bash
cp .env.example .env
```

Edit `.env` and add:
```env
DEBUG=True
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
PAYHERO_API_KEY=your_key
```

### 3. Initialize Database (1 min)

```bash
python manage.py migrate
```

### 4. Run Server (1 min)

```bash
python manage.py runserver
```

Access: `http://localhost:8000/api/`

---

## 📝 API Quick Reference

### Get Bearer Token

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'
```

Store the `access_token` for other requests.

### Use Bearer Token

```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Create Group

```bash
curl -X POST http://localhost:8000/api/groups/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Trip","description":"Beach trip"}'
```

### Create Expense

```bash
curl -X POST http://localhost:8000/api/expenses/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id":1,
    "title":"Dinner",
    "total_amount":2000,
    "split_type":"equal",
    "participant_ids":["user1","user2"]
  }'
```

### Initiate Payment

```bash
curl -X POST http://localhost:8000/api/payments/initiate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"expense_id":1,"participant_id":"user1"}'
```

---

## 🔑 Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register/` | POST | Register user |
| `/api/auth/login/` | POST | Login & get token |
| `/api/users/me/` | GET | Get profile |
| `/api/groups/` | GET/POST | List/create groups |
| `/api/expenses/` | GET/POST | List/create expenses |
| `/api/payments/` | GET/POST | List/initiate payments |
| `/api/ai/smart-split/` | POST | Generate suggestions |

---

## 📦 Project Files

| File | Purpose |
|------|---------|
| `manage.py` | Django CLI |
| `gawa_backend/settings.py` | Configuration |
| `api/models.py` | Database models |
| `api/views.py` | API endpoints |
| `api/tests.py` | Unit tests |
| `requirements.txt` | Dependencies |
| `.env.example` | Environment template |

---

## 🧪 Test Commands

```bash
# Run all tests
python manage.py test api

# Verbose output
python manage.py test api -v 2

# Specific test class
python manage.py test api.tests.UserModelTests

# With coverage
coverage run --source='api' manage.py test api
coverage report
```

---

## 🛠️ Django Commands

```bash
python manage.py runserver              # Start server
python manage.py migrate                # Apply migrations
python manage.py makemigrations         # Create migrations
python manage.py createsuperuser        # Create admin user
python manage.py shell                  # Interactive shell
python manage.py test                   # Run tests
python manage.py check                  # Check configuration
```

---

## 📚 Documentation

| Document | Content |
|----------|---------|
| README.md | Full documentation |
| SETUP.md | Setup & deployment |
| PROJECT_STRUCTURE.md | Architecture details |
| IMPLEMENTATION_SUMMARY.md | Complete overview |
| QUICK_START.md | This file |

---

## 🆘 Common Issues

### Port Already in Use
```bash
python manage.py runserver 8001  # Use different port
```

### Database Error
```bash
rm db.sqlite3                     # Delete old database
python manage.py migrate          # Recreate
```

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Environment Variables Missing
```bash
cp .env.example .env              # Copy template
# Edit .env with your credentials
```

---

## 💡 Tips

- Use `python manage.py shell` to test code interactively
- Check Django admin at `localhost:8000/admin`
- Use Postman for easier API testing
- Read code comments for implementation details
- Check test file for usage examples

---

## 🔗 Important URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/` | Django home |
| `http://localhost:8000/admin/` | Admin panel |
| `http://localhost:8000/api/` | API root |
| `http://localhost:8000/api/auth/` | Auth endpoints |

---

## ✨ Next Steps

1. Configure `.env` with your credentials
2. Run `python manage.py migrate`
3. Start server: `python manage.py runserver`
4. Test endpoints with curl or Postman
5. Check logs for errors
6. Read full documentation in README.md

---

**Ready to build? Let's go! 🚀**
