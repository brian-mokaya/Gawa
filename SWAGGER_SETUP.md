# ⚡ Swagger Setup - Quick Reference

Swagger/OpenAPI documentation has been added to your Gawa backend!

---

## 🚀 What Was Added

✅ **drf-spectacular** - OpenAPI 3.0 schema generator
✅ **Swagger UI** - Interactive API testing interface
✅ **ReDoc** - Beautiful API documentation
✅ **Auto-generated schema** - From your DRF views

---

## 📍 Access Points

### Swagger UI (Interactive Testing) 🎨
```
http://localhost:8000/api/docs/
```
**Use this to test your APIs directly from the browser!**

### ReDoc (Beautiful Documentation) 📖
```
http://localhost:8000/api/redoc/
```
**Use this to read API documentation.**

### OpenAPI Schema (Raw JSON) 📋
```
http://localhost:8000/api/schema/
```
**Use this for integrations with other tools.**

---

## ⚙️ What's Configured

### In `gawa_backend/settings.py`
- Added `'drf_spectacular'` to INSTALLED_APPS
- Set `'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'` in REST_FRAMEWORK

### In `gawa_backend/urls.py`
- Added Swagger UI endpoint: `/api/docs/`
- Added ReDoc endpoint: `/api/redoc/`
- Added schema endpoint: `/api/schema/`

---

## 🎯 Get Started in 2 Steps

### Step 1: Start Your Server
```bash
python manage.py runserver
```

### Step 2: Open Browser
```
http://localhost:8000/api/docs/
```

**That's it! You now have interactive API documentation! 🎉**

---

## 🧪 Testing Example

1. **Click "Authorize"** (green button)
2. **Login** to get token:
   - Find `POST /api/auth/login/`
   - Click "Try it out"
   - Enter: `{"email":"test@example.com","password":"pass"}`
   - Click Execute
3. **Copy the access_token** from response
4. **Click "Authorize"** button again
5. **Paste:** `Bearer your_token_here`
6. **Click Authorize**
7. **Test any endpoint!** (e.g., POST /api/groups/)

---

## 📚 Documentation Features

| Feature | Location |
|---------|----------|
| Endpoint list | Left sidebar |
| Request examples | Try it out section |
| Response examples | Response section |
| Field descriptions | Expand parameters |
| Status codes | Response codes |
| Authorization | Green Authorize button |

---

## 🔑 Key Endpoints

### Authentication
```
POST /api/auth/register/    - Create account
POST /api/auth/login/       - Get access token
```

### Groups
```
GET  /api/groups/           - List groups
POST /api/groups/           - Create group
GET  /api/groups/{id}/      - Get group details
```

### Expenses
```
GET  /api/expenses/         - List expenses
POST /api/expenses/         - Create expense
```

### Payments
```
GET  /api/payments/         - List payments
POST /api/payments/initiate/ - Start payment
```

---

## 💡 Pro Tips

✅ **Authorization sticky** - Set once, applies to all requests
✅ **Copy as cURL** - Right-click to get shell command
✅ **Try different data** - See validation in action
✅ **Check examples** - Hover over fields for hints
✅ **Use ReDoc** - Better for reading documentation

---

## 🎓 Learn More

📖 See **SWAGGER_GUIDE.md** for:
- Detailed authentication flow
- Complete workflow examples
- Error troubleshooting
- Advanced features
- Security notes

---

## ✨ That's All!

Your APIs are now fully documented and testable!

**Visit: http://localhost:8000/api/docs/**

---

**Enjoy your interactive API documentation! 🚀**
